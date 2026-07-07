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


def generate_movie_data():
    unique_suffix = int(time.time())
    return {
        "name": f"Inception_{unique_suffix}",
        "price": round(random.uniform(290, 990), 2),
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology.",
        "location": random.choice(["MSK", "SPB"]),
        "published": True,
        "genreId": random.randint(1, 5)
    }