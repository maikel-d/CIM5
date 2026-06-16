
from django.db import migrations


class Migration(migrations.Migration):
    """Registra CarpetaDireccion como aplicada (tabla ya existe)."""
    
    dependencies = [
        ("direccion", "0021_documentocarpetabien"),
    ]

    operations = []
