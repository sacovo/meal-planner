from django.apps import AppConfig


class MealsConfig(AppConfig):
    name = "meals"

    def ready(self):
        import meals.signals  # noqa: F401 — registers signal handlers
