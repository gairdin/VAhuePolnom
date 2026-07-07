from custom_requester.custom_requester import CustomRequester


class MoviesAPI(CustomRequester):

    def __init__(self, session, base_url):
        super().__init__(base_url=base_url, session=session)

    def create_movie(self, data, expected_status=201):
        return self.send_request(
            method="POST",
            endpoint="/movies",
            json=data,
            expected_status=expected_status,
        )

    def get_movie_by_id(self, movie_id, expected_status=200):
        return self.send_request(
            method="GET",
            endpoint=f"/movies/{movie_id}",
            expected_status=expected_status,
        )

    def delete_movie(self, movie_id, expected_status=200):
        return self.send_request(
            method="DELETE",
            endpoint=f"/movies/{movie_id}",
            expected_status=expected_status,
        )

    def get_movies_list(self, params=None, expected_status=200):
        return self.send_request(
            method="GET",
            endpoint="/movies",
            params=params,
            expected_status=expected_status,
        )

    def patch_movie(self, movie_id, data, expected_status=200):
        return self.send_request(
            method="PATCH",
            endpoint=f"/movies/{movie_id}",
            json=data,
            expected_status=expected_status,
        )