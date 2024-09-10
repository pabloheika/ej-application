from ej_profiles.models import Profile
from rest_framework import serializers
from .enums import Ethnicity, Race, Gender, Region, AgeRange


class ProfileSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    phone_number = serializers.CharField(max_length=20, required=False)
    ethnicity_choices = serializers.ChoiceField(
        choices=[(tag.value, tag) for tag in Ethnicity], required=False
    )
    race = serializers.ChoiceField(
        choices=[(tag.value, tag) for tag in Race], required=False
    )
    gender = serializers.ChoiceField(
        choices=[(tag.value, tag) for tag in Gender], required=False
    )
    birth_date = serializers.DateField(required=False)
    age_range = serializers.ChoiceField(
        choices=[(tag.value, tag) for tag in AgeRange], required=False
    )
    region = serializers.ChoiceField(
        choices=[(tag.value, tag) for tag in Region], required=False
    )

    class Meta:
        model = Profile
        fields = [
            "user",
            "phone_number",
            "ethnicity_choices",
            "race",
            "gender",
            "birth_date",
            "age_range",
            "region",
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
