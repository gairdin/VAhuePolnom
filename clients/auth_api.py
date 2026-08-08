"""
AuthAPI — клиент для auth.dev-cinescope.f5qa.ru.

Методы:
    register_user(user_data)  -> POST /register
    login(creds)              -> POST /login
    authenticate(creds)       -> POST /login + сохраняет Bearer-токен в сессию
"""

from custom_requester.custom_requester import CustomRequester


class AuthAPI(CustomRequester):
    """
    API-клиент для регистрации, входа и получения JWT-токена.
    """

    def __init__(self, session, base_url: str):
        super().__init__(base_url=base_url, session=session)

    # ------------------------------------------------------------------
    # Регистрация
    # ------------------------------------------------------------------

    def register_user(self, user_data: dict, expected_status: int = 201):
        """
        POST /register — создать нового пользователя.

        Ожидаемый статус: 201 (успех) или 409 (email уже занят).
        """
        return self.send_request(
            method="POST",
            endpoint="/register",
            json=user_data,
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # Логин
    # ------------------------------------------------------------------

    def login(self, creds: dict, expected_status: int = 200):
        """
        POST /login — получить accessToken + refreshToken.

        Ожидаемый статус: 200 (успех) или 401 (неверный логин/пароль).
        """
        return self.send_request(
            method="POST",
            endpoint="/login",
            json=creds,
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # Аутентификация (логин + сохранение токена в заголовки сессии)
    # ------------------------------------------------------------------

    def authenticate(self, creds: dict) -> str:
        """
        Залогиниться и сохранить JWT-токен в заголовки сессии.

        После вызова все следующие запросы (через api_manager.movies)
        будут автоматически содержать Authorization: Bearer <token>.

        Возвращает: строку accessToken.
        """
        response_data = self.login(creds).json()

        if "accessToken" not in response_data:
            raise KeyError(
                f"Ключ 'accessToken' не найден в ответе авторизации: {response_data}"
            )

        token = response_data["accessToken"]
        self._update_session_headers(Authorization=f"Bearer {token}")
        return token
