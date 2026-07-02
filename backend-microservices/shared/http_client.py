import threading
import time
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class CircuitBreakerOpen(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "CLOSED"
        self.opened_at: Optional[float] = None
        self._lock = threading.Lock()

    def _maybe_half_open(self) -> None:
        if self.state == "OPEN" and self.opened_at is not None:
            if time.time() - self.opened_at >= self.reset_timeout:
                self.state = "HALF_OPEN"

    def call(self, func, *args, **kwargs):
        with self._lock:
            self._maybe_half_open()
            if self.state == "OPEN":
                raise CircuitBreakerOpen(
                    f"Circuito {self.name} abierto — servicio no disponible"
                )

        try:
            result = func(*args, **kwargs)
        except Exception:
            with self._lock:
                self.failures += 1
                if self.state == "HALF_OPEN":
                    self.state = "OPEN"
                    self.opened_at = time.time()
                elif self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    self.opened_at = time.time()
            raise
        else:
            with self._lock:
                self.failures = 0
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.opened_at = None
            return result


class ServiceClient:
    """Las subclases definen base_url y service_name."""

    def __init__(
        self,
        base_url: str,
        service_name: str,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.timeout = timeout
        self.breaker = CircuitBreaker(name=service_name)

    def _request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # un POST con timeout pudo haberse aplicado igual; solo se reintenta lo que no alcanzó a salir
        retry_on = (
            (httpx.TransportError,)
            if method == "GET"
            else (httpx.ConnectError, httpx.ConnectTimeout)
        )

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.2, max=2),
            retry=retry_if_exception_type(retry_on),
            reraise=True,
        )
        def do_request():
            with httpx.Client(timeout=self.timeout) as client:
                return client.request(
                    method, url, headers=headers, json=json, params=params
                )

        # las fallas se devuelven como envelope de error, no como excepción
        try:
            response = self.breaker.call(do_request)
        except CircuitBreakerOpen:
            return {
                "statusCode": 503,
                "data": None,
                "error": {
                    "code": "CIRCUIT_OPEN",
                    "message": f"Servicio {self.service_name} no disponible (circuito abierto)",
                },
            }
        except httpx.ConnectError:
            return {
                "statusCode": 503,
                "data": None,
                "error": {
                    "code": "CONNECTION_REFUSED",
                    "message": f"No se pudo contactar al servicio {self.service_name}",
                },
            }
        except httpx.TimeoutException:
            return {
                "statusCode": 504,
                "data": None,
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Tiempo de espera agotado al llamar a {self.service_name}",
                },
            }
        except Exception as e:
            return {
                "statusCode": 502,
                "data": None,
                "error": {
                    "code": "BAD_GATEWAY",
                    "message": f"Error al llamar a {self.service_name}: {e}",
                },
            }
        try:
            return response.json()
        except Exception:
            return {
                "statusCode": response.status_code,
                "data": None,
                "error": {
                    "code": "BAD_RESPONSE",
                    "message": f"Respuesta no válida del servicio {self.service_name}",
                },
            }

    def get(self, path: str, token: Optional[str] = None,
            params: Optional[dict] = None) -> dict:
        return self._request("GET", path, token=token, params=params)

    def post(self, path: str, token: Optional[str] = None,
             json: Optional[dict] = None) -> dict:
        return self._request("POST", path, token=token, json=json)

    def put(self, path: str, token: Optional[str] = None,
            json: Optional[dict] = None) -> dict:
        return self._request("PUT", path, token=token, json=json)

    def delete(self, path: str, token: Optional[str] = None) -> dict:
        return self._request("DELETE", path, token=token)
