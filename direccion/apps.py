from django.apps import AppConfig


class DireccionConfig(AppConfig):
    name = 'direccion'

    def ready(self):
        import direccion.signals  # noqa
