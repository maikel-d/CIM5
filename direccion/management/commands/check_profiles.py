from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from direccion.models import UserProfile


class Command(BaseCommand):
    help = "Verifica que todos los usuarios tengan UserProfile y crea los faltantes"

    def handle(self, *args, **options):
        users = User.objects.all()
        total = users.count()
        ok = 0
        created = 0

        for user in users:
            try:
                _ = user.profile
                ok += 1
            except UserProfile.DoesNotExist:
                if user.is_superuser:
                    rol = "ADMINISTRADOR"
                else:
                    rol = "ADMINISTRATIVO"

                UserProfile.objects.create(user=user, rol=rol)
                created += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  [+] Perfil creado para '{user.username}' -> {rol}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"\n=== RESUMEN ==="))
        self.stdout.write(f"  Usuarios totales:     {total}")
        self.stdout.write(self.style.SUCCESS(f"  Perfiles existentes:  {ok}"))
        if created:
            self.stdout.write(self.style.WARNING(f"  Perfiles creados:     {created}"))
        else:
            self.stdout.write(f"  Perfiles creados:     {created}")

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ Listo. Vuelve a intentar eliminar el documento ahora."
                )
            )
