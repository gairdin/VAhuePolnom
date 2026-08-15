import time

import allure
import pytest

from pages.login_page import CinescopeLoginPage
from pages.movie_page import CinescopeMoviePage
from pages.register_page import CinescopeRegisterPage
from utils.data_generator import generate_user_data


@allure.epic("Тестирование UI")
@allure.feature("Отзывы под фильмом")
@allure.story("Оставление отзыва")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
class TestReview:

    @allure.title("Оставление отзыва под фильмом зарегистрированным пользователем")
    def test_leave_review_under_movie(
        self,
        page,
        db_client,
        register_page: CinescopeRegisterPage,
    ):
        login_page = CinescopeLoginPage(page)
        movie_page = CinescopeMoviePage(page)

        user_data = generate_user_data()
        review_text = f"Отличный фильм, очень понравился {int(time.time())}"

        with allure.step("Зарегистрировать нового пользователя через UI"):
            register_page.register(
                user_data["fullName"],
                user_data["email"],
                user_data["password"],
            )
            register_page.expect_url("https://dev-cinescope.coconutqa.ru/login")
            register_page.expect_text_visible("Подтвердите свою почту")

        with allure.step("Подтвердить email пользователя в БД"):
            db_client.conn.cursor().execute(
                "UPDATE users SET verified = TRUE WHERE email = %s",
                (user_data["email"],),
            )
            db_client.conn.commit()
            verified = db_client.fetch_one(
                "SELECT verified FROM users WHERE email = %s",
                (user_data["email"],),
            )
            assert verified and verified[0], "Пользователь не подтверждён в БД"

        with allure.step("Залогиниться под созданным пользователем"):
            login_page.open()
            login_page.login(user_data["email"], user_data["password"])
            login_page.open_all_movies()
            login_page.expect_text_visible("Профиль")

        with allure.step("Открыть страницу фильма"):
            movie_page.open_first_movie()

        with allure.step("Оставить отзыв под фильмом"):
            movie_page.leave_review(review_text, "4")

        with allure.step("Проверить, что отзыв успешно создан"):
            movie_page.expect_text_visible("Отзыв успешно создан")
            movie_page.expect_text_visible(review_text)