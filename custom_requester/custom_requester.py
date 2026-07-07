import requests

class CustomRequester:
    """
    Базовый слой для централизованной отправки HTTP-запросов.
    Управляет сессией, базовыми заголовками и проверкой статус-кодов.
    """

    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, base_url: str, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

        self.headers = self.base_headers.copy()
        self.session.headers.update(self.headers)

    def _update_session_headers(self, **kwargs):
        """
        Обновляет заголовки как в локальном словаре класса, так и внутри requests.Session.
        """
        self.headers.update(kwargs)
        self.session.headers.update(kwargs)

    def send_request(self, method: str, endpoint: str, expected_status: int | None = 200, **kwargs):
        url = f"{self.base_url}{endpoint}"

        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=self.headers,
            **kwargs
        )

        if expected_status is not None and response.status_code != expected_status:
            raise AssertionError(
                f"{method.upper()} {url} -> Получен статус {response.status_code}, ожидался {expected_status}\n"
                f"Тело ответа: {response.text}"
            )

        return response