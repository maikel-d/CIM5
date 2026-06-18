"""Tests de URLs y decorators."""
import pytest


class TestURLs:
    """Verificar que las URLs importantes existen y responden."""

    def test_login_url(self):
        from django.urls import resolve, reverse
        match = resolve('/login/')
        assert match.url_name is not None

    def test_logout_url(self):
        from django.urls import resolve
        match = resolve('/logout/')
        assert match.url_name is not None

    def test_dashboard_url(self):
        from django.urls import resolve
        match = resolve('/')
        assert match.url_name is not None

    def test_personal_urls_resolve(self):
        from django.urls import resolve
        for url in ['/personal/', '/personal/crear/']:
            match = resolve(url)
            assert match.func is not None, f'No resuelve: {url}'

    def test_casos_urls_resolve(self):
        from django.urls import resolve
        for url in ['/casos/', '/casos/crear/']:
            match = resolve(url)
            assert match.func is not None

    def test_bienes_urls_resolve(self):
        from django.urls import resolve
        for url in ['/bienes/', '/bienes/crear/']:
            match = resolve(url)
            assert match.func is not None

    def test_tickets_url(self):
        from django.urls import resolve
        match = resolve('/tickets/')
        assert match.func is not None

    def test_health_url(self):
        from django.urls import resolve
        match = resolve('/health/')
        assert match.func is not None
