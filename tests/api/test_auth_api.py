def test_register_user_success(api_manager, test_user_data):
    """Проверка успешной регистрации пользователя с валидными данными."""
    response = api_manager.auth.register_user(test_user_data)

    assert response.status_code == 201, f"Ожидался статус 201, но получен {response.status_code}. Ответ: {response.text}"