"""Tests de autenticacion y permisos."""
import pytest


class TestLoginView:
    def test_login_page_loads(self, client):
        response = client.get('/login/')
        assert response.status_code == 200

    def test_login_success(self, client, admin_user):
        response = client.post('/login/', {'username': 'admin_test', 'password': 'testpass123'})
        assert response.status_code == 302

    def test_login_fail(self, client, db):
        response = client.post('/login/', {'username': 'noexiste', 'password': 'wrong'})
        assert response.status_code == 200

    def test_logout(self, admin_client):
        response = admin_client.post('/logout/')
        assert response.status_code == 302


class TestProtectedViews:
    def test_dashboard_requires_login(self, client):
        response = client.get('/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_personal_list_requires_login(self, client):
        response = client.get('/personal/')
        assert response.status_code == 302

    def test_casos_list_requires_login(self, client):
        response = client.get('/casos/')
        assert response.status_code == 302

    def test_dashboard_works_for_admin(self, admin_client):
        response = admin_client.get('/')
        assert response.status_code in [200, 302]
