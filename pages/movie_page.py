from pages.base_page import BasePage


class CinescopeMoviePage(BasePage):
    def __init__(self, page):
        super().__init__(page)

        self.review_input = '[data-qa-id="movie_review_input"]'
        self.review_submit_button = '[data-qa-id="movie_review_submit_button"]'

    def open_movie(self, movie_id: int):
        self.open_url(f"{self.home_url}movies/{movie_id}")

    def open_first_movie(self):
        """Открыть первую доступную страницу фильма через 'Все фильмы'."""
        self.open_all_movies()
        self.page.locator('[data-qa-id="more_button"]').first.click()

    def leave_review(self, text: str, rating: str):
        self.enter_text(self.review_input, text)
        self.select_rating(rating)
        self.click(self.review_submit_button)

    def select_rating(self, rating: str):
        """Выбрать оценку в кастомном рейтинге (combobox + option)."""
        self.page.get_by_role("combobox").click()
        self.page.get_by_role("option", name=rating, exact=True).click()