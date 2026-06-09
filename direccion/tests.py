"""
Tests de integridad: verificar que los archivos se borren del disco
al eliminar o actualizar registros que contienen FileField / ImageField.
"""
import os
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.urls import reverse

from .models import (
    Personal, DocumentoPersonal,
    Investigado, DocumentoInvestigado,
    DocumentoDireccion, Caso, UserProfile,
    TicketSoporte, TicketHistorial, Notificacion,
    InformeDiario, AuditLog,
)


# Usamos un MEDIA_ROOT temporal para no contaminar el real
TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PersonalFileCleanupTest(TestCase):
    """Verifica que al eliminar Personal se borren foto y documentos del disco."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "a@a.com", "pass")
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

    def setUp(self):
        self.client.force_login(self.admin)
        # Crear Personal con foto
        self.personal = Personal.objects.create(
            apellidos="Garcia",
            nombres="Luis",
            cedula="V-12345678",
        )
        self.personal.foto.save("test_foto.jpg", ContentFile(b"fake_image_data"))
        self.personal.save()

        # Crear un documento asociado
        self.doc = DocumentoPersonal.objects.create(
            personal=self.personal,
            descripcion="Test doc",
        )
        self.doc.archivo.save("test_doc.pdf", ContentFile(b"fake_pdf_data"))
        self.doc.save()

        # Guardar las rutas reales de los archivos para verificar después
        self.foto_path = Path(self.personal.foto.path)
        self.doc_path = Path(self.doc.archivo.path)
        self.assertTrue(self.foto_path.exists(), "La foto debería existir en setUp")
        self.assertTrue(self.doc_path.exists(), "El documento debería existir en setUp")

    def tearDown(self):
        """Limpieza: borrar archivos temporales que hayan quedado."""
        for p in [self.foto_path, self.doc_path]:
            if p.exists():
                p.unlink()

    def test_personal_delete_removes_foto_from_disk(self):
        """Al eliminar Personal, su foto debe desaparecer del disco."""
        pk = self.personal.pk
        self.client.post(reverse("personal_delete", args=[pk]))
        self.assertFalse(
            self.foto_path.exists(),
            "La foto del personal debería eliminarse del disco al borrar el registro",
        )

    def test_personal_delete_removes_document_from_disk(self):
        """Al eliminar Personal, los documentos asociados deben desaparecer del disco."""
        pk = self.personal.pk
        self.client.post(reverse("personal_delete", args=[pk]))
        self.assertFalse(
            self.doc_path.exists(),
            "El documento del personal debería eliminarse del disco",
        )

    def test_personal_delete_removes_record_from_db(self):
        """Al eliminar Personal, el registro debe desaparecer de la BD."""
        pk = self.personal.pk
        self.client.post(reverse("personal_delete", args=[pk]))
        self.assertFalse(
            Personal.objects.filter(pk=pk).exists(),
            "El registro de Personal debería eliminarse de la BD",
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentoPersonalDeleteTest(TestCase):
    """Verifica que al eliminar un DocumentoPersonal individual se borre del disco."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin2", "a2@a.com", "pass")
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

    def setUp(self):
        self.client.force_login(self.admin)
        self.personal = Personal.objects.create(
            apellidos="Lopez", nombres="Ana", cedula="V-87654321",
        )
        self.doc = DocumentoPersonal.objects.create(
            personal=self.personal, descripcion="Doc test",
        )
        self.doc.archivo.save("test_delete.pdf", ContentFile(b"content"))
        self.doc.save()
        self.doc_path = Path(self.doc.archivo.path)

    def tearDown(self):
        if self.doc_path.exists():
            self.doc_path.unlink()

    def test_delete_individual_documento_personal(self):
        """Eliminar un DocumentoPersonal debe borrar su archivo del disco."""
        self.client.post(
            reverse("personal_documento_delete", args=[self.personal.pk, self.doc.pk])
        )
        self.assertFalse(
            self.doc_path.exists(),
            "El archivo del DocumentoPersonal debería eliminarse del disco",
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class InvestigadoFileCleanupTest(TestCase):
    """Verifica que al eliminar Investigado se borren foto y documentos del disco."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin3", "a3@a.com", "pass")
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

    def setUp(self):
        self.client.force_login(self.admin)
        self.investigado = Investigado.objects.create(
            apellidos="Perez",
            nombres="Juan",
            cedula="V-11223344",
        )
        self.investigado.foto.save("inv_foto.jpg", ContentFile(b"fake_inv_image"))
        self.investigado.save()

        self.doc = DocumentoInvestigado.objects.create(
            investigado=self.investigado, descripcion="Evidencia",
        )
        self.doc.archivo.save("evidencia.pdf", ContentFile(b"fake_evidence"))
        self.doc.save()

        self.foto_path = Path(self.investigado.foto.path)
        self.doc_path = Path(self.doc.archivo.path)

    def tearDown(self):
        for p in [self.foto_path, self.doc_path]:
            if p.exists():
                p.unlink()

    def test_investigado_delete_removes_foto_from_disk(self):
        """Al eliminar Investigado, su foto debe desaparecer del disco."""
        pk = self.investigado.pk
        self.client.post(reverse("investigado_delete", args=[pk]))
        self.assertFalse(
            self.foto_path.exists(),
            "La foto del investigado debería eliminarse del disco",
        )

    def test_investigado_delete_removes_document_from_disk(self):
        """Al eliminar Investigado, los documentos asociados deben desaparecer."""
        pk = self.investigado.pk
        self.client.post(reverse("investigado_delete", args=[pk]))
        self.assertFalse(
            self.doc_path.exists(),
            "El documento del investigado debería eliminarse del disco",
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentoInvestigadoDeleteTest(TestCase):
    """Verifica que al eliminar un DocumentoInvestigado se borre del disco."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin4", "a4@a.com", "pass")
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

    def setUp(self):
        self.client.force_login(self.admin)
        self.inv = Investigado.objects.create(
            apellidos="Ruiz", nombres="Maria", cedula="V-99887766",
        )
        self.doc = DocumentoInvestigado.objects.create(
            investigado=self.inv, descripcion="Doc test",
        )
        self.doc.archivo.save("test_inv_doc.pdf", ContentFile(b"data"))
        self.doc.save()
        self.doc_path = Path(self.doc.archivo.path)

    def tearDown(self):
        if self.doc_path.exists():
            self.doc_path.unlink()

    def test_delete_individual_documento_investigado(self):
        """Eliminar DocumentoInvestigado debe borrar su archivo del disco."""
        self.client.post(
            reverse("investigado_documento_delete", args=[self.inv.pk, self.doc.pk])
        )
        self.assertFalse(
            self.doc_path.exists(),
            "El archivo del DocumentoInvestigado debería eliminarse del disco",
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentoDireccionDeleteTest(TestCase):
    """Verifica que al eliminar DocumentoDireccion se borre del disco."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin5", "a5@a.com", "pass")
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

    def setUp(self):
        self.client.force_login(self.admin)
        self.doc = DocumentoDireccion.objects.create(
            descripcion="Doc direccion test", categoria="LEYES",
        )
        self.doc.archivo.save("direccion.pdf", ContentFile(b"data"))
        self.doc.save()
        self.doc_path = Path(self.doc.archivo.path)

    def tearDown(self):
        if self.doc_path.exists():
            self.doc_path.unlink()

    def test_delete_documento_direccion_removes_file(self):
        """Eliminar DocumentoDireccion debe borrar su archivo del disco."""
        self.client.post(reverse("documento_direccion_delete", args=[self.doc.pk]))
        self.assertFalse(
            self.doc_path.exists(),
            "El archivo de DocumentoDireccion debería eliminarse del disco",
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PersonalFotoReplacementTest(TestCase):
    """Verifica que al reemplazar la foto de Personal se borre la vieja del disco."""

    def setUp(self):
        self.personal = Personal.objects.create(
            apellidos="Castro", nombres="Pedro", cedula="V-55443322",
        )
        # Foto 1
        self.personal.foto.save("foto_vieja.jpg", ContentFile(b"old_image"))
        self.personal.save()
        self.old_foto_path = Path(self.personal.foto.path)

    def tearDown(self):
        # Limpiar cualquier archivo residual
        media = Path(TEST_MEDIA_ROOT)
        if media.exists():
            for f in media.rglob("*"):
                if f.is_file():
                    f.unlink()

    def test_personal_foto_replacement_deletes_old_file(self):
        """Al subir una foto nueva, el archivo anterior debe eliminarse del disco."""
        self.assertTrue(
            self.old_foto_path.exists(),
            "La foto vieja debería existir antes del reemplazo",
        )
        # Reemplazar la foto
        self.personal.foto.save("foto_nueva.jpg", ContentFile(b"new_image"))
        self.personal.save()
        self.assertFalse(
            self.old_foto_path.exists(),
            "La foto vieja debería eliminarse del disco al subir una nueva",
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class InvestigadoFotoReplacementTest(TestCase):
    """Verifica que al reemplazar la foto de Investigado se borre la vieja del disco."""

    def setUp(self):
        self.inv = Investigado.objects.create(
            apellidos="Mendoza", nombres="Sofia", cedula="V-66778899",
        )
        self.inv.foto.save("inv_foto_vieja.jpg", ContentFile(b"old_inv_image"))
        self.inv.save()
        self.old_foto_path = Path(self.inv.foto.path)

    def tearDown(self):
        media = Path(TEST_MEDIA_ROOT)
        if media.exists():
            for f in media.rglob("*"):
                if f.is_file():
                    f.unlink()

    def test_investigado_foto_replacement_deletes_old_file(self):
        """Al subir una foto nueva de investigado, la anterior debe eliminarse."""
        self.assertTrue(
            self.old_foto_path.exists(),
            "La foto vieja del investigado debería existir antes del reemplazo",
        )
        self.inv.foto.save("inv_foto_nueva.jpg", ContentFile(b"new_inv_image"))
        self.inv.save()
        self.assertFalse(
            self.old_foto_path.exists(),
            "La foto vieja debería eliminarse del disco al reemplazarla",
        )


# ============================================================
# TICKET HISTORIAL MODEL TESTS
# ============================================================


class TicketHistorialModelTest(TestCase):
    """Pruebas unitarias para el modelo TicketHistorial y el método registrar_cambio."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("ticketadmin", "ta@a.com", "pass")
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")
        cls.analista = User.objects.create_user("analista1", "analista@a.com", "pass")
        UserProfile.objects.create(user=cls.analista, rol="ANALISTA")

    def setUp(self):
        self.ticket = TicketSoporte.objects.create(
            asunto="Test ticket",
            descripcion="Descripcion de prueba",
            prioridad="MEDIO",
            creado_por=self.analista,
        )

    def test_registrar_cambio_creates_record(self):
        """registrar_cambio() debe crear un registro en TicketHistorial."""
        self.ticket.registrar_cambio(self.admin, "estado", "ABIERTO", "EN_PROCESO")
        self.assertEqual(TicketHistorial.objects.count(), 1)
        h = TicketHistorial.objects.first()
        self.assertEqual(h.ticket, self.ticket)
        self.assertEqual(h.usuario, self.admin)
        self.assertEqual(h.campo, "estado")
        self.assertEqual(h.valor_anterior, "Abierto")
        self.assertEqual(h.valor_nuevo, "En proceso")

    def test_registrar_cambio_skips_equal_values(self):
        """registrar_cambio() NO debe crear registro si los valores son iguales."""
        self.ticket.registrar_cambio(self.admin, "estado", "ABIERTO", "ABIERTO")
        self.assertEqual(TicketHistorial.objects.count(), 0)

    def test_registrar_cambio_skips_equal_prioridad(self):
        """registrar_cambio() NO debe crear registro si prioridad no cambia."""
        self.ticket.registrar_cambio(self.admin, "prioridad", "MEDIO", "MEDIO")
        self.assertEqual(TicketHistorial.objects.count(), 0)

    def test_registrar_cambio_creates_multiple_records(self):
        """registrar_cambio() debe permitir múltiples cambios en distintos campos."""
        self.ticket.registrar_cambio(self.admin, "estado", "ABIERTO", "EN_PROCESO")
        self.ticket.registrar_cambio(self.admin, "prioridad", "MEDIO", "ALTO")
        self.ticket.registrar_cambio(self.admin, "asignado_a", "---", self.admin.get_full_name() or self.admin.username)
        self.assertEqual(TicketHistorial.objects.count(), 3)

    def test_registrar_cambio_without_user(self):
        """registrar_cambio() debe permitir usuario None (usuario eliminado)."""
        self.ticket.registrar_cambio(None, "estado", "ABIERTO", "RESUELTO")
        self.assertEqual(TicketHistorial.objects.count(), 1)
        h = TicketHistorial.objects.first()
        self.assertIsNone(h.usuario)

    def test_formatear_valor_estado(self):
        """_formatear_valor() debe convertir código de estado a su etiqueta."""
        resultado = self.ticket._formatear_valor("estado", "ABIERTO")
        self.assertEqual(resultado, "Abierto")
        resultado = self.ticket._formatear_valor("estado", "EN_PROCESO")
        self.assertEqual(resultado, "En proceso")
        resultado = self.ticket._formatear_valor("estado", "RESUELTO")
        self.assertEqual(resultado, "Resuelto")
        resultado = self.ticket._formatear_valor("estado", "CERRADO")
        self.assertEqual(resultado, "Cerrado")

    def test_formatear_valor_prioridad(self):
        """_formatear_valor() debe convertir código de prioridad a su etiqueta."""
        resultado = self.ticket._formatear_valor("prioridad", "BAJO")
        self.assertEqual(resultado, "Bajo")
        resultado = self.ticket._formatear_valor("prioridad", "MEDIO")
        self.assertEqual(resultado, "Medio")
        resultado = self.ticket._formatear_valor("prioridad", "ALTO")
        self.assertEqual(resultado, "Alto")

    def test_formatear_valor_asignado_a_user(self):
        """_formatear_valor() debe convertir User a su nombre completo."""
        resultado = self.ticket._formatear_valor("asignado_a", self.admin)
        expected = self.admin.get_full_name() or self.admin.username
        self.assertEqual(resultado, expected)

    def test_formatear_valor_asignado_a_string(self):
        """_formatear_valor() debe pasar strings sin modificar para asignado_a."""
        resultado = self.ticket._formatear_valor("asignado_a", "Juan Perez")
        self.assertEqual(resultado, "Juan Perez")

    def test_formatear_valor_none(self):
        """_formatear_valor() debe devolver '---' para valores None."""
        resultado = self.ticket._formatear_valor("estado", None)
        self.assertEqual(resultado, "---")
        resultado = self.ticket._formatear_valor("prioridad", None)
        self.assertEqual(resultado, "---")
        resultado = self.ticket._formatear_valor("asignado_a", None)
        self.assertEqual(resultado, "---")

    def test_ticket_historial_str(self):
        """__str__ de TicketHistorial debe mostrar el cambio."""
        self.ticket.registrar_cambio(self.admin, "estado", "ABIERTO", "EN_PROCESO")
        h = TicketHistorial.objects.first()
        expected = f"#{self.ticket.pk} - Estado: Abierto -> En proceso"
        self.assertEqual(str(h), expected)

    def test_registrar_cambio_on_create(self):
        """Simula el flujo real: crear ticket y registrar cambio inicial."""
        ticket = TicketSoporte.objects.create(
            asunto="Nuevo ticket",
            descripcion="Desc",
            prioridad="ALTO",
            creado_por=self.analista,
        )
        ticket.registrar_cambio(self.analista, "estado", "---", "ABIERTO")
        ticket.registrar_cambio(self.analista, "prioridad", "---", "ALTO")
        self.assertEqual(TicketHistorial.objects.count(), 2)
        cambios = TicketHistorial.objects.filter(ticket=ticket).order_by("fecha")
        self.assertEqual(cambios[0].valor_anterior, "---")
        self.assertEqual(cambios[0].valor_nuevo, "Abierto")
        self.assertEqual(cambios[1].valor_anterior, "---")
        self.assertEqual(cambios[1].valor_nuevo, "Alto")


# ============================================================
# TICKET VIEWS TESTS
# ============================================================


class TicketViewsTest(TestCase):
    """Pruebas de vistas del módulo de Tickets de Soporte."""

    @classmethod
    def setUpTestData(cls):
        # Crear usuarios con diferentes roles
        cls.admin = User.objects.create_user(
            "admin_tickets", "admin_t@a.com", "pass",
            first_name="Admin", last_name="Ticket"
        )
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

        cls.analista = User.objects.create_user(
            "analista_tickets", "analista_t@a.com", "pass",
            first_name="Analista", last_name="Ticket"
        )
        UserProfile.objects.create(user=cls.analista, rol="ANALISTA")

        cls.administrativo = User.objects.create_user(
            "adminis_tickets", "adminis_t@a.com", "pass",
            first_name="Adminis", last_name="Ticket"
        )
        UserProfile.objects.create(user=cls.administrativo, rol="ADMINISTRATIVO")

        # Crear tickets de prueba
        cls.ticket_admin = TicketSoporte.objects.create(
            asunto="Ticket del admin",
            descripcion="Desc admin",
            prioridad="ALTO",
            creado_por=cls.admin,
        )
        cls.ticket_analista = TicketSoporte.objects.create(
            asunto="Ticket del analista",
            descripcion="Desc analista",
            prioridad="MEDIO",
            creado_por=cls.analista,
        )

    # -----------------------------------------------------------
    # ticket_list
    # -----------------------------------------------------------

    def test_ticket_list_admin_sees_all(self):
        """Admin debe ver todos los tickets."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket del admin")
        self.assertContains(response, "Ticket del analista")
        self.assertTemplateUsed(response, "direccion/ticket_list.html")

    def test_ticket_list_analista_sees_own(self):
        """Analista debe ver solo sus propios tickets."""
        self.client.force_login(self.analista)
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ticket del admin")
        self.assertContains(response, "Ticket del analista")

    def test_ticket_list_administrativo_sees_own(self):
        """Administrativo debe ver solo sus propios tickets."""
        self.client.force_login(self.administrativo)
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ticket del admin")
        self.assertNotContains(response, "Ticket del analista")

    def test_ticket_list_unauthenticated_redirects(self):
        """Usuario no autenticado debe ser redirigido al login."""
        response = self.client.get(reverse("ticket_list"))
        self.assertRedirects(response, reverse("login"))

    def test_ticket_list_filter_by_estado(self):
        """Admin puede filtrar tickets por estado."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("ticket_list") + "?estado=ABIERTO")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket del admin")

    def test_ticket_list_filter_by_usuario(self):
        """Admin puede filtrar tickets por usuario creador."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("ticket_list") + f"?usuario={self.analista.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ticket del admin")
        self.assertContains(response, "Ticket del analista")

    # -----------------------------------------------------------
    # ticket_detail
    # -----------------------------------------------------------

    def test_ticket_detail_admin(self):
        """Admin debe poder ver detalle de cualquier ticket."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("ticket_detail", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket del analista")
        self.assertTemplateUsed(response, "direccion/ticket_detail.html")

    def test_ticket_detail_analista(self):
        """Analista debe poder ver detalle de su propio ticket."""
        self.client.force_login(self.analista)
        response = self.client.get(
            reverse("ticket_detail", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket del analista")

    def test_ticket_detail_shows_history(self):
        """El detalle debe mostrar el historial de cambios del ticket."""
        self.ticket_analista.registrar_cambio(
            self.admin, "estado", "ABIERTO", "EN_PROCESO"
        )
        self.client.force_login(self.analista)
        response = self.client.get(
            reverse("ticket_detail", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "En proceso")

    def test_ticket_detail_unauthenticated_redirects(self):
        """Usuario no autenticado debe ser redirigido al login."""
        response = self.client.get(
            reverse("ticket_detail", args=[self.ticket_analista.pk])
        )
        self.assertRedirects(response, reverse("login"))

    def test_ticket_detail_404(self):
        """Detalle de ticket inexistente debe devolver 404."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("ticket_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------------------
    # ticket_create
    # -----------------------------------------------------------

    def test_ticket_create_get_analista(self):
        """GET: analista debe ver el formulario de creación."""
        self.client.force_login(self.analista)
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "direccion/ticket_form.html")
        self.assertContains(response, "Crear")

    def test_ticket_create_get_administrativo(self):
        """GET: administrativo debe ver el formulario de creación."""
        self.client.force_login(self.administrativo)
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 200)

    def test_ticket_create_post_creates_ticket_and_history(self):
        """POST: crear ticket debe redirigir a detail y registrar historial."""
        self.client.force_login(self.analista)
        response = self.client.post(reverse("ticket_create"), {
            "asunto": "Nuevo ticket de prueba",
            "descripcion": "Descripción del ticket de prueba",
            "prioridad": "ALTO",
        })
        # Debe redirigir a ticket_detail
        self.assertEqual(response.status_code, 302)
        ticket = TicketSoporte.objects.get(asunto="Nuevo ticket de prueba")
        self.assertRedirects(response, reverse("ticket_detail", args=[ticket.pk]))
        # Verificar que se creó con los datos correctos
        self.assertEqual(ticket.creado_por, self.analista)
        self.assertEqual(ticket.prioridad, "ALTO")
        self.assertEqual(ticket.estado, "ABIERTO")
        # Verificar que se registró el historial (2 registros: estado + prioridad)
        self.assertEqual(ticket.historial.count(), 2)
        cambios = ticket.historial.order_by("fecha")
        self.assertEqual(cambios[0].campo, "estado")
        self.assertEqual(cambios[0].valor_nuevo, "Abierto")
        self.assertEqual(cambios[1].campo, "prioridad")
        self.assertEqual(cambios[1].valor_nuevo, "Alto")

    def test_ticket_create_admin_can_create(self):
        """Admin ahora puede crear tickets (tiene TICKETS_CREAR)."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "direccion/ticket_form.html")

    def test_ticket_create_post_invalid_form(self):
        """POST con datos inválidos debe mostrar el formulario nuevamente."""
        self.client.force_login(self.analista)
        response = self.client.post(reverse("ticket_create"), {
            "asunto": "",  # asunto es requerido
        })
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertTemplateUsed(response, "direccion/ticket_form.html")

    def test_ticket_create_unauthenticated_redirects(self):
        """Usuario no autenticado debe ser redirigido al login."""
        response = self.client.get(reverse("ticket_create"))
        self.assertRedirects(response, reverse("login"))

    # -----------------------------------------------------------
    # ticket_resolver
    # -----------------------------------------------------------

    def test_ticket_resolver_admin_resolves(self):
        """Admin puede marcar un ticket como resuelto."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("ticket_resolver", args=[self.ticket_analista.pk])
        )
        self.assertRedirects(response, reverse("ticket_list"))
        self.ticket_analista.refresh_from_db()
        self.assertEqual(self.ticket_analista.estado, "RESUELTO")

    def test_ticket_resolver_admin_reopens(self):
        """Admin puede reabrir un ticket resuelto."""
        self.ticket_analista.estado = "RESUELTO"
        self.ticket_analista.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("ticket_resolver", args=[self.ticket_analista.pk])
        )
        self.assertRedirects(response, reverse("ticket_list"))
        self.ticket_analista.refresh_from_db()
        self.assertEqual(self.ticket_analista.estado, "ABIERTO")

    def test_ticket_resolver_creates_history(self):
        """Resolver debe registrar el cambio en el historial."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse("ticket_resolver", args=[self.ticket_analista.pk])
        )
        historial = self.ticket_analista.historial.filter(campo="estado")
        self.assertEqual(historial.count(), 1)
        self.assertEqual(historial.first().valor_anterior, "Abierto")
        self.assertEqual(historial.first().valor_nuevo, "Resuelto")

    def test_ticket_resolver_analista_forbidden(self):
        """Analista NO debe poder resolver tickets (solo admin)."""
        self.client.force_login(self.analista)
        response = self.client.post(
            reverse("ticket_resolver", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_ticket_resolver_administrativo_forbidden(self):
        """Administrativo NO debe poder resolver tickets."""
        self.client.force_login(self.administrativo)
        response = self.client.post(
            reverse("ticket_resolver", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 403)

    # -----------------------------------------------------------
    # ticket_asignar
    # -----------------------------------------------------------

    def test_ticket_asignar_get_admin(self):
        """GET: admin debe ver el formulario de asignación."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("ticket_asignar", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "direccion/ticket_form.html")

    def test_ticket_asignar_post_admin(self):
        """POST: admin puede asignar ticket y cambia estado/prioridad."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("ticket_asignar", args=[self.ticket_analista.pk]),
            {
                "estado": "EN_PROCESO",
                "prioridad": "ALTO",
                "asignado_a": self.admin.pk,
            }
        )
        # Redirige a ticket_detail
        self.assertRedirects(
            response, reverse("ticket_detail", args=[self.ticket_analista.pk])
        )
        self.ticket_analista.refresh_from_db()
        self.assertEqual(self.ticket_analista.estado, "EN_PROCESO")
        self.assertEqual(self.ticket_analista.prioridad, "ALTO")
        self.assertEqual(self.ticket_analista.asignado_a, self.admin)

    def test_ticket_asignar_creates_history(self):
        """Asignar debe registrar cambios en estado, prioridad y asignación."""
        self.client.force_login(self.admin)
        self.client.post(
            reverse("ticket_asignar", args=[self.ticket_analista.pk]),
            {
                "estado": "EN_PROCESO",
                "prioridad": "ALTO",
                "asignado_a": self.admin.pk,
            }
        )
        historial = self.ticket_analista.historial.all()
        self.assertEqual(historial.count(), 3)
        campos = [h.campo for h in historial]
        self.assertIn("estado", campos)
        self.assertIn("prioridad", campos)
        self.assertIn("asignado_a", campos)

    def test_ticket_asignar_analista_forbidden(self):
        """Analista NO debe poder asignar tickets (solo admin)."""
        self.client.force_login(self.analista)
        response = self.client.get(
            reverse("ticket_asignar", args=[self.ticket_analista.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_ticket_asignar_unauthenticated_redirects(self):
        """Usuario no autenticado debe ser redirigido al login."""
        response = self.client.get(
            reverse("ticket_asignar", args=[self.ticket_analista.pk])
        )
        self.assertRedirects(response, reverse("login"))

    def test_ticket_asignar_post_same_values_no_extra_history(self):
        """Asignar con los mismos valores no debe crear historial extra."""
        self.client.force_login(self.admin)
        # Primera asignación: cambia todo
        self.client.post(
            reverse("ticket_asignar", args=[self.ticket_analista.pk]),
            {
                "estado": "EN_PROCESO",
                "prioridad": "ALTO",
                "asignado_a": self.admin.pk,
            }
        )
        # Segunda asignación: mismos valores
        self.client.post(
            reverse("ticket_asignar", args=[self.ticket_analista.pk]),
            {
                "estado": "EN_PROCESO",
                "prioridad": "ALTO",
                "asignado_a": self.admin.pk,
            }
        )
        # Solo debe haber 3 registros (de la primera vez), no 6
        self.assertEqual(self.ticket_analista.historial.count(), 3)


# ============================================================
# INFORMES DIARIOS EXPORT ZIP TESTS
# ============================================================


class InformeDiarioExportZipTest(TestCase):
    """Pruebas para la vista de descarga ZIP de informes diarios."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            "admin_inf", "admin_inf@a.com", "pass",
            first_name="Admin", last_name="Informes"
        )
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

        cls.analista = User.objects.create_user(
            "analista_inf", "analista_inf@a.com", "pass",
            first_name="Analista", last_name="Inf"
        )
        UserProfile.objects.create(user=cls.analista, rol="ANALISTA")

        # Crear informes en diferentes fechas
        from datetime import date
        cls.inf_ene_1 = InformeDiario.objects.create(
            titulo="Informe enero 1",
            contenido="Contenido del informe de enero 1",
            fecha=date(2025, 1, 15),
            creado_por=cls.admin,
        )
        cls.inf_ene_2 = InformeDiario.objects.create(
            titulo="Informe enero 2",
            contenido="Contenido del informe de enero 2",
            fecha=date(2025, 1, 20),
            creado_por=cls.analista,
        )
        cls.inf_jun = InformeDiario.objects.create(
            titulo="Informe junio",
            contenido="Contenido del informe de junio",
            fecha=date(2025, 6, 10),
            creado_por=cls.admin,
        )

    def _check_zip_response(self, response, expected_count, expected_filename_substring):
        """Helper: verifica que la respuesta sea un ZIP valido con N archivos .pdf."""
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(expected_filename_substring, response["Content-Disposition"].lower())
        # Extraer y leer el ZIP
        import zipfile
        from io import BytesIO
        buf = BytesIO(response.content)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            self.assertEqual(len(names), expected_count)
            # Cada archivo debe ser .pdf y tener contenido
            for name in names:
                self.assertTrue(name.endswith('.pdf'), f"{name} debe ser .pdf")
                info = zf.getinfo(name)
                self.assertGreater(info.file_size, 0, f"{name} no debe estar vacio")
        return names

    # -----------------------------------------------------------
    # exportar_informes_descargar — tipo=mes
    # -----------------------------------------------------------

    def test_export_mes_admin_returns_zip(self):
        """Admin descarga ZIP de un mes con informes."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informes_descargar") + "?tipo=mes&mes=1&anio=2025"
        )
        names = self._check_zip_response(response, 2, "january")
        self.assertIn("2025-01-15", names[0])
        self.assertIn("2025-01-20", names[1])

    def test_export_mes_analista_allowed(self):
        """Analista tambien puede descargar ZIP."""
        self.client.force_login(self.analista)
        response = self.client.get(
            reverse("informes_descargar") + "?tipo=mes&mes=6&anio=2025"
        )
        self._check_zip_response(response, 1, "june")

    def test_export_mes_empty_month(self):
        """Mes sin informes devuelve ZIP vacio."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informes_descargar") + "?tipo=mes&mes=3&anio=2025"
        )
        self._check_zip_response(response, 0, "march")

    def test_export_mes_defaults_to_current_month(self):
        """Sin parametros tipo=mes, usa mes/anio actual."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("informes_descargar") + "?tipo=mes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")



    # -----------------------------------------------------------
    # exportar_informes_descargar — tipo=semana
    # -----------------------------------------------------------

    def test_export_semana_with_informes(self):
        """Descargar informes de una semana especifica."""
        # Los informes de enero 2025: 15 (miercoles) esta en la semana 3, 20 (lunes) en la semana 4
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informes_descargar") + "?tipo=semana&semana=3&anio=2025"
        )
        self._check_zip_response(response, 1, "semana_3")

    def test_export_semana_empty(self):
        """Semana sin informes devuelve ZIP vacio."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informes_descargar") + "?tipo=semana&semana=10&anio=2025"
        )
        self._check_zip_response(response, 0, "semana_10")


# ============================================================
# INFORMES DIARIOS PREVIEW PDF TESTS
# ============================================================


class InformeDiarioPreviewPdfTest(TestCase):
    """Pruebas para la vista de previsualización PDF de un informe individual."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            "admin_preview", "admin_pv@a.com", "pass",
            first_name="Admin", last_name="Preview"
        )
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

        cls.analista = User.objects.create_user(
            "analista_preview", "analista_pv@a.com", "pass",
        )
        UserProfile.objects.create(user=cls.analista, rol="ANALISTA")

        cls.administrativo = User.objects.create_user(
            "adminis_preview", "adminis_pv@a.com", "pass",
        )
        UserProfile.objects.create(user=cls.administrativo, rol="ADMINISTRATIVO")

        from datetime import date
        cls.informe = InformeDiario.objects.create(
            titulo="Informe preview test",
            contenido="Contenido de prueba para la previsualización.",
            fecha=date(2025, 3, 15),
            creado_por=cls.admin,
        )

    # -----------------------------------------------------------
    # previsualizar_informe_pdf
    # -----------------------------------------------------------

    def test_preview_admin_returns_inline_pdf(self):
        """Admin debe recibir PDF inline con Content-Disposition: inline."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informe_diario_preview", args=[self.informe.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"].lower())
        self.assertGreater(len(response.content), 200)

    def test_preview_analista_allowed(self):
        """Analista tambien puede previsualizar PDF."""
        self.client.force_login(self.analista)
        response = self.client.get(
            reverse("informe_diario_preview", args=[self.informe.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("inline", response["Content-Disposition"].lower())

    def test_preview_administrativo_allowed(self):
        """Administrativo tambien puede previsualizar PDF."""
        self.client.force_login(self.administrativo)
        response = self.client.get(
            reverse("informe_diario_preview", args=[self.informe.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("inline", response["Content-Disposition"].lower())

    def test_preview_404_for_nonexistent(self):
        """Previsualizar informe inexistente debe devolver 404."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informe_diario_preview", args=[9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_preview_unauthenticated_redirects(self):
        """Usuario no autenticado debe ser redirigido al login."""
        response = self.client.get(
            reverse("informe_diario_preview", args=[self.informe.pk])
        )
        self.assertRedirects(response, reverse("login"))

    def test_preview_filename_includes_date_and_title(self):
        """El filename del PDF debe incluir fecha y parte del título."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("informe_diario_preview", args=[self.informe.pk])
        )
        disposition = response["Content-Disposition"].lower()
        self.assertIn("2025-03-15", disposition)
        self.assertIn(".pdf", disposition)


# ============================================================
# AUDIT LOG VIEW TESTS
# ============================================================


class AuditLogViewTest(TestCase):
    """Pruebas para las vistas de auditoría con filtros por periodo y exportación."""

    @classmethod
    def setUpTestData(cls):
        from datetime import datetime, timedelta
        cls.admin = User.objects.create_user(
            "admin_audit", "admin_audit@a.com", "pass",
            first_name="Admin", last_name="Audit"
        )
        UserProfile.objects.create(user=cls.admin, rol="ADMINISTRADOR")

        cls.analista = User.objects.create_user(
            "analista_audit", "analista_audit@a.com", "pass",
        )
        UserProfile.objects.create(user=cls.analista, rol="ANALISTA")

        now = datetime.now()
        # Create audit logs at different times
        for i in range(5):
            AuditLog.objects.create(
                usuario=cls.admin,
                username=cls.admin.username,
                accion="CREAR",
                modelo="Personal",
                objeto_repr=f"Test log {i}",
                detalle=f"Detalle {i}",
                direccion_ip="127.0.0.1",
                fecha=now - timedelta(days=i),
            )

    # -----------------------------------------------------------
    # audit_log_list — tabs
    # -----------------------------------------------------------

    def test_audit_list_admin_allowed(self):
        """Admin debe poder acceder a la lista de auditoría."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit_log_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "direccion/audit_log_list.html")
        self.assertContains(response, "Test log")

    def test_audit_list_periodo_dia(self):
        """Filtro por día debe incluir logs de hoy."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit_log_list") + "?periodo=dia")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test log 0")

    def test_audit_list_periodo_mes_con_filtro(self):
        """Filtro por mes debe funcionar."""
        self.client.force_login(self.admin)
        from datetime import datetime
        hoy = datetime.now()
        response = self.client.get(
            reverse("audit_log_list") +
            f"?periodo=mes&mes={hoy.month}&anio={hoy.year}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test log")

    def test_audit_list_filtro_modelo(self):
        """Filtro por modelo debe mostrar solo los logs de ese modelo."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("audit_log_list") + "?modelo=Personal"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test log")

    def test_audit_list_filtro_accion(self):
        """Filtro por acción debe mostrar solo los logs de CREAR."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("audit_log_list") + "?accion=CREAR"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Creación")

    def test_audit_list_analista_forbidden(self):
        """Analista NO debe poder acceder a auditoría."""
        self.client.force_login(self.analista)
        response = self.client.get(reverse("audit_log_list"))
        self.assertEqual(response.status_code, 403)

    def test_audit_list_unauthenticated_redirects(self):
        """No autenticado redirige al login."""
        response = self.client.get(reverse("audit_log_list"))
        self.assertRedirects(response, reverse("login"))

    # -----------------------------------------------------------
    # exportar_auditoria_excel
    # -----------------------------------------------------------

    def test_export_excel_admin_allowed(self):
        """Admin puede exportar auditoría a Excel."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit_log_export_excel") + "?periodo=dia")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(".xlsx", response["Content-Disposition"])

    def test_export_excel_analista_forbidden(self):
        """Analista NO puede exportar auditoría a Excel."""
        self.client.force_login(self.analista)
        response = self.client.get(reverse("audit_log_export_excel") + "?periodo=dia")
        self.assertEqual(response.status_code, 403)

    def test_export_excel_with_filters(self):
        """Exportar Excel con filtros de modelo y acción."""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("audit_log_export_excel") +
            "?periodo=dia&modelo=Personal&accion=CREAR"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])

    # -----------------------------------------------------------
    # exportar_auditoria_pdf
    # -----------------------------------------------------------

    def test_export_pdf_admin_allowed(self):
        """Admin puede exportar auditoría a PDF."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("audit_log_export_pdf") + "?periodo=dia")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_export_pdf_analista_forbidden(self):
        """Analista NO puede exportar auditoría a PDF."""
        self.client.force_login(self.analista)
        response = self.client.get(reverse("audit_log_export_pdf") + "?periodo=dia")
        self.assertEqual(response.status_code, 403)

    def test_export_pdf_with_filters(self):
        """Exportar PDF con filtros mes y modelo."""
        self.client.force_login(self.admin)
        from datetime import datetime
        hoy = datetime.now()
        response = self.client.get(
            reverse("audit_log_export_pdf") +
            f"?periodo=mes&mes={hoy.month}&anio={hoy.year}&modelo=Personal"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


# ============================================================
# PERMISSIONS SYSTEM TESTS
# ============================================================


class PermissionsSystemTest(TestCase):
    """Pruebas del sistema granular de permisos."""

    def test_permisos_para_rol_admin_has_all(self):
        """ADMINISTRADOR debe tener todos los permisos."""
        from .permissions import permisos_para_rol, DASHBOARD_VER, PERSONAL_VER, BACKUP_RESTAURAR
        perms = permisos_para_rol('ADMINISTRADOR')
        self.assertIn(DASHBOARD_VER, perms)
        self.assertIn(PERSONAL_VER, perms)
        self.assertIn(BACKUP_RESTAURAR, perms)

    def test_tiene_permiso_supervisor(self):
        """SUPERVISOR debe tener permisos de edicion pero NO de eliminacion."""
        from .permissions import tiene_permiso, PERSONAL_CREAR, PERSONAL_ELIMINAR, CASOS_EDITAR, CASOS_ELIMINAR
        self.assertTrue(tiene_permiso('SUPERVISOR', PERSONAL_CREAR))
        self.assertFalse(tiene_permiso('SUPERVISOR', PERSONAL_ELIMINAR))
        self.assertTrue(tiene_permiso('SUPERVISOR', CASOS_EDITAR))
        self.assertFalse(tiene_permiso('SUPERVISOR', CASOS_ELIMINAR))

    def test_tiene_permiso_analista_limited(self):
        """ANALISTA debe tener permisos basicos pero NO de investigados."""
        from .permissions import tiene_permiso, INFORMES_VER, INVESTIGADOS_VER, CASOS_VER, REPORTES_VER, BIENES_VER
        self.assertTrue(tiene_permiso('ANALISTA', INFORMES_VER))
        self.assertFalse(tiene_permiso('ANALISTA', INVESTIGADOS_VER))
        self.assertFalse(tiene_permiso('ANALISTA', CASOS_VER))
        self.assertFalse(tiene_permiso('ANALISTA', REPORTES_VER))
        self.assertFalse(tiene_permiso('ANALISTA', BIENES_VER))

    def test_tiene_permiso_administrativo(self):
        """ADMINISTRATIVO debe tener permisos operativos pero no de eliminacion."""
        from .permissions import tiene_permiso, CASOS_CREAR, CASOS_ELIMINAR, INVESTIGADOS_CREAR, INVESTIGADOS_EDITAR, REPORTES_VER
        self.assertTrue(tiene_permiso('ADMINISTRATIVO', CASOS_CREAR))
        self.assertFalse(tiene_permiso('ADMINISTRATIVO', CASOS_ELIMINAR))
        self.assertTrue(tiene_permiso('ADMINISTRATIVO', INVESTIGADOS_CREAR))
        self.assertFalse(tiene_permiso('ADMINISTRATIVO', INVESTIGADOS_EDITAR))
        self.assertTrue(tiene_permiso('ADMINISTRATIVO', REPORTES_VER))

    def test_permiso_requerido_decorator_grants_access(self):
        """Usuario con permiso debe acceder a la vista decorada."""
        from django.contrib.auth.models import User
        from .models import UserProfile
        admin = User.objects.create_user('perm_admin', 'p@a.com', 'pass')
        UserProfile.objects.create(user=admin, rol='ADMINISTRADOR')
        self.client.force_login(admin)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_permiso_requerido_decorator_denies_access(self):
        """Usuario sin permiso debe recibir 403."""
        from django.contrib.auth.models import User
        from .models import UserProfile
        analista = User.objects.create_user('perm_analista', 'p2@a.com', 'pass')
        UserProfile.objects.create(user=analista, rol='ANALISTA')
        self.client.force_login(analista)
        # Audit log view requires AUDITORIA_VER which ANALISTA doesn't have
        response = self.client.get(reverse('audit_log_list'))
        self.assertEqual(response.status_code, 403)

    def test_supervisor_role_choice_exists(self):
        """El rol SUPERVISOR debe estar en ROL_CHOICES."""
        from .models import UserProfile
        choices = dict(UserProfile.ROL_CHOICES)
        self.assertIn('SUPERVISOR', choices)
        self.assertEqual(choices['SUPERVISOR'], 'Supervisor')

    def test_profile_tiene_permiso_method(self):
        """UserProfile.tiene_permiso() debe funcionar correctamente."""
        from django.contrib.auth.models import User
        from .models import UserProfile
        from .permissions import INFORMES_CREAR, BACKUP_DESCARGAR

        analista = User.objects.create_user('test_met', 'tm@a.com', 'pass')
        UserProfile.objects.create(user=analista, rol='ANALISTA')

        profile = analista.profile
        self.assertTrue(profile.tiene_permiso(INFORMES_CREAR))
        self.assertFalse(profile.tiene_permiso(BACKUP_DESCARGAR))

    def test_ticket_list_supervisor_sees_all(self):
        """SUPERVISOR debe ver todos los tickets (como admin)."""
        from django.contrib.auth.models import User
        from .models import UserProfile, TicketSoporte

        supervisor = User.objects.create_user('super_ticket', 'st@a.com', 'pass')
        UserProfile.objects.create(user=supervisor, rol='SUPERVISOR')
        self.client.force_login(supervisor)

        response = self.client.get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 200)

    def test_rol_requerido_adm_crear(self):
        """Vista con PERSONAL_CREAR: ADMINISTRADOR y ANALISTA pueden."""
        from django.contrib.auth.models import User
        from .models import UserProfile

        admin = User.objects.create_user('rol_adm', 'ra@a.com', 'pass')
        UserProfile.objects.create(user=admin, rol='ADMINISTRADOR')
        analista = User.objects.create_user('rol_ana', 'ran@a.com', 'pass')
        UserProfile.objects.create(user=analista, rol='ANALISTA')

        # PersonalCreate requires PERSONAL_CREAR (ambos roles tienen el permiso)
        self.client.force_login(admin)
        response = self.client.get(reverse('personal_create'))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(analista)
        response = self.client.get(reverse('personal_create'))
        self.assertEqual(response.status_code, 200)

    def test_supervisor_can_edit_personal(self):
        """SUPERVISOR debe poder editar personal (tiene PERSONAL_EDITAR)."""
        from django.contrib.auth.models import User
        from .models import UserProfile, Personal

        sup = User.objects.create_user('super_edit', 'se@a.com', 'pass')
        UserProfile.objects.create(user=sup, rol='SUPERVISOR')

        p = Personal.objects.create(apellidos='Test', nombres='User', cedula='V-99999999')

        self.client.force_login(sup)
        response = self.client.get(reverse('personal_edit', args=[p.pk]))
        self.assertEqual(response.status_code, 200)

    def test_supervisor_cannot_delete_personal(self):
        """SUPERVISOR NO debe poder eliminar personal (sin PERSONAL_ELIMINAR)."""
        from django.contrib.auth.models import User
        from .models import UserProfile, Personal

        sup = User.objects.create_user('super_del', 'sd@a.com', 'pass')
        UserProfile.objects.create(user=sup, rol='SUPERVISOR')

        p = Personal.objects.create(apellidos='Test2', nombres='User2', cedula='V-88888888')

        self.client.force_login(sup)
        response = self.client.get(reverse('personal_delete', args=[p.pk]))
        self.assertEqual(response.status_code, 403)

    def test_ticket_create_supervisor_allowed(self):
        """SUPERVISOR debe poder crear tickets (tiene TICKETS_CREAR)."""
        from django.contrib.auth.models import User
        from .models import UserProfile

        sup = User.objects.create_user('super_tk', 'stk@a.com', 'pass')
        UserProfile.objects.create(user=sup, rol='SUPERVISOR')

        self.client.force_login(sup)
        response = self.client.get(reverse('ticket_create'))
        self.assertEqual(response.status_code, 200)