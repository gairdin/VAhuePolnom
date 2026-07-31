"""
ApiManager — единая точка входа во все API-клиенты.

В тестах используется фикстура api_manager, которая уже всё настроила:
    api_manager.auth      # клиент для auth.dev-cinescope.f5qa.ru
    api_manager.movies    # клиент для api.dev-cinescope.f5qa.ru
"""

from clients.auth_api import AuthAPI
from clients.movies_api import MoviesAPI
from clients.user_api import UserApi


class ApiManager:
    def __init__(self, session, auth_url: str, movies_url: str):
        self.session = session
        self.auth = AuthAPI(session=session, base_url=auth_url)
        self.movies = MoviesAPI(session=session, base_url=movies_url)
        self.user_api = UserApi(session=session, base_url=auth_url)

    def close_session(self):
        self.session.close()