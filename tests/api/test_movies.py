import allure
import pytest
from entities.movie import MoviesResponse


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
# ТЕСТЫ С ПРОВЕРКОЙ В БД
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
# НЕГАТИВНЫЕ ТЕСТЫ
# =====================================================================

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