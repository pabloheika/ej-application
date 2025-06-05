# src/ej_dataviz/serializers.py

from rest_framework import serializers
from ej_clusters.models.cluster import Cluster

class ClusterSerializer(serializers.ModelSerializer):
    """
    Serializador básico para expor os campos de um Cluster.
    """
    class Meta:
        model = Cluster
        fields = [
            "id",
            "name",
            "description",
        ]
        read_only_fields = ["id"]
