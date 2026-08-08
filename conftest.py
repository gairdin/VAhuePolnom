import pytest
import requests
from clients.api_manager import ApiManager
from enums.hosts import Hosts
from utils.data_generator import generate_user_data, generate_movie_data
from entities.movie import Movie
from entities.user import User
from constants.roles import Roles
from resources.user_creds import SuperAdminCreds
from clients.db_client import DbClient
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def db_client():
    client = DbClient()
    yield client
    client.close()


@pytest.fixture
def db_conn(db_client):
    return db_client.conn

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


@pytest.fixture(scope="session")
def admin_creds():
    return {
        "email": "api1@gmail.com",
        "password": "asdqwe123Q"
    }


@pytest.fixture
def movie_data():
    return generate_movie_data()


@pytest.fixture(scope="session")
def existing_movies(api_manager):
    """Фикстура — список уже существующих в БД фильмов (pre-seeded), валидированный через Movie."""
    response = api_manager.movies.get_movies_list(expected_status=200)
    data = response.json()
    assert len(data["movies"]) > 0, "Нет предзагруженных фильмов для тестов"
    return [Movie(**movie) for movie in data["movies"]]


@pytest.fixture
def existing_movie(existing_movies):
    """Фикстура — один существующий фильм."""
    return existing_movies[0]


@pytest.fixture
def created_movie_with_cleanup(api_manager, movie_data, admin_creds):
    """Фикстура создания фильма под SUPER_ADMIN с последующим удалением."""
    api_manager.auth.authenticate(admin_creds)

    response = api_manager.movies.create_movie(movie_data, expected_status=201)
    movie_body = Movie(**response.json())

    yield movie_body

    movie_id = movie_body.id
    api_manager.movies.delete_movie(movie_id, expected_status=200)


@pytest.fixture
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_session = ApiManager(session=session, auth_url=Hosts.AUTH.value, movies_url=Hosts.MOVIES.value)
        user_pool.append(user_session)
        return user_session

    yield _create_user_session

    for user in user_pool:
        user.close_session()


@pytest.fixture
def test_user():
    data = generate_user_data()
    data["roles"] = [Roles.USER.value]
    return data


@pytest.fixture
def creation_user_data(test_user):
    updated_data = test_user.copy()
    updated_data.update({
        "verified": True,
        "banned": False
    })
    return updated_data


@pytest.fixture
def super_admin(user_session):
    new_session = user_session()
    super_admin = User(
        SuperAdminCreds.USERNAME,
        SuperAdminCreds.PASSWORD,
        [Roles.SUPER_ADMIN.value],
        new_session
    )
    super_admin.api.auth.authenticate(super_admin.creds)
    return super_admin


@pytest.fixture
def common_user(user_session, super_admin, creation_user_data):
    new_session = user_session()
    common_user = User(
        creation_user_data["email"],
        creation_user_data["password"],
        [Roles.USER.value],
        new_session
    )
    super_admin.api.user_api.create_user(creation_user_data)
    common_user.api.auth.authenticate(common_user.creds)
    return common_user