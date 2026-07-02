def test_register_user_success(api_manager, test_user_data):
    """Проверка успешной регистрации пользователя с валидными данными."""
    response = api_manager.auth.register_user(test_user_data)

    assert response.status_code == 201, f"Ожидался статус 201, но получен {response.status_code}. Ответ: {response.text}"


def test_login_and_token_generation(api_manager, registered_user):
    """Проверка генерации JWT токена при успешном логине созданного пользователя."""
    # В registered_user уже лежат email и password ТОЛЬКО ЧТО созданного юзера из фикстуры
    response = api_manager.auth.login(registered_user)

    assert response.status_code == 200, f"Ожидался статус 200, но получен {response.status_code}. Ответ: {response.text}"

    response_json = response.json()
    assert "token" in response_json, f"В ответе сервера нет ключа 'token'. Ответ: {response_json}"