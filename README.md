# Dynamic Web Scraping with Scrapy + Playwright

This project demonstrates **dynamic web scraping** using **Scrapy** and **Playwright** to extract product details and capture screenshots from **Vodafone UK** and **T-Mobile US** websites.  

It contains **two tasks**:  

- **Task-1:** Vodafone UK (Phones listing & screenshots)  
- **Task-2:** T-Mobile US (Phones listing, variants & promotions)  

Both tasks ensure **dynamic rendering**, **multiple variant handling**, and **organized output**.  

---

## ⚙️ Tech Stack
- **Python 3.9+**
- **Scrapy**
- **Playwright**
- **Pandas / CSV handling**
- **JavaScript execution support in Playwright**

---

## Project Structure

```bash
DynamicWebScraping/
├── requirements.txt # Project dependencies
├── README.md # Project overview
│
├── Task-1/
│ ├── Sample/ # Sample screenshots
│ ├── Vodafone UK/ # Captured screenshots (output)
│ ├── vodafone_scrape/ # Scrapy project for Vodafone UK
│ ├── product_urls.csv # Extracted product URLs
│ └── Task - vodafone.txt # Task instructions
│
└── Task-2/
├── Sample/ # Sample screenshots
├── T-Mobile US/ # Captured screenshots (output)
├── TMobile/ # Scrapy project for T-Mobile US
├── tmobile_product_urls.csv # Extracted product URLs
└── Task - tmobile.txt # Task instructions
```
---

## 📝 Task Details

### ✅ Task-1: Vodafone UK  
📌 **Listing Page:**  
`https://www.vodafone.co.uk/mobile/phones/pay-monthly-contracts`

1. **Fetch all product URLs** from the listing page → Save in `product_urls.csv`.  
2. **Iterate over first 5 URLs** and for each product:  
   - Create a folder named after the product.  
   - For **each variant (e.g., 128GB, 256GB):**  
     - `PDP_{variant}.png` → Product detail page screenshot.  
     - `MSRP_{variant}.png` → Screenshot after selecting **Pay full price**.  
     - `Phoneplan_{variant}.png` → After **Build Your Phone Plan → Continue without Trade-in**.  
     - `Airtime_{variant}.png` → After selecting **Continue**.  
3. **Maintain hierarchy:**
Vodafone UK > {Model Name} > {Screenshots}
4. **Use dynamic locators (XPath/CSS selectors)** → Avoid hardcoding.  
5. **Full-page screenshots** (as shown in `Sample/`).  

---

### ✅ Task-2: T-Mobile US  
📌 **Listing Page:**  
`https://www.t-mobile.com/cell-phones`

1. **Fetch all product URLs** → Save in `tmobile_product_urls.csv`.  
2. **Iterate over first 5 URLs** and for each product:  
- Create a folder named after the product.  
- **Select color with max variants.**  
- For each variant → Take screenshot as `{VariantName}.png`.  
- **Promotions (if available):**  
  - `offer_promo.png` → Promotions popup screenshot.  
  - `offers{i}.png` → Each promo details expanded.  
3. **Maintain hierarchy:**
T-Mobile US > {Model Name} > {Screenshots}
4. Follow **sample outputs** in `Sample/`.  

---

## ▶️ Installation & Setup

1. Clone this repo:
```bash
git clone https://github.com/yourusername/DynamicWebScraping.git
cd DynamicWebScraping
```
2. Install dependencies from requirements.txt:
```bash
pip install -r requirements.txt
```
3. Install Playwright browsers:
```bash
playwright install
```

---

## Running the Spiders

After installing dependencies and Playwright browsers, you can run the spiders for each task.

---

### Task-1 (Vodafone UK)

Run the spider to scrape product URLs:
```bash
cd Task-1/vodafone_scrape
scrapy crawl vodafone_spider
```
and to take screenshots:
```bash
cd Task-1/vodafone_scrape
scrapy crawl vodafone_product
```

### Task-2 (T-Mobile US)

Run the spider to scrape product URLs:
```bash
cd Task-2/tMobile
scrapy crawl tmobile_list
```
and to take screenshots:
```bash
cd Task-2/tMobile
scrapy crawl tmobile_products
```

---

## Check Sample Output
```bash
Task-1
└──Vodafone UK/
    └── iPhone 15/
        ├── PDP_128GB.png
        ├── MSRP_128GB.png
        ├── Phoneplan_128GB.png
        └── Airtime_128GB.png
 ```
```bash       
Task-2
└── T-Mobile US/
     └── Samsung Galaxy S23/
          ├── 128GB.png
          ├── 256GB.png
          ├── offer_promo.png
          ├── offers1.png
          ├── offers2.png
          └── ...
```
