import scrapy
from scrapy_playwright.page import PageMethod
import csv
from urllib.parse import urljoin


class TMobileListingSpider(scrapy.Spider):
    name = "tmobile_listing"
    start_urls = ["https://www.t-mobile.com/cell-phones"]

    def start_requests(self):
        custom_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                headers=custom_headers,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),

                        # Accept cookie banner if present
                        PageMethod(
                            "evaluate",
                            """() => {
                                const btn = document.querySelector("#onetrust-accept-btn-handler");
                                if (btn) btn.click();
                            }"""
                        ),

                        # Expand viewport
                        PageMethod("set_viewport_size", {"width": 1280, "height": 2000}),

                        # Infinite scroll until no new items
                        PageMethod(
                            "evaluate",
                            """() => {
                                const delay = ms => new Promise(res => setTimeout(res, ms));
                                return (async () => {
                                    let prevCount = 0;
                                    let sameCount = 0;
                                    while (sameCount < 3) {
                                        window.scrollBy(0, window.innerHeight);
                                        await delay(2000);
                                        let items = document.querySelectorAll("a[itemprop='url']").length;
                                        if (items === prevCount) {
                                            sameCount++;
                                        } else {
                                            prevCount = items;
                                            sameCount = 0;
                                        }
                                    }
                                })();
                            }"""
                        ),
                        PageMethod("wait_for_timeout", 2000),
                    ],
                },
            )

    async def parse(self, response):

        base = "https://www.t-mobile.com"

        # Extract product URLs
        raw_hrefs = response.css("a[itemprop='url']::attr(href)").getall()

        product_urls = set()
        for href in raw_hrefs:
            if not href:
                continue
            if href.startswith("/cell-phone/"):
                full = urljoin(base, href)
                product_urls.add(full)

        product_list = sorted(product_urls)

        # Save to CSV
        with open("tmobile_product_urls.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url"])
            for u in product_list:
                writer.writerow([u])

        self.log(f"Found {len(product_list)} product URLs (saved to tmobile_product_urls.csv)")

        # Also yield for debugging
        for u in product_list:
            yield {"url": u}
