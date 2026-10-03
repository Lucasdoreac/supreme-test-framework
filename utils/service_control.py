"""Stop and start a service of the local Compose stack from inside a scenario.

Used only by the resilience scenarios (API or Auth down for a moment) and only when the run opts in
with E2E_ALLOW_SERVICE_CONTROL=1 and mounts the Docker socket. It talks to the Docker Engine API and
can touch nothing but the allowlisted services of the one Compose project named in E2E_COMPOSE_PROJECT,
so a wrong variable cannot stop another project's container.
"""
import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.request

ALLOWED_SERVICES = frozenset({"api", "auth"})
SOCKET_PATH = "/var/run/docker.sock"


class ServiceControlUnavailable(RuntimeError):
    """The run did not opt in to stopping services (or has no Docker socket)."""


class _UnixConnection(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("docker")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(60)
        self.sock.connect(SOCKET_PATH)


def _engine(method, path, body=None):
    connection = _UnixConnection()
    try:
        connection.request(method, path, body=json.dumps(body) if body is not None else None,
                           headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        payload = response.read()
        return response.status, (json.loads(payload) if payload and payload[:1] in b"[{" else payload)
    finally:
        connection.close()


def _container_id(service):
    if os.getenv("E2E_ALLOW_SERVICE_CONTROL") != "1" or not os.path.exists(SOCKET_PATH):
        raise ServiceControlUnavailable("set E2E_ALLOW_SERVICE_CONTROL=1 and mount the Docker socket")
    if service not in ALLOWED_SERVICES:
        raise ValueError(f"service '{service}' is not allowed (only {sorted(ALLOWED_SERVICES)})")
    project = os.getenv("E2E_COMPOSE_PROJECT", "")
    if not project:
        raise ServiceControlUnavailable("E2E_COMPOSE_PROJECT is not set")
    filters = json.dumps({"label": [f"com.docker.compose.project={project}",
                                    f"com.docker.compose.service={service}"]})
    status, found = _engine("GET", f"/containers/json?all=1&filters={urllib.request.quote(filters)}")
    if status != 200 or len(found) != 1:
        raise ServiceControlUnavailable(f"expected exactly one '{service}' container in '{project}'")
    return found[0]["Id"]


def stop(service):
    status, _ = _engine("POST", f"/containers/{_container_id(service)}/stop?t=3")
    assert status in (204, 304), f"could not stop {service}: HTTP {status}"


def start(service):
    status, _ = _engine("POST", f"/containers/{_container_id(service)}/start")
    assert status in (204, 304), f"could not start {service}: HTTP {status}"


def wait_until_answering(url, timeout=90, body=None):
    """True once the URL answers with a status below 500 (the service, and what it forwards to, is up)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            request = urllib.request.Request(
                url, data=json.dumps(body).encode() if body is not None else None,
                headers={"Content-Type": "application/json"}, method="POST" if body is not None else "GET")
            urllib.request.urlopen(request, timeout=3)
            return True
        except urllib.error.HTTPError as error:
            if error.code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def restart(service, api_url):
    """Start the service and wait until the API answers again. The Auth is probed through the API's logout
    route with a made-up session: 5xx while the Auth is unreachable, a plain 4xx/2xx once it answers."""
    start(service)
    if service == "auth":
        up = wait_until_answering(f"{api_url}/auth/logout", body={"email": "probe@example.invalid", "token": "probe"})
    else:
        up = wait_until_answering(f"{api_url}/")
    assert up, f"{service} did not come back"
