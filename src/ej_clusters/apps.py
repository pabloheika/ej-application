from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EjClustersConfig(AppConfig):
    name = "ej_clusters"
    verbose_name = _("Clusters")
    rules = None
    api = None

    def ready(self):
        from . import rules
        from . import api
        from . import signals

        self.rules = rules
        self.api = api
        self.signals = signals
