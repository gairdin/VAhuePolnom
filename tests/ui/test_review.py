import time

import allure
import pytest

from pages.login_page import CinescopeLoginPage
from pages.movie_page import CinescopeMoviePage


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
        registered_user,
        created_movie_with_cleanup,
        login_page: CinescopeLoginPage,
        movie_page: CinescopeMoviePage,
    ):
        review_text = f"Отличный фильм, очень понравился {int(time.time())}"

        with allure.step("Зарегистрировать нового пользователя через API"):
            email = registered_user["email"]
            password = registered_user["password"]

        with allure.step("Подтвердить email пользователя в БД"):
            db_client.verify_user(email)

        with allure.step("Залогиниться под созданным пользователем"):
            login_page.open()
            login_page.login(email, password)
            login_page.open_all_movies()
            login_page.expect_text_visible("Профиль")

        with allure.step("Открыть страницу фильма"):
            movie_page.open_movie(created_movie_with_cleanup.id)

        with allure.step("Оставить отзыв под фильмом"):
            movie_page.leave_review(review_text, "4")

        with allure.step("Проверить, что отзыв успешно создан"):
            movie_page.expect_text_visible("Отзыв успешно создан")
            movie_page.expect_text_visible(review_text)