from django.db import migrations, models
import django
import direccion.models


class Migration(migrations.Migration):

    dependencies = [
        ("direccion", "0020_bien_carpeta"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentoCarpetaBien",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("archivo", models.FileField(help_text="Formatos: PDF, Word (.doc, .docx), imagenes", upload_to=direccion.models.carpeta_bien_document_path, verbose_name="Archivo")),
                ("tipo", models.CharField(choices=[("PDF", "PDF"), ("WORD", "Word"), ("IMAGEN", "Imagen"), ("OTRO", "Otro")], db_index=True, editable=False, max_length=10, verbose_name="Tipo")),
                ("descripcion", models.CharField(blank=True, max_length=255, null=True, verbose_name="Descripcion")),
                ("fecha_subida", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha de subida")),
                ("carpeta", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documentos", to="direccion.carpetabien", verbose_name="Carpeta")),
            ],
            options={
                "verbose_name": "Documento de Carpeta de Bienes",
                "verbose_name_plural": "Documentos de Carpetas de Bienes",
                "ordering": ["-fecha_subida"],
            },
        ),
    ]
