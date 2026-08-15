import allure
from playwright.sync_api import Page, expect


class PageAction:
    """Низкоуровневая обёртка над действиями Playwright (клик, ввод, ожидание)."""

    def __init__(self, page: Page):
        self.page = page

    @allure.step("Переход на страницу: {url}")
    def open_url(self, url: str):
        self.page.goto(url)

    @allure.step("Ввод текста в поле: {locator}")
    def enter_text(self, locator: str, text: str):
        self.page.fill(locator, text)

    @allure.step("Клик по элементу: {locator}")
    def click(self, locator: str):
        self.page.click(locator)

    @allure.step("Проверка видимости текста: {text}")
    def expect_text_visible(self, text: str):
        expect(self.page.get_by_text(text)).to_be_visible()

    @allure.step("Проверка редиректа на URL: {url}")
    def expect_url(self, url: str):
        self.page.wait_for_url(url)