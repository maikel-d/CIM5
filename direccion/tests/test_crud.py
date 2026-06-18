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
            'cedula': 'V-99999999', 'telefono': '04120000000',
            'email': 'test@test.com', 'direccion': 'Calle Falsa 123',
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
            'cedula': sample_personal.cedula, 'telefono': sample_personal.telefono,
            'email': sample_personal.email, 'direccion': sample_personal.direccion,
        })
        assert r.status_code in [200, 302]


class TestCasosCRUD:
    @pytest.fixture(autouse=True)
    def setup(self, db, admin_client, sample_personal):
        self.client = admin_client
        self.personal = sample_personal

    def test_list_casos(self):
        r = self.client.get('/casos/')
        assert r.status_code in [200, 302]

    def test_create_caso(self):
        r = self.client.post('/casos/crear/', {
            'numero_expediente': 'EXP-TEST-001',
            'descripcion': 'Caso de test',
            'personal_asignado': self.personal.pk,
            'estatus': 'ABIERTO',
            'prioridad': 'MEDIA',
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
            'prioridad': 'BAJA',
        })
        assert r.status_code in [200, 302]
