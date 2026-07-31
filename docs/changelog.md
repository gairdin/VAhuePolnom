# Документация внесённых изменений

## Содержание

1. [Ролевая модель](#1-ролевая-модель)
2. [Pydantic — валидация данных](#2-pydantic--валидация-данных)
3. [Что и зачем создано/изменено](#3-что-и-зачем-созданоизменено)
4. [Полный список файлов](#4-полный-список-файлов)

---

## 1. Ролевая модель

### 1.1. Проблема, которую решаем

**Было:** в каждом тесте приходилось вручную логиниться:

```python
def test_create_movie(api_manager, admin_creds, movie_data):
    api_manager.auth.authenticate(admin_creds)  # ← повторяется в каждом тесте
    api_manager.movies.create_movie(movie_data)
```

И не было разницы между «запрос от админа» и «запрос от обычного юзера» — просто разные креды.

**Стало:** тест указывает, кто делает запрос, и ничего больше:

```python
def test_create_movie(super_admin, movie_data):
    super_admin.api.movies.create_movie(movie_data)  # super_admin уже залогинен
```

### 1.2. Как это работает — цепочка компонентов

```
User ─────────────────> имеет api: ApiManager
  ├── email                         ├── .auth       (AuthAPI)
  ├── password                      ├── .movies     (MoviesAPI)
  ├── roles                         └── .user_api   (UserApi)
  └── .creds → (email, password)
```

#### Шаг 1. Класс User (`entities/user.py`)

Хранит данные пользователя и даёт доступ к API:

```python
class User:
    def __init__(self, email: str, password: str, roles: list, api: ApiManager):
        self.email = email
        self.password = password
        self.roles = roles
        self.api = api  # Через user.api можно делать запросы

    @property
    def creds(self):
        """Возвращает (email, password) для authenticate()."""
        return self.email, self.password
```

**Зачем `@property`?** Чтобы писать `user.creds` вместо `user.creds()`. Это не метод, а свойство — вызывается как атрибут.

#### Шаг 2. Enum ролей (`constants/roles.py`)

Список всех ролей, чтобы не ошибиться в названии:

```python
from enum import Enum

class Roles(Enum):
    USER = "USER"          # Roles.USER.value → "USER"
    ADMIN = "ADMIN"        # Roles.ADMIN.value → "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"  # Roles.SUPER_ADMIN.value → "SUPER_ADMIN"
```

**Почему Enum, а не просто строка?**
- `Roles.SUPER_ADMIN.value` — IDE подскажет варианты
- `"SUPER_ADMIN"` — можно опечататься: `"SUPER_ADMINN"` и не заметить
- Если роль переименуют — меняешь в одном месте

#### Шаг 3. Креды в `.env` и `resources/user_creds.py`

Чтобы пароли не хранились в коде и не утекали в git:

**`.env`:**
```
SUPER_ADMIN_USERNAME=api1@gmail.com
SUPER_ADMIN_PASSWORD=asdqwe123Q
```

**`resources/user_creds.py`:**
```python
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает .env в переменные окружения


class SuperAdminCreds:
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "api1@gmail.com")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "asdqwe123Q")
```

`os.getenv("ИМЯ", "значение_по_умолчанию")` — читает переменную из `.env`. Если файла нет — использует запасное значение.

`.env` добавлен в `.gitignore` — он не попадёт в репозиторий.

#### Шаг 4. UserApi (`clients/user_api.py`)

Клиент для работы с пользователями через API:

```python
class UserApi(CustomRequester):
    def __init__(self, session, base_url: str):
        super().__init__(base_url=base_url, session=session)

    def get_user(self, user_locator, expected_status=200):
        return self.send_request("GET", f"/user/{user_locator}", expected_status=expected_status)

    def create_user(self, user_data: dict, expected_status=201):
        return self.send_request("POST", "/user", json=user_data, expected_status=expected_status)
```

#### Шаг 5. Фикстуры (`conftest.py`)

**`user_session`** — фабрика сессий. Создаёт изолированные HTTP-сессии и автоматически закрывает их после теста:

```python
@pytest.fixture
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_session = ApiManager(session=session, auth_url=..., movies_url=...)
        user_pool.append(user_session)
        return user_session

    yield _create_user_session

    # После теста: закрыть все созданные сессии
    for user in user_pool:
        user.close_session()
```

**`super_admin`** — возвращает готового залогиненного супер-админа:

```python
@pytest.fixture
def super_admin(user_session):
    new_session = user_session()
    super_admin = User(
        SuperAdminCreds.USERNAME,      # "api1@gmail.com"
        SuperAdminCreds.PASSWORD,      # "asdqwe123Q"
        [Roles.SUPER_ADMIN.value],     # ["SUPER_ADMIN"]
        new_session
    )
    super_admin.api.auth.authenticate(super_admin.creds)  # логин + токен
    return super_admin
```

**`common_user`** — создаёт обычного юзера через API и логинит его:

```python
@pytest.fixture
def common_user(user_session, super_admin, creation_user_data):
    new_session = user_session()
    common_user = User(
        creation_user_data["email"],
        creation_user_data["password"],
        [Roles.USER.value],
        new_session
    )
    # super_admin создаёт этого юзера через API
    super_admin.api.user_api.create_user(creation_user_data)
    # сам юзер логинится
    common_user.api.auth.authenticate(common_user.creds)
    return common_user
```

**Почему `common_user` зависит от `super_admin`?** Потому что нового юзера может создать только админ (по сваггеру, `POST /user` доступен только SUPER_ADMIN).

#### Шаг 6. Примеры тестов с ролевой моделью

```python
class TestUser:

    # Админ создаёт юзера — проверяем, что всё ок
    def test_create_user(self, super_admin, creation_user_data):
        response = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)

        assert response.json().get("verified") is True

    # Обычный юзер не может получить данные другого юзера
    def test_get_user_by_id_forbidden_for_common_user(self, common_user):
        common_user.api.user_api.get_user(common_user.email, expected_status=403)
```

---

## 2. Pydantic — валидация данных

### 2.1. Что такое Pydantic простыми словами

**Pydantic** — это библиотека, которая проверяет, что данные соответствуют ожидаемой структуре.

**Пример из жизни:** ты заказываешь пиццу по телефону. Оператор записывает:
- Название: строка
- Количество: число
- Адрес: строка

Если ты скажешь «количество: много» — оператор не поймёт. Нужно число. Pydantic работает как этот оператор: проверяет, что данные правильного типа, и если нет — выбрасывает ошибку **до того, как ты начнёшь с этими данными работать**.

### 2.2. Как это выглядит в коде

**Без Pydantic** — ответ от API это просто словарь, и ты сам проверяешь каждое поле через `assert`:

```python
response = api_manager.movies.create_movie(movie_data).json()
# Вручную проверяем каждое поле:
assert response["name"] == movie_data["name"]
assert response["price"] == movie_data["price"]
assert response["location"] == movie_data["location"]
assert type(response["id"]) == int
```

Если API вернёт `price: "abc"` (строку вместо числа) — тест упадёт с непонятной ошибкой
внутри `assert`, а не при получении данных.

**С Pydantic** — ты описываешь структуру один раз, и он проверяет всё сам:

```python
from pydantic import BaseModel

# Описываем, как должен выглядеть фильм
class Movie(BaseModel):
    id: int           # обязательное целое число
    name: str         # обязательная строка
    price: int        # обязательное целое число
    location: str     # обязательная строка
    published: bool   # обязательное булево значение

# Pydantic сам проверит данные
movie = Movie(**response.json())
print(movie.name)   # обращаемся к полю через точку
```

**Что произойдёт, если API вернёт не те типы:**

| Ответ API | Что ожидает Pydantic | Результат |
|---|---|---|
| `price: "500"` (строка) | `price: int` | Pydantic **сам конвертирует** в `500` |
| `price: "abc"` (строка) | `price: int` | ❌ `ValidationError` — не может конвертировать |
| `id: null` | `id: int` | ❌ `ValidationError` — `null` не может быть `int` |
| `published: "true"` (строка) | `published: bool` | Pydantic **сам конвертирует** в `True` |

**Главное отличие:** ошибка возникает в момент создания объекта, а не где-то в середине теста. Ты сразу видишь, какое поле не прошло проверку.

### 2.3. Подробный разбор синтаксиса

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Movie(BaseModel):
    id: int = Field(..., gt=0)        # обязательное поле, должно быть > 0
    name: str = Field(..., min_length=1)  # обязательное, минимум 1 символ
    price: int = Field(..., ge=0)     # обязательное, price >= 0
    description: Optional[str] = None  # необязательное, может быть None
    location: str                     # обязательное
    published: bool                   # обязательное
    genreId: int                      # обязательное
    createdAt: Optional[datetime] = None  # Pydantic сам сконвертирует строку в datetime
    updatedAt: Optional[datetime] = None
```

**Разберём каждую часть:**

- `id: int` — поле `id` должно быть целым числом
- `Field(..., gt=0)` — валидатор:
  - `...` (Ellipsis) — поле **обязательно**, должно быть передано
  - `gt=0` — значение должно быть **greater than** (больше) 0
  - `ge=0` — **greater or equal** (больше или равно) 0
  - `min_length=1` — минимальная длина строки 1 символ
- `Optional[str]` — может быть строкой или `None` (необязательное поле)
- `= None` — значение по умолчанию, если поле не передано
- `datetime` — Pydantic умеет конвертировать строку `"2025-01-01T12:00:00Z"` в объект `datetime`

### 2.4. Что такое `**` (распаковка словаря)?

```python
data = {"name": "Inception", "price": 500}
movie = Movie(**data)
# Это то же самое, что:
movie = Movie(name="Inception", price=500)
```

Оператор `**` «распаковывает» словарь в именованные аргументы. Ключи словаря становятся именами параметров, значения — значениями параметров.

### 2.5. Model для Movie (`entities/movie.py`)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Movie(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    price: int = Field(..., ge=0)
    description: Optional[str] = None
    location: str
    published: bool
    genreId: int
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
```

**Что проверяется при создании `Movie(**response.json())`:**

1. `id` существует, это `int` и он больше 0
2. `name` существует, это непустая строка
3. `price` существует, это `int >= 0`
4. `description` — если есть, то строка; если нет — `None`
5. `location`, `published`, `genreId` — существуют и правильных типов
6. `createdAt`, `updatedAt` — если есть, конвертируются в `datetime`

Если хоть одна проверка не пройдена — Pydantic выбрасывает `ValidationError` с подробным описанием:

```
1 validation error for Movie
price
  Input should be a valid integer [type=int_condition, ...]
```

### 2.6. Model для UserResponse (`entities/user_response.py`)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: str = Field(..., min_length=1)
    email: str
    fullName: str
    roles: list[str]
    verified: bool
    banned: bool
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
```

Особенность: `roles: list[str]` — список строк. Pydantic проверит, что это именно список, и каждый элемент в нём — строка.

### 2.7. Как Pydantic используется в тестах

**Было (без Pydantic):**

```python
def test_create_and_get_movie(api_manager, admin_creds, movie_data):
    api_manager.auth.authenticate(admin_creds)

    create_res = api_manager.movies.create_movie(movie_data, expected_status=201)
    created_movie = create_res.json()  # ← просто словарь
    movie_id = created_movie["id"]

    get_res = api_manager.movies.get_movie_by_id(movie_id)
    movie_body = get_res.json()  # ← просто словарь

    # Вручную проверяем каждое поле
    assert movie_body["name"] == movie_data["name"]
    assert movie_body["price"] == movie_data["price"]
    assert movie_body["location"] == movie_data["location"]
```

**Стало (с Pydantic):**

```python
def test_create_and_get_movie(api_manager, admin_creds, movie_data):
    api_manager.auth.authenticate(admin_creds)

    create_res = api_manager.movies.create_movie(movie_data, expected_status=201)
    created_movie = Movie(**create_res.json())  # ← Pydantic проверил структуру
    movie_id = created_movie.id                 # ← обращаемся через . (точку)

    get_res = api_manager.movies.get_movie_by_id(movie_id)
    movie_body = Movie(**get_res.json())  # ← ещё одна проверка

    # Поля уже проверены Pydantic, остаётся только смысловая проверка
    assert movie_body.name == movie_data["name"]
    assert movie_body.price == movie_data["price"]
    assert movie_body.location == movie_data["location"]
```

**Разница:**

| Без Pydantic | С Pydantic |
|---|---|
| `response["id"]` — если `id` нет, ошибка в середине теста | `movie.id` — если `id` нет, ошибка сразу при создании `Movie()` |
| `response["price"]` — может быть строкой, тест не заметит | `movie.price` — Pydantic сконвертирует в `int` или упадёт |
| Нужно помнить все ключи словаря | IDE подсказывает поля через точку |
| Ошибка: `KeyError: 'id'` | Ошибка: `ValidationError: field required` (понятнее) |

### 2.8. Обращение к полям через точку

Когда ты создаёшь `movie = Movie(**data)`, Pydantic превращает словарь в объект, и к полям можно обращаться через точку:

```python
# Словарь — обращение через ["ключ"]
movie_dict["name"]
movie_dict["price"]

# Pydantic-объект — обращение через .поле
movie.name
movie.price
```

IDE (PyCharm) будет подсказывать доступные поля при вводе `movie.`.

---

## 3. Что и зачем создано/изменено

### 3.1. Новые файлы

| Файл | Назначение |
|---|---|
| `entities/user.py` | Класс `User` — модель пользователя (email, password, roles, api) |
| `entities/movie.py` | Pydantic-модель `Movie` — валидация ответов API для фильмов |
| `entities/user_response.py` | Pydantic-модель `UserResponse` — валидация ответов API для пользователей |
| `entities/__init__.py` | Пустой файл, чтобы папка `entities/` стала Python-пакетом |
| `constants/roles.py` | Enum `Roles` — список ролей (USER, ADMIN, SUPER_ADMIN) |
| `constants/__init__.py` | Пустой файл, чтобы папка `constants/` стала Python-пакетом |
| `resources/user_creds.py` | `SuperAdminCreds` — читает креды из `.env` |
| `resources/__init__.py` | Пустой файл, чтобы папка `resources/` стала Python-пакетом |
| `.env` | Файл с секретными данными (не попадает в git) |
| `.gitignore` | Список файлов, игнорируемых git (`.env` добавлен) |
| `clients/user_api.py` | `UserApi` — клиент для `GET /user` и `POST /user` |
| `tests/api/test_user.py` | Тесты для UserApi |

### 3.2. Изменённые файлы

| Файл | Что изменено |
|---|---|
| `clients/api_manager.py` | Добавлен `user_api` (экземпляр `UserApi`) и метод `close_session()` |
| `conftest.py` | Добавлены фикстуры: `user_session`, `test_user`, `creation_user_data`, `super_admin`, `common_user` |
| `tests/api/test_movies.py` | 3 теста обновлены: используют `Movie(**response.json())` вместо сырых словарей |

### 3.3. Структура проекта после изменений

```
VAhuePolnom/
├── clients/
│   ├── api_manager.py        ← добавлен user_api + close_session
│   ├── auth_api.py
│   ├── movies_api.py
│   └── user_api.py           ← НОВЫЙ
├── constants/
│   ├── __init__.py            ← НОВЫЙ
│   └── roles.py              ← НОВЫЙ
├── custom_requester/
│   └── custom_requester.py
├── docs/
│   ├── fixtures_explanation.txt
│   └── role_model_guide.md
├── entities/
│   ├── __init__.py            ← НОВЫЙ
│   ├── movie.py              ← НОВЫЙ (Pydantic)
│   ├── user.py               ← НОВЫЙ
│   └── user_response.py      ← НОВЫЙ (Pydantic)
├── enums/
│   └── hosts.py
├── resources/
│   ├── __init__.py            ← НОВЫЙ
│   └── user_creds.py         ← НОВЫЙ
├── tests/
│   └── api/
│       ├── test_auth_api.py
│       ├── test_movies.py    ← изменён (Pydantic)
│       └── test_user.py      ← НОВЫЙ
├── utils/
│   └── data_generator.py
├── гайды/
│   └── гайд 1/
├── .env                       ← НОВЫЙ
├── .gitignore                 ← НОВЫЙ
├── conftest.py                ← изменён (новые фикстуры)
├── pytest.ini
├── requirements.txt           ← добавлен pydantic
```

---

## 4. Полный список файлов

### entities/user.py
```python
from clients.api_manager import ApiManager


class User:
    def __init__(self, email: str, password: str, roles: list, api: ApiManager):
        self.email = email
        self.password = password
        self.roles = roles
        self.api = api

    @property
    def creds(self):
        return self.email, self.password
```

### entities/movie.py
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Movie(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    price: int = Field(..., ge=0)
    description: Optional[str] = None
    location: str
    published: bool
    genreId: int
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
```

### entities/user_response.py
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    id: str = Field(..., min_length=1)
    email: str
    fullName: str
    roles: list[str]
    verified: bool
    banned: bool
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
```

### constants/roles.py
```python
from enum import Enum


class Roles(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
```

### resources/user_creds.py
```python
import os
from dotenv import load_dotenv

load_dotenv()


class SuperAdminCreds:
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "api1@gmail.com")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "asdqwe123Q")
```

### .env
```
SUPER_ADMIN_USERNAME=api1@gmail.com
SUPER_ADMIN_PASSWORD=asdqwe123Q
```

### .gitignore
```
.env
```

### clients/user_api.py
```python
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
```

### clients/api_manager.py (изменён)
```python
from clients.auth_api import AuthAPI
from clients.movies_api import MoviesAPI
from clients.user_api import UserApi


class ApiManager:
    def __init__(self, session, auth_url: str, movies_url: str):
        self.session = session
        self.auth = AuthAPI(session=session, base_url=auth_url)
        self.movies = MoviesAPI(session=session, base_url=movies_url)
        self.user_api = UserApi(session=session, base_url=auth_url)

    def close_session(self):
        self.session.close()
```

### conftest.py (новые фикстуры)
```python
# Импорты добавлены в начало файла:
from entities.user import User
from constants.roles import Roles
from resources.user_creds import SuperAdminCreds

# --- Новые фикстуры в конце файла ---

@pytest.fixture
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_session = ApiManager(session=session, auth_url=Hosts.AUTH.value, movies_url=Hosts.MOVIES.value)
        user_pool.append(user_session)
        return user_session

    yield _create_user_session

    for user in user_pool:
        user.close_session()


@pytest.fixture
def test_user():
    data = generate_user_data()
    data["roles"] = [Roles.USER.value]
    return data


@pytest.fixture
def creation_user_data(test_user):
    updated_data = test_user.copy()
    updated_data.update({
        "verified": True,
        "banned": False
    })
    return updated_data


@pytest.fixture
def super_admin(user_session):
    new_session = user_session()
    super_admin = User(
        SuperAdminCreds.USERNAME,
        SuperAdminCreds.PASSWORD,
        [Roles.SUPER_ADMIN.value],
        new_session
    )
    super_admin.api.auth.authenticate(super_admin.creds)
    return super_admin


@pytest.fixture
def common_user(user_session, super_admin, creation_user_data):
    new_session = user_session()
    common_user = User(
        creation_user_data["email"],
        creation_user_data["password"],
        [Roles.USER.value],
        new_session
    )
    super_admin.api.user_api.create_user(creation_user_data)
    common_user.api.auth.authenticate(common_user.creds)
    return common_user
```

### tests/api/test_user.py (новый файл)
```python
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
```