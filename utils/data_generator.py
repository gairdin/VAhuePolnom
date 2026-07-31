"""
Генераторы тестовых данных для пользователей и фильмов.

Функции возвращают словари, совместимые со схемами RegisterDto и CreateMovieDto
из Swagger-спецификации.

Пример:
    from utils.data_generator import generate_user_data, generate_movie_data
    user = generate_user_data()
    movie = generate_movie_data()
"""

import time
import random

# ID жанров, существующих в БД (подсмотрены через GET /movies).
# Значения вне этого списка (1-3, 5-6) вернут 400 Bad Request.
VALID_GENRE_IDS = [4, 7, 8, 9, 10]


def generate_user_data() -> dict:
    """
    Сгенерировать данные для регистрации нового пользователя.

    Формат: RegisterDto (email, fullName, password, passwordRepeat).
    Email гарантированно уникален — содержит timestamp + random.
    Пароль фиксированный: SecurePassword123.
    """
    unique_suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    password = "SecurePassword123"
    return {
        "email": f"user_{unique_suffix}@cinescope.ru",
        "fullName": "Иванов Иван Иванович",
        "password": password,
        "passwordRepeat": password,
    }


def generate_movie_data() -> dict:
    """
    Сгенерировать данные для создания нового фильма.

    Формат: CreateMovieDto (name, price, description, location, published, genreId).
    Название содержит timestamp — это защита от 409 Conflict при параллельных тестах.
    """
    unique_suffix = int(time.time())
    return {
        "name": f"Inception_{unique_suffix}",
        "price": random.randint(290, 990),
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology.",
        "location": random.choice(["MSK", "SPB"]),
        "published": True,
        "genreId": random.choice(VALID_GENRE_IDS),
    }