import allure
import pytest
from utils.data_generator import generate_movie_data
from entities.movie import Movie, MoviesResponse


# =====================================================================
# ПОЗИТИВНЫЕ ТЕСТЫ (CRUD + ФИЛЬТРЫ)
# =====================================================================

@pytest.mark.smoke
@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("CRUD")
@allure.story("Create and Get movie")
@allure.title("Создание фильма и получение по ID")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_and_get_movie(api_manager, admin_creds, movie_data):
    """Создание фильма под SUPER_ADMIN, затем получение по ID и проверка полей."""
    api_manager.auth.authenticate(admin_creds)

    with allure.step("Создать фильм POST /movies"):
        create_res = api_manager.movies.create_movie(movie_data, expected_status=201)
        created_movie = Movie(**create_res.json())
        movie_id = created_movie.id

    try:
        with allure.step("Получить фильм по ID GET /movies/{id}"):
            get_res = api_manager.movies.get_movie_by_id(movie_id, expected_status=200)
            movie_body = Movie(**get_res.json())

        with allure.step("Проверить совпадение полей"):
            assert movie_body.name == movie_data["name"]
            assert movie_body.price == movie_data["price"]
            assert movie_body.location == movie_data["location"]
            assert movie_body.description == movie_data["description"]

    finally:
        api_manager.movies.delete_movie(movie_id, expected_status=200)


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Filters")
@allure.story("Filter by location")
@allure.title("Фильтрация списка фильмов по локации")
@allure.severity(allure.severity_level.NORMAL)
def test_get_movies_with_filters(api_manager, admin_creds, created_movie_with_cleanup):
    """Проверка фильтрации списка фильмов по локации."""
    api_manager.auth.authenticate(admin_creds)
    target_location = created_movie_with_cleanup.location

    with allure.step(f"Запросить фильмы с локацией {target_location}"):
        params = {"locations": [target_location]}
        response = api_manager.movies.get_movies_list(params=params, expected_status=200)
        data = response.json()
        movies_response = MoviesResponse(**data)

    with allure.step("Проверить, что все фильмы соответствуют локации"):
        assert len(movies_response.movies) > 0, f"Нет фильмов с локацией {target_location}"
        for movie in movies_response.movies:
            assert movie.location == target_location, \
                f"Фильм {movie.id} не соответствует фильтру локации"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("CRUD")
@allure.story("Patch movie")
@allure.title("Редактирование фильма (PATCH)")
@allure.severity(allure.severity_level.CRITICAL)
def test_patch_movie_success(api_manager, admin_creds, created_movie_with_cleanup):
    """Редактирование (PATCH) фильма под SUPER_ADMIN."""
    api_manager.auth.authenticate(admin_creds)
    movie_id = created_movie_with_cleanup.id

    with allure.step(f"Обновить цену фильма {movie_id}"):
        update_data = {"price": 9999}
        response = api_manager.movies.patch_movie(movie_id, data=update_data, expected_status=200)

    with allure.step("Проверить, что цена изменилась"):
        patched_movie = Movie(**response.json())
        assert patched_movie.price == 9999


# =====================================================================
# ПАРАМЕТРИЗОВАННЫЙ ТЕСТ — фильтрация по разным локациям
# =====================================================================

@pytest.mark.smoke
@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Filters")
@allure.story("Parametrized location filter")
@allure.title("Фильтрация фильмов по локации: {location}")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("location", ["MSK", "SPB"])
def test_get_movies_filter_by_location_parametrized(api_manager, location):
    """Параметризованный тест: проверка фильтрации по разным локациям."""
    with allure.step(f"Запросить фильмы с локацией {location}"):
        params = {"locations": [location]}
        response = api_manager.movies.get_movies_list(params=params, expected_status=200)
        data = response.json()
        movies_response = MoviesResponse(**data)

    with allure.step("Проверить, что все фильмы соответствуют локации"):
        for movie in movies_response.movies:
            assert movie.location == location, \
                f"Фильм {movie.id} не соответствует фильтру локации {location}"


