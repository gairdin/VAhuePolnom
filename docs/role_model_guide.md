# Ролевая модель, параметризация, аннотации и .env

## Содержание

1. [Ролевая модель](#1-ролевая-модель)
2. [Параметризация тестов](#2-параметризация-тестов)
3. [Аннотации типов](#3-аннотации-типов)
4. [Хранение секретов (.env)](#4-хранение-секретов-env)
5. [Практические задания](#5-практические-задания)

---

## 1. Ролевая модель

### Зачем нужна

Без ролевой модели каждый тест сам заботится об аутентификации:

```python
def test_create_movie(api_manager, admin_creds, movie_data):
    api_manager.auth.authenticate(admin_creds)          # ← боilerplate
    api_manager.movies.create_movie(movie_data)
```

С ролевой моделью тест просто указывает, от чьего лица работает:

```python
def test_create_movie(super_admin, movie_data):
    super_admin.api.movies.create_movie(movie_data)     # ← super_admin уже залогинен
```

### Компоненты ролевой модели

#### 1.1 Модель User

```python
class User:
    """Представляет пользователя системы с его учётными данными и API-доступом."""

    def __init__(self, email: str, password: str, roles: list, api: ApiManager):
        self.email = email
        self.password = password
        self.roles = roles
        self.api = api  # ApiManager для выполнения запросов от имени этого юзера

    @property
    def creds(self):
        """Кортеж (email, password) для передачи в authenticate()."""
        return self.email, self.password
```

**Почему это удобно:**

- `user.creds` → `("user@mail.com", "pass123")` — не нужно помнить порядок полей
- `user.api` — доступ ко всем API-клиентам (auth, movies, user...)
- Можно расширять: добавить `user.id`, `user.token` и т.д.

#### 1.2 Enum ролей

```python
# constants/roles.py
from enum import Enum

class Roles(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
```

**Зачем Enum, а не просто строка:**
- `Roles.SUPER_ADMIN.value` — автодополнение в IDE, нельзя ошибиться
- `"SUPER_ADMIN"` — можно опечататься: `"SUPER_ADMINN"` → тихая ошибка
- Если роль переименуют — меняешь в одном месте, а не по всем файлам

#### 1.3 Фикстура user_session (фабрика сессий)

Управляет жизненным циклом HTTP-сессий. Каждый юзер получает свою сессию.

```python
@pytest.fixture
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_session = ApiManager(session)
        user_pool.append(user_session)
        return user_session

    yield _create_user_session

    # Cleanup: закрыть все созданные сессии
    for user in user_pool:
        user.close_session()
```

**Важно:** `ApiManager` нужно доработать — добавить метод `close_session()`:

```python
def close_session(self):
    self.session.close()
```

#### 1.4 Фикстура super_admin

```python
@pytest.fixture
def super_admin(user_session):
    new_session = user_session()

    super_admin = User(
        SuperAdminCreds.USERNAME,
        SuperAdminCreds.PASSWORD,
        [Roles.SUPER_ADMIN.value],
        new_session
    )

    super_admin.api.auth_api.authenticate(super_admin.creds)
    return super_admin
```

**Что происходит:**
1. Создаётся новая HTTP-сессия
2. Создаётся объект `User` с кредами супер-админа
3. Выполняется аутентификация — токен сохраняется в заголовки сессии
4. Готовый объект возвращается в тест

#### 1.5 Фикстура common_user (обычный юзер)

```python
@pytest.fixture
def common_user(user_session, super_admin, creation_user_data):
    new_session = user_session()

    common_user = User(
        creation_user_data['email'],
        creation_user_data['password'],
        [Roles.USER.value],
        new_session
    )

    super_admin.api.user_api.create_user(creation_user_data)
    common_user.api.auth_api.authenticate(common_user.creds)
    return common_user
```

**Отличие от super_admin:** юзера сначала нужно создать через API (это делает super_admin), а потом залогинить.

#### 1.6 Фикстура данных для создания юзера

```python
@pytest.fixture(scope="function")
def creation_user_data(test_user):
    updated_data = test_user.copy()
    updated_data.update({
        "verified": True,
        "banned": False
    })
    return updated_data
```

⚠️ **Важно:** словари — изменяемый тип. Без `.copy()` фикстура `test_user` и `creation_user_data` будут ссылаться на один и тот же объект.

### Как это работает в тесте

```python
class TestUser:

    def test_create_user(self, super_admin, creation_user_data):
        response = super_admin.api.user_api.create_user(creation_user_data).json()

        assert response.get('id') and response['id'] != ''
        assert response.get('email') == creation_user_data['email']
        assert response.get('fullName') == creation_user_data['fullName']
        assert response.get('roles', []) == creation_user_data['roles']
        assert response.get('verified') is True

    def test_get_user_by_locator(self, super_admin, creation_user_data):
        created = super_admin.api.user_api.create_user(creation_user_data).json()

        by_id = super_admin.api.user_api.get_user(created['id']).json()
        by_email = super_admin.api.user_api.get_user(creation_user_data['email']).json()

        assert by_id == by_email

    def test_get_user_by_id_forbidden_for_user(self, common_user):
        common_user.api.user_api.get_user(common_user.email, expected_status=403)
```

**Ключевой момент:** третьему тесту не нужен `super_admin` — он проверяет, что `common_user` (роль USER) получает 403. Тест лаконичный и самодокументируемый.

---

## 2. Параметризация тестов

### Проблема

Нужно проверить один и тот же сценарий с разными входными данными. Без параметризации — копипаст:

```python
def test_login_valid_admin(api_manager):
    api_manager.auth.login({"email": "api1@gmail.com", "password": "asdqwe123Q"}, expected_status=201)

def test_login_invalid_user(api_manager):
    api_manager.auth.login({"email": "no@user.com", "password": "wrong"}, expected_status=500)

def test_login_empty_username(api_manager):
    api_manager.auth.login({"email": "", "password": "pass"}, expected_status=500)
```

### Решение: `@pytest.mark.parametrize`

```python
@pytest.mark.parametrize("email,password,expected_status", [
    ("api1@gmail.com",               "asdqwe123Q",   201),
    ("no@user.com",                  "wrong",        500),
    ("",                             "pass",         500),
], ids=["valid admin", "invalid user", "empty username"])
def test_login(api_manager, email, password, expected_status):
    login_data = {"email": email, "password": password}
    api_manager.auth.login(login_data, expected_status=expected_status)
```

### Синтаксис

```python
# Один параметр
@pytest.mark.parametrize("name", ["Alice", "Bob", "Charlie"])

# Несколько параметров — список кортежей
@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (4, 5, 9), (10, 20, 30)])

# С читаемыми именами (ids)
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (4, 5, 9),
], ids=["small numbers", "medium numbers"])
```

### Параметризация класса

Весь класс прогоняется с каждым набором параметров:

```python
@pytest.mark.parametrize("role", ["USER", "ADMIN", "SUPER_ADMIN"])
class TestRoleAccess:

    def test_get_movies(self, role, api_manager):
        # Запустится 3 раза
        ...

    def test_get_movie_by_id(self, role, api_manager):
        # Тоже 3 раза
        ...
```

### Комбинирование параметров класса и метода

```python
@pytest.mark.parametrize("location", ["MSK", "SPB"])
class TestMoviesByLocation:

    @pytest.mark.parametrize("published", [True, False])
    def test_filter_by_location_and_published(self, location, published, api_manager):
        # Запустится 4 раза: MSK+True, MSK+False, SPB+True, SPB+False
        params = {"locations": [location], "published": published}
        api_manager.movies.get_movies_list(params=params, expected_status=200)
```

### Пропуск отдельных комбинаций

```python
@pytest.mark.parametrize("feature,platform", [
    ("feature_a", "windows"),
    ("feature_a", "mac"),
    pytest.param("feature_b", "mac", marks=pytest.mark.skip(reason="Not supported")),
])
```

### Частые ошибки

| Ошибка | Правильно |
|--------|-----------|
| `"param1, param2"` (пробел) | `"param1,param2"` (без пробела) |
| `("a","b")` вместо списка | `[("a","b")]` |
| Разное кол-во параметров | Должно совпадать: `"a,b,c"` → `[(1,2,3)]` |

---

## 3. Аннотации типов

### Зачем нужны

Аннотации — это подсказки для программиста и IDE. Python **не проверяет** их на этапе выполнения, но IDE подсветит ошибку, если передать не тот тип.

```python
def add(a, b):      # Что такое a и b? Числа? Строки?
    return a + b

def add(a: int, b: int) -> int:   # Теперь ясно: числа → число
    return a + b
```

### Базовые аннотации

```python
def greet(name: str) -> str:
    return f"Привет, {name}!"

def is_adult(age: int) -> bool:
    return age >= 18

def process(data: dict) -> list:
    return list(data.values())
```

### Коллекции (Python 3.9+)

```python
def sum_numbers(numbers: list[int]) -> int:
    return sum(numbers)

def get_user_ids() -> list[int]:
    return [1, 2, 3]

def count_by_city(data: dict[str, int]) -> None:
    ...
```

Для Python 3.8 и ниже — импорт из `typing`:

```python
from typing import List, Dict, Tuple, Set

def sum_numbers(numbers: List[int]) -> int: ...
def user_info() -> Dict[str, int]: ...
def get_coords() -> Tuple[float, float]: ...
```

### Optional и Union

```python
from typing import Optional, Union

# Может вернуть строку или None
def find_user(user_id: int) -> Optional[str]:
    if user_id == 1:
        return "Найден"
    return None

# Аргумент может быть int или str
def process_value(value: Union[int, str]) -> str:
    return str(value)

# Альтернативная запись (Python 3.10+):
def find_user(user_id: int) -> str | None: ...
def process_value(value: int | str) -> str: ...
```

### Аннотации в классах

```python
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Привет, меня зовут {self.name}!"
```

### Аннотации в проекте (уже есть)

```python
# custom_requester/custom_requester.py
def send_request(
    self,
    method: str,
    endpoint: str,
    expected_status: int | None = 200,
    **kwargs,
) -> requests.Response:
    ...
```

### Что дают аннотации

1. **Автодополнение** в IDE — при вводе `user.` IDE покажет доступные методы
2. **Раннее обнаружение ошибок** — IDE подчеркнёт, если передать `str` вместо `int`
3. **Самодокументирование** — не нужно читать реализацию, чтобы понять, какие типы ожидаются

---

## 4. Хранение секретов (.env)

### Проблема

Сейчас креды жёстко зашиты в код:

```python
# conftest.py
admin_creds = {"email": "api1@gmail.com", "password": "asdqwe123Q"}
```

Если запушить в git — пароль утечёт в репозиторий.

### Решение

**Шаг 1.** Создать `.env` в корне проекта:

```
SUPER_ADMIN_USERNAME=api1@gmail.com
SUPER_ADMIN_PASSWORD=asdqwe123Q
```

**Шаг 2.** Создать `resources/user_creds.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env в os.environ

class SuperAdminCreds:
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")
```

**Шаг 3.** Добавить `.env` в `.gitignore`:

```
.env
```

**Шаг 4.** Использовать в фикстурах:

```python
@pytest.fixture
def super_admin(user_session):
    new_session = user_session()
    super_admin = User(
        SuperAdminCreds.USERNAME,
        SuperAdminCreds.PASSWORD,
        [Roles.SUPER_ADMIN.value],
        new_session
    )
    super_admin.api.auth_api.authenticate(super_admin.creds)
    return super_admin
```

### Преимущества

- **Безопасность** — пароли не попадают в git
- **Гибкость** — разные `.env` для локальной, тестовой и боевой среды
- **Простота** — библиотека `python-dotenv` уже в `requirements.txt`

---

## 5. Практические задания

### Задание 1. Ролевая модель

1. Создай модель `User` в `entities/user.py`
2. Создай `constants/roles.py` с Enum `Roles`
3. Создай `resources/user_creds.py` с `SuperAdminCreds`
4. Добавь фикстуры в `conftest.py`: `user_session`, `super_admin`, `common_user`
5. Добавь `close_session()` в `ApiManager`
6. Создай `UserApi` с методами `create_user` и `get_user`

### Задание 2. Параметризация

Напиши параметризованный тест для `GET /movies` с разными фильтрами:

```python
@pytest.mark.parametrize("location,expected_count", [
    ("MSK", None),    # не проверяем точное количество
    ("SPB", None),
    ("NONEXISTENT", 0),
], ids=["MSK location", "SPB location", "invalid location"])
def test_get_movies_filtered_by_location(super_admin, location, expected_count):
    response = super_admin.api.movies.get_movies_list(
        params={"locations": [location]},
        expected_status=200
    ).json()
    if expected_count is not None:
        assert len(response["movies"]) == expected_count
    for movie in response["movies"]:
        assert movie["location"] == location
```

### Задание 3. Аннотации

1. Открой `custom_requester.py` и добавь недостающие аннотации
2. В `data_generator.py` аннотируй возвращаемые типы → `-> dict`
3. Создай отдельный файл `annotations_practice.py` с примерами

### Задание 4. .env

1. Создай `.env` с кредами супер-админа
2. Добавь `.env` в `.gitignore`
3. Создай `resources/user_creds.py`
4. Обнови `conftest.py` — замени `admin_creds` на `SuperAdminCreds`