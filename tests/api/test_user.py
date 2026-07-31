from entities.user_response import UserResponse
from constants.roles import Roles


class TestUser:

    def test_create_user(self, super_admin, creation_user_data):
        response = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)
        user = UserResponse(**response.json())

        assert user.email == creation_user_data["email"]
        assert user.fullName == creation_user_data["fullName"]
        assert user.roles == creation_user_data["roles"]
        assert user.verified is True
        assert user.banned is False

    def test_get_user_by_locator(self, super_admin, creation_user_data):
        created = UserResponse(**super_admin.api.user_api.create_user(creation_user_data).json())

        by_id = UserResponse(**super_admin.api.user_api.get_user(created.id).json())
        by_email = UserResponse(**super_admin.api.user_api.get_user(created.email).json())

        assert by_id == by_email

    def test_get_user_by_id_forbidden_for_common_user(self, common_user):
        common_user.api.user_api.get_user(common_user.email, expected_status=403)

    def test_user_has_expected_role(self, super_admin, creation_user_data):
        created = UserResponse(**super_admin.api.user_api.create_user(creation_user_data).json())

        assert Roles.USER.value in created.roles

    def test_create_user_without_verified_field(self, super_admin, test_user):
        user_data = test_user.copy()
        user_data.pop("roles", None)
        user_data["roles"] = [Roles.USER.value]

        response = super_admin.api.user_api.create_user(user_data, expected_status=400)