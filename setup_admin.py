import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.contrib.auth.models import User
from direccion.models import UserProfile

admin = User.objects.filter(username='admin').first()
if not admin:
    # Usar variable de entorno ADMIN_PASSWORD, o default admin321
    password = os.environ.get('ADMIN_PASSWORD', 'admin321')
    admin = User.objects.create_superuser('admin', 'admin@direccion.gob.ve', password)
    print()
    print('=' * 42)
    print('  SUPERUSUARIO CREADO')
    print('=' * 42)
    print(f'  Usuario:  admin')
    print(f'  Password: {password}')
    print('=' * 42)
    print('  GUARDA ESTAS CREDENCIALES EN UN LUGAR SEGURO')
    print('=' * 42)
    print()
else:
    print('[OK] Superusuario ya existe')

if not hasattr(admin, 'profile'):
    UserProfile.objects.create(user=admin, rol='ADMINISTRADOR')
    print('[OK] Perfil ADMINISTRADOR creado')
else:
    print('[OK] Perfil ya existe:', admin.profile.get_rol_display())
