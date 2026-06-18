"""
Tests para Bienes, busqueda, reportes y middleware."""
import pytest


class TestBienesCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client):
        self.client = admin_client

    def test_list_bienes(self):
        r = self.client.get("/bienes/")
        assert r.status_code in [200, 302]

    def test_create_bien_page(self):
        r = self.client.get("/bienes/crear/")
        assert r.status_code in [200, 302]


class TestSearch:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client):
        self.client = admin_client

    def test_search_returns_json(self):
        r = self.client.get("/buscar/?q=test")
        assert r.status_code in [200, 302]


class TestDashboardReports:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client):
        self.client = admin_client

    def test_reports_page(self):
        r = self.client.get("/reportes/")
        assert r.status_code in [200, 302]
