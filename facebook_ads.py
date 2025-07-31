import scrapy
from scrapy_playwright.page import PageMethod
import urllib.parse

KEYWORDS = ["ebook gratis"]
COUNTRIES = ["United States"]

class FacebookAdsSpider(scrapy.Spider):
    name = "facebook_ads"
    custom_settings = {
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": False},
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
    }

    def start_requests(self):
        for country in COUNTRIES:
            for kw in KEYWORDS:
                q = urllib.parse.quote(kw)
                url = (
                    "https://www.facebook.com/ads/library/"
                    f"?active_status=all&ad_type=all&country={urllib.parse.quote(country)}&q={q}"
                )
                yield scrapy.Request(
                    url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_timeout", 5000),
                            PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                            PageMethod("wait_for_timeout", 3000),
                        ],
                        "keyword": kw,
                        "country": country,
                    },
                    callback=self.parse_listing,
                )

    async def parse_listing(self, response):
        keyword = response.meta["keyword"]
        country = response.meta["country"]
        page = response.meta["playwright_page"]

        for _ in range(3):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

        cards = await page.query_selector_all("div[role='article']")
        for card in cards[:5]:
            try:
                ad_copy = await card.inner_text()
                landing = None
                link_handle = await card.query_selector("a[href]")
                if link_handle:
                    href = await link_handle.get_attribute("href")
                    if href and href.startswith("http") and "facebook.com" not in href:
                        landing = href
                yield {
                    "keyword": keyword,
                    "country": country,
                    "ad_copy": ad_copy.strip().replace("\n", " "),
                    "landing_url": landing,
                }
            except Exception:
                continue
