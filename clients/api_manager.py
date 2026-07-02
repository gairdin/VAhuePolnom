from clients.auth_api import AuthAPI
from clients.movies_api import MoviesAPI


class ApiManager:
    """
    Менеджер единой точки входа.
    Инициализирует доменные API-клиенты с их собственными базовыми URL.
    """

    def __init__(self, session, auth_url: str, movies_url: str):
        self.session = session

        # Разводим клиенты по разным поддоменам
        self.auth = AuthAPI(session=session, base_url=auth_url)
        self.movies = MoviesAPI(session=session, base_url=movies_url)