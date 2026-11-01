from unittest.mock import patch

import pytest
from django.db import OperationalError
from rest_framework.test import APIClient

URL = "/api/v1/health"


@pytest.mark.django_db
def test_health_ok():
    response = APIClient().get(URL)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_database_down():
    with patch("apps.core.services.connection") as connection:
        connection.cursor.side_effect = OperationalError("sin conexión")
        response = APIClient().get(URL)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "error"
    assert body["code"] == "service_unavailable"
    assert body["fields"] == {}
