import pytest
import requests
from clients.api_manager import ApiManager
# Укажи правильный путь до файла генератора в твоем проекте
from utils.data_generator import generate_user_data, generate_movie_data

AUTH_BASE_URL = "https://auth.dev-cinescope.f5qa.ru"
MOVIES_BASE_URL = "https://api.dev-cinescope.f5qa.ru"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    yield s
    s.close()


@pytest.fixture(scope="session")
def api_manager(session):
    return ApiManager(session=session, auth_url=AUTH_BASE_URL, movies_url=MOVIES_BASE_URL)


@pytest.fixture
def test_user_data():
    """Отдает уникальные данные для регистрации нового пользователя."""
    return generate_user_data()


@pytest.fixture
def registered_user(api_manager, test_user_data):
    """
    Фикстура регистрирует пользователя и возвращает ТОЛЬКО те креды,
    которые нужны для авторизации (обычно это email и пароль).
    """
    # Регистрируем пользователя
    api_manager.auth.register_user(test_user_data, expected_status=201)

    # Возвращаем словарь только с нужными полями для эндпоинта логина,
    # чтобы сервер не ругался на лишние данные
    return {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }


@pytest.fixture
def movie_data():
    return generate_movie_data()


@pytest.fixture
def created_movie_with_cleanup(api_manager, movie_data, registered_user):
    # Авторизуемся под только что созданным пользователем
    api_manager.auth.authenticate(registered_user)

    response = api_manager.movies.create_movie(movie_data, expected_status=201)
    movie_body = response.json()

    yield movie_body

    movie_id = movie_body["id"]
    api_manager.movies.delete_movie(movie_id, expected_status=200)