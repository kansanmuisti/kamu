from django.apps import AppConfig

class ParliamentConfig(AppConfig):
    name = 'parliament'
    verbose_name = "Parliament"

    def ready(self):
        pass
