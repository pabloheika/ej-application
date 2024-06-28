from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
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
    secret_id = serializers.CharField(required=False, write_only=True)

    anonymous = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "password",
            "password_confirm",
            "secret_id",
            "anonymous",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(_("Passwords do not match"))
        return data

    def validate_email(self, data):
        if User.objects.filter(email=data).exists():
            raise serializers.ValidationError(_("Email already exists"))
        return data

    def validate_secret_id(self, data):
        if User.objects.filter(secret_id=data).exists():
            raise serializers.ValidationError(_("Secret ID already exists"))
        return data

    def validate_anonymous(self, data):
        if data:
            return data
        return False

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            name=validated_data["name"],
        )
        if "secret_id" in validated_data:
            user.secret_id = validated_data["secret_id"]

        if "anonymous" in validated_data:
            user.anonymous = validated_data["anonymous"]

        user.set_password(validated_data["password"])
        user.save()
        return user


class UserAuthSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    secret_id = serializers.CharField(required=False)
