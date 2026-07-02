from custom_requester.custom_requester import CustomRequester

class MoviesAPI(CustomRequester):
    """
    API-клиент для работы с каталогом фильмов (доменная логика).
    """

    def __init__(self, session, base_url: str):
        super().__init__(base_url=base_url, session=session)

    def create_movie(self, movie_data: dict, expected_status: int = 201):
        """Создание фильма."""
        return self.send_request(
            method="POST",
            endpoint="/movies",
            json=movie_data,
            expected_status=expected_status,
        )

    def get_movie(self, movie_id: str | int, expected_status: int = 200):
        """Получение информации о фильме по ID."""
        return self.send_request(
            method="GET",
            endpoint=f"/movies/{movie_id}",
            expected_status=expected_status,
        )

    def delete_movie(self, movie_id: str | int, expected_status: int = 200):
        """Удаление фильма по ID."""
        return self.send_request(
            method="DELETE",
            endpoint=f"/movies/{movie_id}",
            expected_status=expected_status,
        )