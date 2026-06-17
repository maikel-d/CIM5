"""Migration 0023 - cambios reales ya aplicados en BD"""

import direccion.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('direccion', '0022_carpetadireccion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentousuario',
            name='carpeta',
        ),
        migrations.RemoveField(
            model_name='documentousuario',
            name='usuario',
        ),
        migrations.AlterModelOptions(
            name='documentocarpetabien',
            options={'ordering': ['-fecha_subida'], 'verbose_name': 'Documento de Carpeta', 'verbose_name_plural': 'Documentos de Carpetas'},
        ),
        migrations.RemoveField(
            model_name='documentodireccion',
            name='carpeta',
        ),
        migrations.AlterField(
            model_name='carpetabien',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación'),
        ),
        migrations.AlterField(
            model_name='carpetadireccion',
            name='categoria',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Categoría'),
        ),
        migrations.AlterField(
            model_name='carpetadireccion',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación'),
        ),
        migrations.AlterField(
            model_name='documentocarpetabien',
            name='archivo',
            field=models.FileField(help_text='Formatos: PDF, Word (.doc, .docx), imágenes', upload_to=direccion.models.carpeta_bien_document_path, verbose_name='Archivo'),
        ),
        migrations.AlterField(
            model_name='documentocarpetabien',
            name='descripcion',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Descripción'),
        ),
        migrations.DeleteModel(
            name='CarpetaUsuario',
        ),
        migrations.DeleteModel(
            name='DocumentoUsuario',
        ),
    ]
