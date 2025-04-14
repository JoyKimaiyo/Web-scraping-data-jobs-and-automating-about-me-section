# scrapers/linkedin_login.py
import asyncio
from playwright.async_api import async_playwright
import os

COOKIE_PATH = 'config/linkedin_cookies.json'

async def save_cookies():
    os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)  # Ensure directory exists

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Open real browser
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")

        print("⚠️ Please log in manually, then press ENTER here...")
        input()

        # Save cookies
        cookies = await context.storage_state(path=COOKIE_PATH)
        await browser.close()
        print("✅ Cookies saved!")

if __name__ == "__main__":
    asyncio.run(save_cookies())
