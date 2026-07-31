from custom_requester.custom_requester import CustomRequester


class UserApi(CustomRequester):
    def __init__(self, session, base_url: str):
        super().__init__(base_url=base_url, session=session)

    def get_user(self, user_locator, expected_status=200):
        return self.send_request(
            method="GET",
            endpoint=f"/user/{user_locator}",
            expected_status=expected_status,
        )

    def create_user(self, user_data: dict, expected_status=201):
        return self.send_request(
            method="POST",
            endpoint="/user",
            json=user_data,
            expected_status=expected_status,
        )