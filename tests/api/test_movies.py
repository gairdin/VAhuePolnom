def test_create_and_get_movie(api_manager, movie_data, auth_creds):
    """Тест создания и последующего чтения фильма через API-клиент."""
    # 1. Авторизуемся (проставляется Bearer в сессию)
    api_manager.auth.authenticate(auth_creds)

    # 2. Создаем фильм
    create_res = api_manager.movies.create_movie(movie_data, expected_status=201).json()
    movie_id = create_res["id"]

    # 3. Получаем фильм по ID и проверяем данные
    get_res = api_manager.movies.get_movie(movie_id, expected_status=200).json()
    assert get_res["title"] == movie_data["title"]
    assert get_res["director"] == movie_data["director"]


def test_delete_movie_via_fixture(api_manager, created_movie_with_cleanup):
    """Тест демонстрирует использование yield-фикстуры для проверки удаления."""
    movie = created_movie_with_cleanup
    movie_id = movie["id"]

    # Вызываем ручку удаления (токен уже проставлен внутри фикстуры при вызове authenticate)
    api_manager.movies.delete_movie(movie_id, expected_status=200)

    # Проверяем, что сущность пропала (ожидаем 404 Not Found)
    api_manager.movies.get_movie(movie_id, expected_status=404)