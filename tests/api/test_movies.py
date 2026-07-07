import pytest
from utils.data_generator import generate_movie_data


# =====================================================================
# ПОЗИТИВНЫЕ ТЕСТЫ (CRUD + ФИЛЬТРЫ)
# =====================================================================

def test_create_and_get_movie(api_manager, admin_creds, movie_data):
    """Создание фильма под SUPER_ADMIN, затем получение по ID и проверка полей."""
    api_manager.auth.authenticate(admin_creds)

    create_res = api_manager.movies.create_movie(movie_data, expected_status=201)
    created_movie = create_res.json()
    movie_id = created_movie["id"]

    try:
        get_res = api_manager.movies.get_movie_by_id(movie_id, expected_status=200)
        movie_body = get_res.json()

        assert movie_body["name"] == movie_data["name"]
        assert movie_body["price"] == movie_data["price"]
        assert movie_body["location"] == movie_data["location"]
        assert movie_body["description"] == movie_data["description"]

    finally:
        api_manager.movies.delete_movie(movie_id, expected_status=200)


def test_get_movies_with_filters(api_manager, admin_creds, created_movie_with_cleanup):
    """Проверка фильтрации списка фильмов по локации."""
    api_manager.auth.authenticate(admin_creds)
    target_location = created_movie_with_cleanup["location"]

    params = {"locations": [target_location]}
    response = api_manager.movies.get_movies_list(params=params, expected_status=200)
    data = response.json()

    assert len(data["movies"]) > 0, f"Нет фильмов с локацией {target_location}"
    for movie in data["movies"]:
        assert movie["location"] == target_location, \
            f"Фильм {movie['id']} не соответствует фильтру локации"


def test_patch_movie_success(api_manager, admin_creds, created_movie_with_cleanup):
    """Редактирование (PATCH) фильма под SUPER_ADMIN."""
    api_manager.auth.authenticate(admin_creds)
    movie_id = created_movie_with_cleanup["id"]

    update_data = {"price": 9999}
    response = api_manager.movies.patch_movie(movie_id, data=update_data, expected_status=200)

    assert response.status_code == 200
    assert response.json()["price"] == 9999


# =====================================================================
# НЕГАТИВНЫЕ ТЕСТЫ — права доступа (USER не имеет прав SUPER_ADMIN)
# =====================================================================

def test_create_movie_as_regular_user_forbidden(api_manager, registered_user, movie_data):
    """Обычный пользователь (USER) не может создавать фильмы — 403 Forbidden."""
    api_manager.auth.authenticate(registered_user)

    response = api_manager.movies.create_movie(movie_data, expected_status=None)

    assert response.status_code == 403, \
        f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"


def test_patch_movie_as_regular_user_forbidden(api_manager, registered_user, existing_movie):
    """Обычный пользователь (USER) не может редактировать фильмы — 403 Forbidden."""
    api_manager.auth.authenticate(registered_user)
    movie_id = existing_movie["id"]

    update_data = {"price": 9999}
    response = api_manager.movies.patch_movie(movie_id, data=update_data, expected_status=None)

    assert response.status_code == 403, \
        f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"


def test_delete_movie_as_regular_user_forbidden(api_manager, registered_user, existing_movie):
    """Обычный пользователь (USER) не может удалять фильмы — 403 Forbidden."""
    api_manager.auth.authenticate(registered_user)
    movie_id = existing_movie["id"]

    response = api_manager.movies.delete_movie(movie_id, expected_status=None)

    assert response.status_code == 403, \
        f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"

def test_delete_non_existing_movie(api_manager, admin_creds):
    api_manager.auth.authenticate(admin_creds)
    movie_id = 999999999999999999999999999
    response = api_manager.movies.delete_movie(movie_id, expected_status=None)
    assert response.status_code == 404, \
        f"фильма нема такого, {response.status_code}"


def test_create_movie_duplicate_name_conflict(api_manager, admin_creds, created_movie_with_cleanup):
    """Нельзя создать фильм с уже существующим названием — 409 Conflict."""
    api_manager.auth.authenticate(admin_creds)

    duplicate_movie_data = {
        "name": created_movie_with_cleanup["name"],
        "price": 500,
        "description": "Duplicate",
        "location": "MSK",
        "published": True,
        "genreId": 4
    }

    response = api_manager.movies.create_movie(duplicate_movie_data, expected_status=None)

    assert response.status_code == 409, \
        f"Ожидался статус 409 при дублировании имени, но получен {response.status_code}"


def test_create_movie_missing_required_fields_bad_request(api_manager, admin_creds):
    """Отправка пустого тела запроса под SUPER_ADMIN — 400/422 Bad Request."""
    api_manager.auth.authenticate(admin_creds)

    invalid_data = {}
    response = api_manager.movies.create_movie(invalid_data, expected_status=None)

    assert response.status_code in [400, 422], \
        f"Ожидался статус 400/422 при валидации схемы, но получен {response.status_code}"


def test_get_movie_by_nonexistent_id(api_manager):
    """Запрос несуществующего фильма — 404 Not Found."""
    response = api_manager.movies.get_movie_by_id(0, expected_status=None)

    assert response.status_code == 404, \
        f"Ожидался статус 404, но получен {response.status_code}"


def test_create_movie_with_invalid_genre_id(api_manager, admin_creds):
    """Создание фильма с несуществующим genreId — 400 Bad Request."""
    api_manager.auth.authenticate(admin_creds)

    invalid_data = {
        "name": "Invalid Genre Movie",
        "price": 500,
        "description": "Test",
        "location": "MSK",
        "published": True,
        "genreId": 999
    }
    response = api_manager.movies.create_movie(invalid_data, expected_status=None)

    assert response.status_code == 400, \
        f"Ожидался статус 400, но получен {response.status_code}"