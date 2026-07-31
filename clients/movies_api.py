"""
MoviesAPI — клиент для api.dev-cinescope.f5qa.ru.

Методы покрывают все 5 эндпоинтов фильмов:
    GET    /movies         — get_movies_list(params)
    POST   /movies         — create_movie(data)
    GET    /movies/{id}    — get_movie_by_id(id)
    PATCH  /movies/{id}    — patch_movie(id, data)
    DELETE /movies/{id}    — delete_movie(id)

Требуемые роли (из Swagger):
    GET     — PUBLIC (без авторизации)
    POST    — SUPER_ADMIN
    PATCH   — SUPER_ADMIN
    DELETE  — SUPER_ADMIN
"""

from custom_requester.custom_requester import CustomRequester


class MoviesAPI(CustomRequester):
    """
    CRUD + фильтрация фильмов.
    """

    def __init__(self, session, base_url):
        super().__init__(base_url=base_url, session=session)

    # ------------------------------------------------------------------
    # POST /movies — создать фильм (только SUPER_ADMIN)
    # ------------------------------------------------------------------

    def create_movie(self, data: dict, expected_status=201):
        return self.send_request(
            method="POST",
            endpoint="/movies",
            json=data,
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # GET /movies — список с фильтрацией (PUBLIC)
    # ------------------------------------------------------------------

    def get_movies_list(self, params: dict | None = None, expected_status=200):
        """
        Параметры фильтрации (все опциональны):
            page, pageSize, minPrice, maxPrice,
            locations (список), published, genreId, createdAt
        """
        return self.send_request(
            method="GET",
            endpoint="/movies",
            params=params,
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # GET /movies/{id} — один фильм (PUBLIC)
    # ------------------------------------------------------------------

    def get_movie_by_id(self, movie_id: int, expected_status=200):
        return self.send_request(
            method="GET",
            endpoint=f"/movies/{movie_id}",
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # PATCH /movies/{id} — частичное обновление (только SUPER_ADMIN)
    # ------------------------------------------------------------------

    def patch_movie(self, movie_id: int, data: dict, expected_status=200):
        return self.send_request(
            method="PATCH",
            endpoint=f"/movies/{movie_id}",
            json=data,
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # DELETE /movies/{id} — удалить фильм (только SUPER_ADMIN)
    # ------------------------------------------------------------------

    def delete_movie(self, movie_id: int, expected_status=200):
        return self.send_request(
            method="DELETE",
            endpoint=f"/movies/{movie_id}",
            expected_status=expected_status,
        )