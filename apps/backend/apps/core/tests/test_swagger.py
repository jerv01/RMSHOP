import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_swagger_schema_accessible():
    response = APIClient().get("/api/v1/schema/")
    assert response.status_code == 200
    assert "openapi" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_swagger_ui_accessible():
    response = APIClient().get("/api/v1/docs/")
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    assert "swagger-ui" in response.content.decode("utf-8")
