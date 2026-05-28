"""Cliente HTTP base para llamadas inter-servicio.

Incluye:
- Retry con backoff exponencial (3 intentos) usando tenacity
- Circuit Breaker funcional con estados CLOSED → OPEN → HALF_OPEN
- Manejo estructurado de ApiResponse<T>
"""

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
    """Se lanza cuando el breaker está abierto y no permite la llamada."""


class CircuitBreaker:
    """Circuit breaker con tres estados: CLOSED, OPEN, HALF_OPEN.

    - **CLOSED**: las llamadas pasan al servicio. Se cuentan fallos consecutivos.
    - **OPEN**: tras `failure_threshold` fallos, todas las llamadas fallan
      inmediatamente con `CircuitBreakerOpen`. Tras `reset_timeout` segundos,
      transición a HALF_OPEN.
    - **HALF_OPEN**: una llamada de prueba. Si éxito → CLOSED y se resetea
      el contador. Si falla → OPEN nuevamente.

    Demo: si matas un container, los breakers de sus clientes se abren tras
    `failure_threshold` requests, fallan rápido los siguientes, y prueban
    recuperación cada `reset_timeout` segundos.
    """

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
                    f"Circuit {self.name} OPEN — service unavailable"
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
    """Cliente HTTP base para llamadas inter-servicio.

    Cada subclase configura `base_url` y `service_name`. Aporta retry, CB y
    parsing de ApiResponse<T>.
    """

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

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.2, max=2),
            retry=retry_if_exception_type(
                (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError)
            ),
            reraise=True,
        )
        def do_request():
            with httpx.Client(timeout=self.timeout) as client:
                return client.request(
                    method, url, headers=headers, json=json, params=params
                )

        # Envolver todas las posibles fallas (red + CB) en ApiResponse-shaped dict
        try:
            response = self.breaker.call(do_request)
        except CircuitBreakerOpen:
            return {
                "statusCode": 503,
                "data": None,
                "error": {
                    "code": "CIRCUIT_OPEN",
                    "message": f"Service {self.service_name} unavailable (circuit open)",
                },
            }
        except httpx.ConnectError:
            return {
                "statusCode": 503,
                "data": None,
                "error": {
                    "code": "CONNECTION_REFUSED",
                    "message": f"Cannot reach {self.service_name}",
                },
            }
        except httpx.TimeoutException:
            return {
                "statusCode": 504,
                "data": None,
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Timeout calling {self.service_name}",
                },
            }
        except Exception as e:
            return {
                "statusCode": 502,
                "data": None,
                "error": {
                    "code": "BAD_GATEWAY",
                    "message": f"Error calling {self.service_name}: {e}",
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
                    "message": f"No-JSON response from {self.service_name}",
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
