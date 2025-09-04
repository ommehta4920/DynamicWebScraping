import scrapy
import csv
import os
import re
from urllib.parse import urlparse
from scrapy_playwright.page import PageMethod


class TMobileProductSpider(scrapy.Spider):
    name = "tmobile_products"

    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
        "CONCURRENT_REQUESTS": 1,
        "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 1,
    }

    def start_requests(self):
        # Load product URLs from CSV
        with open("tmobile_product_urls.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            urls = [row["url"] for row in reader]

        for url in urls[:1]:  # limit to first product for testing
            yield scrapy.Request(
                url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,  # gives access to playwright_page
                    playwright_page_methods=[
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("set_viewport_size", {"width": 1280, "height": 2000}),
                    ],
                ),
                callback=self.parse_product,
            )

    async def parse_product(self, response):
        page = response.meta["playwright_page"]

        # --- Helpers ---
        async def safe_click(sel):
            """Click element if it exists, ignore if missing."""
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=1000)
                    await page.wait_for_timeout(500)
                    return True
            except Exception:
                return False
            return False

        async def force_click(sel):
            """Try normal click, fallback to JS click (bypasses overlays)."""
            try:
                await page.click(sel, timeout=1000)
            except Exception:
                await page.evaluate(f"""
                    const el = document.querySelector("{sel}");
                    if (el) el.click();
                """)

        # --- Handle random popups gracefully ---
        await safe_click("#onetrust-accept-btn-handler")   # Cookies
        await safe_click("[data-testid='_15gifts-engagement-bubble-button-secondary']")  # Compare popup
        await safe_click(".op-block-class")  # Notifications

        # --- Get product title ---
        # --- Extract brand from URL ---
        url_path = urlparse(response.url).path  # /cell-phone/apple-iphone-14
        parts = url_path.strip("/").split("/")
        brand_slug = parts[-1].split("-")[0] if len(parts) > 1 else ""
        brand = brand_slug.capitalize()  # Apple, Samsung, Google etc.

        # --- Extract product name from <h1> ---
        try:
            product_name = await page.inner_text("h1")
        except Exception:
            product_name = parts[-1].replace("-", " ").title()

        # --- Combine brand + product ---
        full_name = f"{brand} {product_name}".strip()

        # --- Folder and file-safe versions ---
        folder_title = re.sub(r"[^a-zA-Z0-9 ]+", "", full_name).strip()
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", full_name).strip("_")

        # --- Base dir ---
        base_dir = os.path.join("T-Mobile US", folder_title)
        os.makedirs(base_dir, exist_ok=True)

        # --- Find best color (with max variants) ---
        colors = await page.eval_on_selector_all(
            ".upf-skuSelector__group--color input[type=radio]",
            "els => els.map(e => e.value)"
        )

        best_color = None
        max_variants = 0
        for color in colors:
            await force_click(f"input[value='{color}']")
            await page.wait_for_timeout(2000)

            variants = await page.eval_on_selector_all(
                ".upf-skuSelector__group--storage input[type=radio]",
                "els => els.map(e => e.value)"
            )
            if len(variants) > max_variants:
                best_color = color
                max_variants = len(variants)

        if best_color:
            await force_click(f"input[value='{best_color}']")
            await page.wait_for_timeout(500)

        # --- Screenshot each variant (always take at least one) ---
        variants = await page.eval_on_selector_all(
            ".upf-skuSelector__group--storage input[type=radio]",
            "els => els.map(e => e.value)"
        )

        for var in variants:
            await force_click(f"input[value='{var}']")
            await page.wait_for_timeout(2000)

            clean_variant = re.sub(r"[^a-zA-Z0-9]+", "_", var).strip("_")

            # --- Always save base variant screenshot ---
            variant_file = os.path.join(base_dir, f"{folder_title}_{clean_variant}.png")
            await page.screenshot(path=variant_file, full_page=True)
            self.logger.info(f"Variant screenshot saved: {variant_file}")

            # --- Optional: Airtime flow if continue button exists ---
            continue_btn = await page.query_selector("button[data-selector='configurator-cta']")
            if continue_btn:
                await continue_btn.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(3000)

                airtime_file = os.path.join(base_dir, f"{folder_title}_{clean_variant}_airtime.png")
                await page.screenshot(path=airtime_file, full_page=True)
                self.logger.info(f"Airtime screenshot saved: {airtime_file}")

        # --- Handle promotions (with Airtime flow) ---
        promo_btn = await page.query_selector(".upf-productCard__promo--action")
        if promo_btn:
            await promo_btn.click()
            await page.wait_for_timeout(3000)
            
            # --- Screenshot promo modal with all offers ---
            promo_file = os.path.join(base_dir, f"{folder_title}_offer_promo.png")
            await page.screenshot(path=promo_file, full_page=True)
            self.logger.info(f"Promo list screenshot saved: {promo_file}")

            details = await page.query_selector_all("button.upf-productPromoDetails__card--btn")
            for i in range(len(details)):
                details = await page.query_selector_all("button.upf-productPromoDetails__card--btn")
                btn = details[i]
                await btn.click()
                await page.wait_for_timeout(2000)

                # --- Always screenshot the modal content ---
                offer_file = os.path.join(base_dir, f"{folder_title}_offer{i+1}.png")
                await page.screenshot(path=offer_file, full_page=True)
                self.logger.info(f"Promo modal screenshot saved: {offer_file}")

                # --- Optional: Airtime flow if continue button exists ---
                continue_btn = await page.query_selector("button[data-selector='configurator-cta']")
                if continue_btn:
                    await continue_btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)

                    airtime_file = os.path.join(base_dir, f"{folder_title}_offer{i+1}_airtime.png")
                    await page.screenshot(path=airtime_file, full_page=True)
                    self.logger.info(f"Airtime promo screenshot saved: {airtime_file}")

                # Go back (force click in case normal fails)
                await force_click("button.upf-productPromoDetails__card--back")
                await page.wait_for_timeout(1000)

            # Close promotions popup once after all offers
            await force_click("button.phx-modal__close")
            await page.wait_for_timeout(1000)

        # --- Cleanup ---
        await page.close()
