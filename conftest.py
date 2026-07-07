import pytest
import requests
from clients.api_manager import ApiManager
from enums.hosts import Hosts
from utils.data_generator import generate_user_data, generate_movie_data


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    yield s
    s.close()


@pytest.fixture(scope="session")
def api_manager(session):
    return ApiManager(
        session=session,
        auth_url=Hosts.AUTH.value,
        movies_url=Hosts.MOVIES.value
    )


@pytest.fixture
def test_user_data():
    return generate_user_data()


@pytest.fixture
def registered_user(api_manager, test_user_data):
    api_manager.auth.register_user(test_user_data, expected_status=201)
    return {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }


@pytest.fixture
def movie_data():
    return generate_movie_data()


@pytest.fixture(scope="session")
def existing_movies(api_manager):
    """Фикстура — список уже существующих в БД фильмов (pre-seeded)."""
    response = api_manager.movies.get_movies_list(expected_status=200)
    data = response.json()
    assert len(data["movies"]) > 0, "Нет предзагруженных фильмов для тестов"
    return data["movies"]


@pytest.fixture
def existing_movie(existing_movies):
    """Фикстура — один существующий фильм."""
    return existing_movies[0]