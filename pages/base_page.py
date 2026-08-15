from pages.actions import PageAction


class BasePage(PageAction):
    """Логика и локаторы, общие для всех страниц сайта."""

    def __init__(self, page):
        super().__init__(page)
        self.home_url = "https://dev-cinescope.coconutqa.ru/"
        self.all_movies_link = 'a[href="/movies"]'
        self.login_page_button = '[data-qa-id="login_page_button"]'

    def go_to_all_movies(self):
        self.click(self.all_movies_link)

    def open_all_movies(self):
        self.open_url(f"{self.home_url}movies")