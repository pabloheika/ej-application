from rest_framework import serializers
from .models import User

try:
    from allauth.account.adapter import get_adapter
except Exception:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")


class RegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, min_length=5, required=True)
    email = serializers.EmailField()

    def save(self, request):
        try:
            user = User.objects.get(email=request.data.get("email"))
        except Exception:
            email = request.data.get("email")
            name = request.data.get("name")
            password = request.data.get("password")
            user = User(email=email, name=name)
            user.set_password(password)
            # Specify profile_data when saving the user, so the profile
            # is created with data, instead of being created empty, then
            # updated with data.
            profile_data = {}
            phone_number = request.data.get("phone_number")
            if phone_number:
                profile_data = {"phone_number": phone_number}
            user.save(profile_data=profile_data)

        self.check_user_metadata(user, request)
        return user

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        return data

    def custom_signup(self, request, user):
        pass

    def get_cleaned_data(self):
        return {
            "username": self.validated_data.get("username", ""),
            "password1": self.validated_data.get("password1", ""),
            "email": self.validated_data.get("email", ""),
        }
