import time
import random


def generate_user_data():
    unique_suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    password = "SecurePassword123"
    return {
        "email": f"user_{unique_suffix}@cinescope.ru",
        "fullName": "Иванов Иван Иванович",
        "password": password,
        "passwordRepeat": password
    }


VALID_GENRE_IDS = [4, 7, 8, 9, 10]


def generate_movie_data():
    unique_suffix = int(time.time())
    return {
        "name": f"Inception_{unique_suffix}",
        "price": random.randint(290, 990),
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology.",
        "location": random.choice(["MSK", "SPB"]),
        "published": True,
        "genreId": random.choice(VALID_GENRE_IDS)
    }