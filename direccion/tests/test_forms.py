"""Tests de formularios del sistema."""
import pytest


class TestUserCreateForm:
    def test_form_fields_exist(self):
        from direccion.forms import UserCreateForm
        form = UserCreateForm()
        for f in ['username', 'first_name', 'last_name', 'password1', 'password2', 'rol']:
            assert f in form.fields, f'Campo {f} no encontrado'

    def test_form_valid_data(self, db):
        from direccion.forms import UserCreateForm
        data = {'username': 'nuevo', 'first_name': 'Test', 'last_name': 'User',
                'password1': 'Pass123!', 'password2': 'Pass123!',
                'rol': 'ANALISTA'}
        form = UserCreateForm(data=data)
        assert form.is_valid(), form.errors.as_text()

    def test_password_mismatch(self, db):
        from direccion.forms import UserCreateForm
        form = UserCreateForm(data={'username': 'otro', 'first_name': 'Test', 'last_name': 'User',
                                     'password1': 'Pass123!', 'password2': 'Diff456!',
                                     'rol': 'ANALISTA'})
        assert not form.is_valid()


class TestPersonalForm:
    def test_valid_personal(self, db):
        from direccion.forms import PersonalForm
        data = {'nombres': 'Maria', 'apellidos': 'Gomez', 'cedula': 'V-87654321',
                'correo': 'maria@test.com', 'telefonos': '04129876543',
                'direccion': 'Calle test 123'}
        form = PersonalForm(data=data)
        assert form.is_valid(), form.errors.as_text()

    def test_invalid_email(self, db):
        from direccion.forms import PersonalForm
        form = PersonalForm(data={'nombres': 'Maria', 'apellidos': 'Gomez',
                                   'cedula': 'V-87654321', 'correo': 'invalido',
                                   'telefonos': '04129876543'})
        assert not form.is_valid()


class TestTicketSoporteForm:
    def test_valid_ticket(self, db):
        from direccion.forms import TicketSoporteForm
        form = TicketSoporteForm(data={'asunto': 'Problema', 'descripcion': 'Test',
                                        'prioridad': 'MEDIO'})
        assert form.is_valid(), form.errors.as_text()
