import scrapy
from scrapy_playwright.page import PageMethod
import csv
from urllib.parse import urljoin


class VodafoneListingSpider(scrapy.Spider):
    name = "vodafone_listing"
    start_urls = ["https://www.vodafone.co.uk/mobile/pay-monthly-contracts"]

    def start_requests(self):
        custom_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/116.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9",
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
                        PageMethod("set_viewport_size", {"width": 1280, "height": 2000}),
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
                                        let items = document.querySelectorAll("a[href*='/mobile/pay-monthly-contracts/']").length;
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
        
        # Save html code of the page
        # with open("listing_dump.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)

        # self.log(f"Saved raw HTML dump: listing_dump.html")
        
        
        base = "https://www.vodafone.co.uk"

        # Target only phone product links
        raw_hrefs = response.css("a[href*='/mobile/pay-monthly-contracts/']::attr(href)").getall()

        product_urls = set()
        for href in raw_hrefs:
            if not href:
                continue
            if "/mobile/pay-monthly-contracts/" in href and href.count("/") >= 4:
                full = urljoin(base, href)
                product_urls.add(full)

        product_list = sorted(product_urls)

        # Save to CSV
        with open("product_urls.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url"])
            for u in product_list:
                writer.writerow([u])

        self.log(f"Found {len(product_list)} product URLs (saved to product_urls.csv)")

        # Also yield for debugging
        for u in product_list:
            yield {"url": u}
