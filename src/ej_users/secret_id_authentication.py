from rest_framework.response import Response
from .models import User
from .manager import convert_anonymous_participation_to_regular_user


class SecretIdAuthentication:
    def __init__(self, serializer):
        self.serializer = serializer

    def handle_unique_secret_id_error(self, serializer, request):
        if serializer.errors.get("secret_id")[0].code == "invalid":
            anonymous_user = User.objects.get(secret_id=request.data["secret_id"])
            anonymous_user.secret_id = None
            anonymous_user.save()

            serializer = self.serializer(data=request.data)
            if not serializer.is_valid():
                anonymous_user.secret_id = request.data["secret_id"]
                anonymous_user.save()
                return Response(serializer.errors, status=400)

            user = serializer.save()
            user = convert_anonymous_participation_to_regular_user(anonymous_user, user)
            user.save()
            return user
        return None

    def handle_invalid_email_error(self, request):
        user_secret = User.objects.get(secret_id=request.data["secret_id"])
        user_email = User.objects.get(email=request.data["email"])
        if user_secret != user_email:
            user_secret.secret_id = None
            user_secret.save()
            user_email.secret_id = request.data["secret_id"]
            user_email.save()

            user = convert_anonymous_participation_to_regular_user(
                user_secret, user_email
            )
            user.save()
            return user
        return None
