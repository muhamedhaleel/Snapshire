from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token):
    User = get_user_model()

    try:
        access_token = AccessToken(token)
        user_id = access_token["user_id"]

        return User.objects.get(
            pk=user_id,
            is_active=True,
        )
    except (
        InvalidToken,
        TokenError,
        User.DoesNotExist,
        KeyError,
    ):
        return None


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope = dict(scope)

        params = parse_qs(
            scope.get("query_string", b"").decode("utf-8")
        )
        token = params.get("token", [None])[0]

        scope["user"] = (
            await get_user_from_token(token)
            if token
            else None
        )

        return await self.app(scope, receive, send)