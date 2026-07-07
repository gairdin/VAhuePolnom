import pytest
from utils.data_generator import generate_movie_data


# =====================================================================
# ПОЗИТИВНЫЕ ТЕСТЫ (public GET endpoints)
# =====================================================================

def test_get_existing_movie_by_id(api_manager, existing_movie):
    """Проверка получения фильма по ID — существующий в БД фильм (pre-seeded)."""
    movie_id = existing_movie["id"]
    response = api_manager.movies.get_movie_by_id(movie_id, expected_status=200)
    movie = response.json()

    assert movie["id"] == movie_id
    assert movie["name"] == existing_movie["name"]
    assert movie["price"] == existing_movie["price"]
    assert movie["location"] == existing_movie["location"]


def test_get_movies_with_filters(api_manager, existing_movie):
    """Проверка фильтрации списка фильмов по локации (pre-seeded данные)."""
    target_location = existing_movie["location"]

    params = {"locations": [target_location]}
    response = api_manager.movies.get_movies_list(params=params, expected_status=200)
    data = response.json()

    assert len(data["movies"]) > 0, f"Нет фильмов с локацией {target_location}"
    for movie in data["movies"]:
        assert movie["location"] == target_location, \
            f"Фильм {movie['id']} не соответствует фильтру локации"


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


def test_create_movie_duplicate_name_forbidden(api_manager, registered_user, existing_movie, movie_data):
    """Нельзя создать фильм как USER — даже с дублирующимся именем, так как нет прав SUPER_ADMIN."""
    api_manager.auth.authenticate(registered_user)

    response = api_manager.movies.create_movie(movie_data, expected_status=None)

    assert response.status_code == 403, \
        f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"


def test_create_movie_missing_required_fields_forbidden(api_manager, registered_user):
    """Отправка пустого тела запроса как USER возвращает 403 (нет прав SUPER_ADMIN)."""
    api_manager.auth.authenticate(registered_user)

    invalid_data = {}
    response = api_manager.movies.create_movie(invalid_data, expected_status=None)

    assert response.status_code == 403, \
        f"Ожидался статус 403 (Forbidden), но получен {response.status_code}"