"""
Signals para limpiar archivos del disco al eliminar o actualizar modelos.
Usa @receiver con sender especifico para evitar hooks innecesarios.
"""
import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

# Modelos con campos de archivo
from direccion.models import (
    Personal, Investigado, InformeDiario,
    DocumentoPersonal, DocumentoInvestigado,
    DocumentoCaso, DocumentoBien, DocumentoCarpetaBien,
)

FILE_MODEL_FIELDS = {
    Personal: ["foto"],
    Investigado: ["foto"],
    InformeDiario: ["archivo"],
    DocumentoPersonal: ["archivo"],
    DocumentoInvestigado: ["archivo"],
    DocumentoCaso: ["archivo"],
    DocumentoBien: ["archivo"],
    DocumentoCarpetaBien: ["archivo"],
}


models_that_have_files = list(FILE_MODEL_FIELDS.keys())


def _delete_file_from_disk(file_field):
    """Elimina un archivo del disco si existe."""
    if file_field and os.path.isfile(file_field.path):
        os.remove(file_field.path)


@receiver(post_delete, sender=Personal)
@receiver(post_delete, sender=Investigado)
@receiver(post_delete, sender=InformeDiario)
@receiver(post_delete, sender=DocumentoPersonal)
@receiver(post_delete, sender=DocumentoInvestigado)
@receiver(post_delete, sender=DocumentoCaso)
@receiver(post_delete, sender=DocumentoBien)
@receiver(post_delete, sender=DocumentoCarpetaBien)
def cleanup_files_on_delete(sender, instance, **kwargs):
    """Elimina archivos del disco al borrar un modelo con campos de archivo."""
    fields = FILE_MODEL_FIELDS.get(sender, [])
    for field_name in fields:
        _delete_file_from_disk(getattr(instance, field_name, None))


@receiver(pre_save, sender=Personal)
@receiver(pre_save, sender=Investigado)
@receiver(pre_save, sender=InformeDiario)
@receiver(pre_save, sender=DocumentoPersonal)
@receiver(pre_save, sender=DocumentoInvestigado)
@receiver(pre_save, sender=DocumentoCaso)
@receiver(pre_save, sender=DocumentoBien)
@receiver(pre_save, sender=DocumentoCarpetaBien)
def cleanup_old_file_on_update(sender, instance, **kwargs):
    """Elimina archivo anterior si se reemplaza por uno nuevo."""
    if not instance.pk:
        return
    fields = FILE_MODEL_FIELDS.get(sender, [])
    if not fields:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    for field_name in fields:
        old_file = getattr(old, field_name, None)
        new_file = getattr(instance, field_name, None)
        if old_file and old_file != new_file:
            _delete_file_from_disk(old_file)