# =====================================================================
# ТЕСТ С ПРОВЕРКОЙ В БД
# =====================================================================

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.db
@allure.epic("Movies")
@allure.feature("CRUD")
@allure.story("Create movie with DB verification")
@allure.title("Создание фильма с проверкой в БД")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_movie_and_verify_in_db(api_manager, admin_creds, movie_data, db_client):
    """Создание фильма и проверка, что он появился в БД."""
    api_manager.auth.authenticate(admin_creds)

    with allure.step("Создать фильм через API"):
        create_res = api_manager.movies.create_movie(movie_data, expected_status=201)
        created_movie = Movie(**create_res.json())
        movie_id = created_movie.id

    try:
        with allure.step("Проверить наличие фильма в БД через SQL"):
            row = db_client.get_movie_by_id(movie_id)

        with allure.step("Сверить данные из БД с отправленными"):
            assert row is not None, f"Фильм с id {movie_id} не найден в БД"
            db_name, db_price, db_location = row[1], row[2], row[3]
            assert db_name == movie_data["name"], f"Имя в БД ({db_name}) не совпадает"
            assert db_price == movie_data["price"], f"Цена в БД ({db_price}) не совпадает"
            assert db_location == movie_data["location"], f"Локация в БД ({db_location}) не совпадает"
    finally:
        api_manager.movies.delete_movie(movie_id, expected_status=200)


# =====================================================================
# ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ С ПРОВЕРКОЙ В БД
# =====================================================================

@pytest.mark.regression
@pytest.mark.db
@allure.epic("Movies")
@allure.feature("DB")
@allure.story("Genre exists in DB")
@allure.title("Проверка существования жанра фильма в БД")
@allure.severity(allure.severity_level.NORMAL)
def test_movie_genre_exists_in_db(api_manager, db_client, existing_movie):
    """Проверка, что genre_id фильма существует в таблице genres."""
    movie_id = existing_movie.id
    movie_genre_id = existing_movie.genreId

    with allure.step(f"Проверить genre_id={movie_genre_id} в таблице genres"):
        genre = db_client.get_genre_by_id(movie_genre_id)

    with allure.step("Убедиться, что жанр существует"):
        assert genre is not None, f"Жанр с id {movie_genre_id} не найден в БД"
        assert genre[0] == movie_genre_id


@pytest.mark.regression
@pytest.mark.db
@allure.epic("Movies")
@allure.feature("DB")
@allure.story("Movies in API vs DB")
@allure.title("Проверка соответствия фильмов в API и БД (первые 5)")
@allure.severity(allure.severity_level.NORMAL)
def test_movies_api_results_exist_in_db(api_manager, db_client):
    """Проверка, что первые 5 фильмов из API существуют в БД."""
    with allure.step("Получить список фильмов через API"):
        response = api_manager.movies.get_movies_list(expected_status=200)
        data = response.json()
        movies_response = MoviesResponse(**data)

    with allure.step("Проверить каждый фильм в БД"):
        for movie in movies_response.movies[:5]:
            row = db_client.get_movie_by_id(movie.id)
            assert row is not None, f"Фильм id={movie.id} из API не найден в БД"
            assert row[1] == movie.name, f"Имя фильма id={movie.id} не совпадает"


# =====================================================================
# НЕГАТИВНЫЕ ТЕСТЫ — права доступа (USER не имеет прав SUPER_ADMIN)
# =====================================================================

@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Authorization")
@allure.story("Regular user forbidden")
@allure.title("Обычный пользователь не может создавать фильмы — 403")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_movie_as_regular_user_forbidden(api_manager, registered_user, movie_data):
    """Обычный пользователь (USER) не может создавать фильмы — 403 Forbidden."""
    api_manager.auth.authenticate(registered_user)

    with allure.step("Попробовать создать фильм под USER"):
        response = api_manager.movies.create_movie(movie_data, expected_status=None)

    with allure.step("Проверить статус 403"):
        assert response.status_code == 403, \
            f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Authorization")
@allure.story("Regular user forbidden")
@allure.title("Обычный пользователь не может редактировать фильмы — 403")
@allure.severity(allure.severity_level.NORMAL)
def test_patch_movie_as_regular_user_forbidden(api_manager, registered_user, existing_movie):
    """Обычный пользователь (USER) не может редактировать фильмы — 403 Forbidden."""
    api_manager.auth.authenticate(registered_user)
    movie_id = existing_movie.id

    with allure.step("Попробовать изменить фильм под USER"):
        update_data = {"price": 9999}
        response = api_manager.movies.patch_movie(movie_id, data=update_data, expected_status=None)

    with allure.step("Проверить статус 403"):
        assert response.status_code == 403, \
            f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Authorization")
