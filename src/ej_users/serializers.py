from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from ej_profiles.serializer import ProfileSerializer
from .models import User


class UsersSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=50, min_length=5, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}, max_length=128
    )
    password_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}, max_length=128
    )
    profile_data = ProfileSerializer(default={})

    class Meta:
        model = User
        fields = ["id", "name", "email", "password", "password_confirm", "profile_data"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(_("Passwords do not match"))
        return data

    def validate_email(self, data):
        if User.objects.filter(email=data).exists():
            raise serializers.ValidationError(_("Email already exists"))
        return data

    def create(self, validated_data):
        user = User(email=validated_data["email"], name=validated_data["name"])
        user.set_password(validated_data["password"])
        # Specify profile_data when saving the user, so it creates a
        # non-empty profile, avoiding another DB access to fill the profile.
        user.save(profile_data=validated_data["profile_data"])
        return user


class UserAuthSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
