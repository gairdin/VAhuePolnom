from pages.base_page import BasePage


class CinescopeLoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = f"{self.home_url}login"

        self.email_input = '[data-qa-id="login_email_input"]'
        self.password_input = '[data-qa-id="login_password_input"]'
        self.submit_button = '[data-qa-id="login_submit_button"]'

    def open(self):
        self.open_url(self.url)

    def login(self, email: str, password: str):
        with self.page.expect_response(
            lambda r: "auth.dev-cinescope" in r.url and "/login" in r.url
        ):
            self.enter_text(self.email_input, email)
            self.enter_text(self.password_input, password)
            self.click(self.submit_button)