@allure.story("Regular user forbidden")
@allure.title("Обычный пользователь не может удалять фильмы — 403")
@allure.severity(allure.severity_level.NORMAL)
def test_delete_movie_as_regular_user_forbidden(api_manager, registered_user, existing_movie):
    """Обычный пользователь (USER) не может удалять фильмы — 403 Forbidden."""
    api_manager.auth.authenticate(registered_user)
    movie_id = existing_movie.id

    with allure.step("Попробовать удалить фильм под USER"):
        response = api_manager.movies.delete_movie(movie_id, expected_status=None)

    with allure.step("Проверить статус 403"):
        assert response.status_code == 403, \
            f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Negative")
@allure.story("Delete non-existing")
@allure.title("Удаление несуществующего фильма — 404")
@allure.severity(allure.severity_level.NORMAL)
def test_delete_non_existing_movie(api_manager, admin_creds):
    api_manager.auth.authenticate(admin_creds)
    movie_id = 999999999999999999999999999
    with allure.step("Попробовать удалить несуществующий фильм"):
        response = api_manager.movies.delete_movie(movie_id, expected_status=None)
    assert response.status_code == 404, \
        f"фильма нема такого, {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Negative")
@allure.story("Duplicate name")
@allure.title("Создание фильма с дублирующимся названием — 409")
@allure.severity(allure.severity_level.NORMAL)
def test_create_movie_duplicate_name_conflict(api_manager, admin_creds, created_movie_with_cleanup):
    """Нельзя создать фильм с уже существующим названием — 409 Conflict."""
    api_manager.auth.authenticate(admin_creds)

    with allure.step("Создать фильм с существующим названием"):
        duplicate_movie_data = {
            "name": created_movie_with_cleanup.name,
            "price": 500,
            "description": "Duplicate",
            "location": "MSK",
            "published": True,
            "genreId": 4
        }
        response = api_manager.movies.create_movie(duplicate_movie_data, expected_status=None)

    with allure.step("Проверить статус 409"):
        assert response.status_code == 409, \
            f"Ожидался статус 409 при дублировании имени, но получен {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Negative")
@allure.story("Missing required fields")
@allure.title("Создание фильма с пустым телом — 400/422")
@allure.severity(allure.severity_level.NORMAL)
def test_create_movie_missing_required_fields_bad_request(api_manager, admin_creds):
    """Отправка пустого тела запроса под SUPER_ADMIN — 400/422 Bad Request."""
    api_manager.auth.authenticate(admin_creds)

    with allure.step("Отправить пустое тело запроса"):
        invalid_data = {}
        response = api_manager.movies.create_movie(invalid_data, expected_status=None)

    with allure.step("Проверить статус 400 или 422"):
        assert response.status_code in [400, 422], \
            f"Ожидался статус 400/422 при валидации схемы, но получен {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Negative")
@allure.story("Non-existing ID")
@allure.title("Запрос несуществующего фильма — 404")
@allure.severity(allure.severity_level.NORMAL)
def test_get_movie_by_nonexistent_id(api_manager):
    """Запрос несуществующего фильма — 404 Not Found."""
    with allure.step("Запросить фильм с id=0"):
        response = api_manager.movies.get_movie_by_id(0, expected_status=None)

    with allure.step("Проверить статус 404"):
        assert response.status_code == 404, \
            f"Ожидался статус 404, но получен {response.status_code}"


@pytest.mark.regression
@allure.epic("Movies")
@allure.feature("Negative")
@allure.story("Invalid genre")
@allure.title("Создание фильма с несуществующим genreId — 400")
@allure.severity(allure.severity_level.NORMAL)
def test_create_movie_with_invalid_genre_id(api_manager, admin_creds):
    """Создание фильма с несуществующим genreId — 400 Bad Request."""
    api_manager.auth.authenticate(admin_creds)

    with allure.step("Создать фильм с genreId=999"):
        invalid_data = {
            "name": "Invalid Genre Movie",
            "price": 500,
            "description": "Test",
            "location": "MSK",
            "published": True,
            "genreId": 999
        }
        response = api_manager.movies.create_movie(invalid_data, expected_status=None)

    with allure.step("Проверить статус 400"):
        assert response.status_code == 400, \
            f"Ожидался статус 400, но получен {response.status_code}"
