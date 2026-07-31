import requests


class CustomRequester:
    """
    Базовый класс для отправки HTTP-запросов.

    - Автоматически подставляет base_url к endpoint
    - Устанавливает заголовки Content-Type и Accept
    - Проверяет статус-код ответа (если expected_status != None)
    - Позволяет обновлять заголовки (например, Authorization) через сессию

    Как использовать:
        class MoviesAPI(CustomRequester):
            def get_movie(self, id):
                return self.send_request("GET", f"/movies/{id}")
    """

    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, base_url: str, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session if session else requests.Session()

        self.headers = self.base_headers.copy()
        self.session.headers.update(self.headers)

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    def _update_session_headers(self, **kwargs):
        """
        Обновить заголовки сессии (например, добавить Authorization после логина).
        Вызывается из auth_api.authenticate() — руками не трогать.
        """
        self.headers.update(kwargs)
        self.session.headers.update(kwargs)

    # ------------------------------------------------------------------
    # Основной метод
    # ------------------------------------------------------------------

    def send_request(
        self,
        method: str,
        endpoint: str,
        expected_status: int | None = 200,
        **kwargs,
    ) -> requests.Response:
        """
        Отправить HTTP-запрос и проверить статус ответа.

        Параметры:
            method           — "GET", "POST", "PATCH", "DELETE"
            endpoint         — /movies, /login и т.д. (добавляется к base_url)
            expected_status  — ожидаемый статус (200, 201 …).
                               None — пропустить проверку (для негативных тестов)
            **kwargs         — json=, params=, data= … (передаются в requests)

        Возвращает:
            requests.Response

        Пример:
            self.send_request("POST", "/movies", json={…}, expected_status=201)
        """
        url = f"{self.base_url}{endpoint}"

        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=self.headers,
            **kwargs,
        )

        if expected_status is not None and response.status_code != expected_status:
            raise AssertionError(
                f"{method.upper()} {url} -> "
                f"Получен статус {response.status_code}, ожидался {expected_status}\n"
                f"Тело ответа: {response.text}"
            )

        return response