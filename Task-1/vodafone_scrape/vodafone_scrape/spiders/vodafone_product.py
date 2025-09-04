import scrapy
import csv
import os
from urllib.parse import urlparse
from scrapy_playwright.page import PageMethod


class VodafoneProductSpider(scrapy.Spider):
    name = "vodafone_products"

    def start_requests(self):
        # Read first 5 product URLs from CSV
        with open("product_urls.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            urls = [row["url"] for row in reader][:5]

        for url in urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,  # to get playwright_page in meta
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),

                        # Accept cookies
                        PageMethod(
                            "evaluate",
                            """() => {
                                const cookieBtn = document.querySelector("#onetrust-accept-btn-handler");
                                if (cookieBtn) cookieBtn.click();
                            }"""
                        ),
                        PageMethod("wait_for_timeout", 1500),

                        # Handle "Already with us?" modal
                        PageMethod(
                            "evaluate",
                            """() => {
                                const newCustBtn = document.querySelector("button[data-testid='newOrExisting-cta-new']");
                                if (newCustBtn) newCustBtn.click();
                            }"""
                        ),
                        PageMethod("wait_for_timeout", 2000),
                    ],
                    "screenshot_path": self.get_folder_name(url),
                },
                callback=self.parse_product,
            )

    def get_folder_name(self, url):
        """Extract clean folder name based on product model from URL"""
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        model_name = " ".join(p.capitalize() for p in parts[-2:])  # e.g. "Apple Iphone-13"
        base_dir = os.path.join("Vodafone UK", model_name.replace("-", " "))
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    async def parse_product(self, response):
        page = response.meta.get("playwright_page")
        if not page:
            self.logger.error("Playwright page not found in response.meta")
            return

        screenshot_path = response.meta["screenshot_path"]

        # --- Collect variant names ---
        try:
            await page.wait_for_selector("#selectedCapacity", timeout=5000)
            await page.click("#selectedCapacity")
            await page.wait_for_timeout(1000)

            variant_elements = await page.query_selector_all("ul[role='listbox'] li")
            variant_texts = [await el.inner_text() for el in variant_elements]
        except Exception as e:
            self.logger.error(f"No variants found for {response.url} → {e}")
            await page.close()
            return

        # --- Loop over variants ---
        for variant in variant_texts:
            clean_variant = variant.strip().replace(" ", "")

            # Reopen dropdown each time
            await page.click("#selectedCapacity")
            await page.wait_for_timeout(500)

            # Select variant by text
            option = await page.query_selector(f"ul[role='listbox'] li:has-text('{variant}')")
            if option:
                await option.click()
                await page.wait_for_timeout(2000)

                # --- 1. PDP Screenshot (full page) ---
                await page.screenshot(
                    path=os.path.join(screenshot_path, f"PDP_{clean_variant}.png"),
                    full_page=True
                )
                self.logger.info(f"PDP screenshot saved for {clean_variant}")

                # --- 2. MSRP Screenshot (popup only) ---
                msrp_btn = await page.query_selector("button:has-text('Pay for your phone in one go')")
                if msrp_btn:
                    await msrp_btn.click()
                    await page.wait_for_timeout(2000)
                    await page.screenshot(
                        path=os.path.join(screenshot_path, f"MSRP_{clean_variant}.png"),
                        full_page=False
                    )
                    # Close popup
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(1000)
                    self.logger.info(f"MSRP screenshot saved for {clean_variant}")

                # --- 3. Phoneplan Screenshot ---
                build_btn = await page.query_selector("button:has-text('Build your own plan')")
                if build_btn:
                    await build_btn.click()
                    await page.wait_for_timeout(2000)

                    cont_btn = await page.query_selector("button:has-text('Continue without trade in')")
                    if cont_btn:
                        await cont_btn.click()
                        await page.wait_for_load_state("domcontentloaded")
                        await page.wait_for_timeout(3000)

                        await page.screenshot(
                            path=os.path.join(screenshot_path, f"Phoneplan_{clean_variant}.png"),
                            full_page=True
                        )
                        self.logger.info(f"Phoneplan screenshot saved for {clean_variant}")

                # --- 4. Airtime Screenshot ---
                continue_btn = await page.query_selector("button[data-selector='configurator-cta']")
                if continue_btn:
                    await continue_btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)

                    await page.screenshot(
                        path=os.path.join(screenshot_path, f"Airtime_{clean_variant}.png"),
                        full_page=True
                    )
                    self.logger.info(f"Airtime screenshot saved for {clean_variant}")

        await page.close()
