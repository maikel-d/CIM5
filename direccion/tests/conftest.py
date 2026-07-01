"""
Fixtures compartidas para todos los tests."""
import pytest
from django.test import Client
from django.contrib.auth.models import User
import tempfile
from django.conf import settings


@pytest.fixture(autouse=True)
def use_temp_media():
    tmpdir = tempfile.mkdtemp()
    original_media = settings.MEDIA_ROOT
    settings.MEDIA_ROOT = tmpdir
    yield
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    settings.MEDIA_ROOT = original_media


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def admin_user(db):
    from direccion.models import UserProfile
    user = User.objects.create_superuser(
        username='admin_test', email='admin@test.com', password='testpass123'
    )
    UserProfile.objects.create(user=user, rol='ADMINISTRADOR')
    return user


@pytest.fixture
def admin_client(db, admin_user, client):
    client.force_login(admin_user)
    return client


@pytest.fixture
def basic_user(db):
    from direccion.models import UserProfile
    user = User.objects.create_user(
        username='basic_test', email='basic@test.com', password='testpass123'
    )
    UserProfile.objects.create(user=user, rol='ADMINISTRATIVO')
    return user


@pytest.fixture
def basic_client(db, basic_user, client):
    client.force_login(basic_user)
    return client


@pytest.fixture
def sample_personal(db):
    from direccion.models import Personal
    return Personal.objects.create(
        nombres='Juan', apellidos='Perez', cedula='V-12345678',
        telefonos='04121234567', correo='juan@test.com',
        direccion='Direccion test',
    )


@pytest.fixture
def sample_caso(db):
    from direccion.models import Caso
    return Caso.objects.create(
        nombre='Caso de prueba', descripcion='Caso de prueba',
    )
