"""Adaptador del Orders API de MercadoPago (Checkout API, Colombia).

Es el único módulo que habla HTTP con MercadoPago; el resto del backend usa sus métodos y
recibe diccionarios con la orden de MercadoPago tal como la documenta la API.
"""

import hashlib
import hmac
import logging

import httpx
from django.conf import settings

from apps.payments.exceptions import (
    PaymentGatewayNotConfigured,
    PaymentGatewayUnavailable,
    PaymentRequestRejected,
)

logger = logging.getLogger(__name__)

# Respuesta de "orden creada pero alguna transacción falló": trae la orden y se procesa como
# rechazo, no como error de comunicación.
_TRANSACTION_FAILED_STATUS = 402


class MercadoPagoGateway:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.access_token = (
            settings.MERCADOPAGO_ACCESS_TOKEN if access_token is None else access_token
        )
        self.base_url = (base_url or settings.MERCADOPAGO_API_BASE_URL).rstrip("/")
        self.timeout = settings.MERCADOPAGO_TIMEOUT_SECONDS if timeout is None else timeout

    def create_order(self, *, payload: dict, idempotency_key: str) -> dict:
        """POST /v1/orders. Devuelve la orden de MercadoPago (también si el pago fue rechazado)."""
        return self._request(
            "POST",
            "/v1/orders",
            json=payload,
            headers={"X-Idempotency-Key": idempotency_key},
            accept_failed_transaction=True,
        )

    def get_order(self, *, mp_order_id: str) -> dict:
        """GET /v1/orders/{id}: estado actual de la orden en MercadoPago."""
        return self._request("GET", f"/v1/orders/{mp_order_id}")

    def list_pse_banks(self) -> list[dict]:
        """Bancos disponibles para PSE, según GET /v1/payment_methods."""
        methods = self._request("GET", "/v1/payment_methods")
        for method in methods if isinstance(methods, list) else []:
            if method.get("id") == "pse":
                institutions = method.get("financial_institutions") or []
                if isinstance(institutions, dict):
                    institutions = [institutions]
                return [
                    {"id": str(inst.get("id")), "description": inst.get("description", "")}
                    for inst in institutions
                    if inst.get("id") is not None
                ]
        return []

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        headers: dict | None = None,
        accept_failed_transaction: bool = False,
    ):
        if not self.access_token:
            raise PaymentGatewayNotConfigured()

        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            **(headers or {}),
        }
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                headers=request_headers,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("MercadoPago no respondió (%s %s): %s", method, path, exc)
            raise PaymentGatewayUnavailable() from exc

        if response.status_code == _TRANSACTION_FAILED_STATUS and accept_failed_transaction:
            return _failed_transaction_order(response)

        if response.status_code == 429 or response.status_code >= 500:
            logger.warning("MercadoPago respondió %s en %s %s", response.status_code, method, path)
            raise PaymentGatewayUnavailable()

        if response.status_code >= 400:
            # Se registra solo el código de error de MercadoPago, nunca el cuerpo enviado.
            logger.warning(
                "MercadoPago rechazó %s %s con %s: %s",
                method,
                path,
                response.status_code,
                _error_codes(response),
            )
            raise PaymentRequestRejected(fields={"gateway_errors": _error_codes(response)})

        return response.json()


def _safe_json(response: httpx.Response):
    try:
        return response.json()
    except ValueError:
        return {}


def _error_codes(response: httpx.Response) -> list[str]:
    body = _safe_json(response)
    if not isinstance(body, dict):
        return []
    errors = body.get("errors") or []
    codes = [str(err.get("code")) for err in errors if isinstance(err, dict) and err.get("code")]
    return codes or ([str(body["code"])] if body.get("code") else [])


def _failed_transaction_order(response: httpx.Response) -> dict:
    """Normaliza la respuesta 402: la orden con su transacción fallida, marcada como `failed`."""
    body = _safe_json(response)
    if not isinstance(body, dict):
        body = {}
    order = body.get("data") if isinstance(body.get("data"), dict) else body
    order = dict(order)
    order.setdefault("status", "failed")
    order.setdefault("status_detail", "rejected")
    return order


def verify_webhook_signature(*, signature_header: str, request_id: str, data_id: str) -> bool:
    """Valida el header x-signature de una notificación de MercadoPago (HMAC-SHA256).

    Formato: "ts=<epoch>,v1=<hex>". El manifiesto firmado es
    "id:<data.id>;request-id:<x-request-id>;ts:<ts>;" con data.id en minúsculas.
    """
    secret = settings.MERCADOPAGO_WEBHOOK_SECRET
    if not secret:
        raise PaymentGatewayNotConfigured()
    parts = dict(
        part.strip().split("=", 1) for part in (signature_header or "").split(",") if "=" in part
    )
    ts, received = parts.get("ts"), parts.get("v1")
    if not ts or not received or not data_id:
        return False
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
