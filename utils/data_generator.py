import time
import random
import string

def generate_random_string(length=6):
    """Генерация случайной строки для обеспечения уникальности."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def generate_user_data():
    """Генерация уникальных валидных данных для регистрации нового пользователя."""
    unique_suffix = int(time.time())
    random_str = generate_random_string()
    password = f"Secure_{random_str}123!"

    return {
        "email": f"user_{unique_suffix}_{random_str}@cinescope.ru",
        "username": f"user_{unique_suffix}_{random_str}",
        "fullName": "Иванов Иван Иванович",
        "password": password,
        "passwordRepeat": password
    }

def generate_movie_data():
    """Генерация уникальных данных для создания фильма."""
    unique_suffix = int(time.time())
    return {
        "title": f"Inception {unique_suffix}",
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology.",
        "year": 2010,
        "director": "Christopher Nolan",
        "genre": "Sci-Fi"
    }