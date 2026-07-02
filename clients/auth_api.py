from custom_requester.custom_requester import CustomRequester

class AuthAPI(CustomRequester):
    """
    API-клиент для управления аутентификацией и пользователями Cinescope.
    """

    def __init__(self, session, base_url: str):
        super().__init__(base_url=base_url, session=session)

    def register_user(self, user_data: dict, expected_status: int = 201):
        """Регистрация нового пользователя."""
        return self.send_request(
            method="POST",
            endpoint="/register",
            json=user_data,
            expected_status=expected_status,
        )

    def login(self, creds: dict, expected_status: int = 200):
        """Авторизация (получение токена)."""
        return self.send_request(
            method="POST",
            endpoint="/login",
            json=creds,
            expected_status=expected_status,
        )

    def authenticate(self, creds: dict) -> str:
        """
        Авторизация + автоматическое сохранение JWT-токена в заголовки сессии.
        """
        response_data = self.login(creds).json()

        if "token" not in response_data:
            raise KeyError(f"Ключ 'token' не найден в ответе авторизации: {response_data}")

        token = response_data["token"]
        self._update_session_headers(Authorization=f"Bearer {token}")
        return token
