"""Tests CRUD para las entidades principales."""
import pytest


class TestPersonalCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client):
        self.client = admin_client
        self.list_url = '/personal/'
        self.create_url = '/personal/crear/'

    def test_list_personal(self):
        r = self.client.get(self.list_url)
        assert r.status_code in [200, 302]

    def test_create_personal(self):
        r = self.client.post(self.create_url, {
            'nombres': 'Test', 'apellidos': 'User',
            'cedula': 'V-99999999', 'telefonos': '04120000000',
            'correo': 'test@test.com', 'direccion': 'Calle Falsa 123',
        })
        assert r.status_code in [200, 302]
        if r.status_code == 302:
            from direccion.models import Personal
            assert Personal.objects.filter(cedula='V-99999999').exists()

    def test_detail_personal(self, sample_personal):
        r = self.client.get(f'/personal/{sample_personal.pk}/')
        assert r.status_code in [200, 302]

    def test_edit_personal(self, sample_personal):
        r = self.client.post(f'/personal/{sample_personal.pk}/editar/', {
            'nombres': 'Editado', 'apellidos': sample_personal.apellidos,
            'cedula': sample_personal.cedula,
            'telefonos': sample_personal.telefonos,
            'correo': sample_personal.correo,
            'direccion': sample_personal.direccion,
        })
        assert r.status_code in [200, 302]


class TestCasosCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client):
        self.client = admin_client

    def test_list_casos(self):
        r = self.client.get('/casos/')
        assert r.status_code in [200, 302]

    def test_create_caso(self):
        r = self.client.post('/casos/crear/', {
            'nombre': 'Caso de test',
            'descripcion': 'Descripcion de prueba',
        })
        assert r.status_code in [200, 302]


class TestTickets:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client):
        self.client = admin_client

    def test_list_tickets(self):
        r = self.client.get('/tickets/')
        assert r.status_code in [200, 302]

    def test_create_ticket(self):
        r = self.client.post('/tickets/crear/', {
            'asunto': 'Ticket test',
            'descripcion': 'Descripcion del ticket',
            'prioridad': 'MEDIO',
        })
        assert r.status_code in [200, 302]
