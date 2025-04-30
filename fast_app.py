import ssl
import undetected_chromedriver as uc
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import csv
from io import StringIO
from fastapi import Query
from fastapi.responses import StreamingResponse
import datetime
import uvicorn
import os
import config as CFG

# Fix for SSL certificate verification issues
ssl._create_default_https_context = ssl._create_unverified_context

# Path to your Chrome profile
# chrome_profile = r"/Users/ritikanand/Library/Application Support/Google/Chrome/Default"
chrome_profile = CFG.chrome_profile


class ProductInfo(BaseModel):
    product_id: str
    title: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[str] = None
    description: Optional[str] = None
    delivery_info: Optional[str] = None
    url: str

def setup_database():
    conn = sqlite3.connect('meesho_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT,
        title TEXT,
        price TEXT,
        rating TEXT,
        description TEXT,
        delivery_info TEXT,
        url TEXT,
        pincode TEXT,
        query TEXT,
        timestamp DATETIME
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
setup_database()



class MeeshoScraper:
    def __init__(self, pincode, chrome_profile_path):
        self.pincode = pincode
        self.chrome_profile_path = chrome_profile_path
        self.driver = None
        
    def setup_driver(self):
        """Set up undetected Chrome driver with your profile"""
        options = uc.ChromeOptions()
        
        options.add_argument(f"--user-data-dir={self.chrome_profile_path}")
        
        options.add_argument("--profile-directory=Default")
        
        # Additional options to avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Create the driver
        self.driver = uc.Chrome(
            options=options,
            version_main=CFG.chrome_version
        )
        
        self.driver.maximize_window()
        
        return self.driver
    
    def search_products(self, query, max_products=10):
        """Search for products and get details"""
        try:
            # Navigate to Meesho search
            search_url = f"https://www.meesho.com/search?q={query}"
            self.driver.get(search_url)
            
            time.sleep(3)
            
            product_elements = []
            
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            
            # Find product links that match the pattern
            product_links = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/p/') and not(contains(substring-after(@href, '/p/'), '/'))]"))
            )
            
            # Limit to max_products
            product_links = product_links[:max_products]
            
            products = []
            for link in product_links:
                try:
                    href = link.get_attribute("href")
                    product_id = href.split("/p/")[-1]
                    
                    
                    
                    products.append({
                        "product_id": product_id,
                        "url": href
                    })
                    
                except Exception as e:
                    print(f"Error extracting product info: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error in search_products: {e}")
            return []
    
    def check_delivery_date(self, product_url):
        """Check delivery date for a product"""
        data={
            "title": None,
            "price": None,
            "rating": None,
            "description": None,
            "delivery_info": None,
        }
        try:
            time.sleep(2)
            self.driver.get(product_url)

        # Get product title
            title_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'ShippingInfo__DetailCard')]/span"))
            )
            title = title_element.text if title_element else "No Title"
            data['title']=title
            
            # Get price if available
            try:
                price_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'ShippingInfo__PriceRow')]"))
            )
                price = price_element.text
            except:
                price = "Price not available"
            data['price']=price

            # Get product description if available
            try:
                description_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'ProductDescription__DetailsCardStyled')]"))
                )
                description = description_element.text
            except:
                description = "Description not available"
            data['description']=description
            
            # Get rating if available
            try:
                rating_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'CountWrapper__AverageRating')]"))
            )
                rating = rating_element.text
            except:
                rating = "No rating"
            data['rating']=rating



            try:
                # Wait for pincode input field to be available
                pincode_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//input[@id='pin']"))
                )
                
                ActionChains(self.driver).move_to_element(pincode_input).perform()
                time.sleep(0.3)
                
                pincode_input.clear()
                
                for digit in self.pincode:
                    pincode_input.send_keys(digit)
                    time.sleep(0.1)  # Small delay between keystrokes
                
                # Find and click check button
                check_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='CHECK']/ancestor::button"))
                )
                time.sleep(0.5)

                ActionChains(self.driver).move_to_element(check_btn).click().perform()
                
                # Wait for delivery info to load
                time.sleep(3)
                
                # Extract delivery date
                delivery_info = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[starts-with(normalize-space(), 'Delivery') and @color='greyBase']"))
                )
                delivery=delivery_info.text
            except:
                delivery='Not Available'
            data['delivery_info']=delivery

            
            
            
            return data
            
        except Exception as e:
            print(f"Error checking delivery date: {e}")
            return data

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

# Create FastAPI app
app = FastAPI(title="Meesho Product Scraper API")

@app.get("/search_product/", response_model=List[ProductInfo])
async def search_meesho(query: str = Query(..., description="Search query"), 
                        pincode: str = Query("209861", description="Delivery pincode",regex="^[0-9]{6}$", 
                        min_length=6,max_length=6),
                        max_products: int = Query(10, description="Maximum number of products to return",ge=1, le=10)):
    """
    Search Meesho for products and return details including delivery information
    """
    scraper = MeeshoScraper(
        pincode=pincode,
        chrome_profile_path=chrome_profile
    )
    
    try:
        # Set up driver
        scraper.setup_driver()
        
        # Search for products
        products = scraper.search_products(query, max_products)

        
        for product in products:
            additional_info = scraper.check_delivery_date(product["url"])
            product["delivery_info"] = additional_info["delivery_info"]
            product["description"] = additional_info["description"]
            product["title"] = additional_info["title"]
            product["rating"] = additional_info["rating"]
            product["price"] = additional_info["price"]

        conn = sqlite3.connect('meesho_data.db')
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now()
        
        for product in products:
            cursor.execute('''
            INSERT INTO products 
            (product_id, title, price, rating, description, delivery_info, url, pincode, query, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product["product_id"],
                product["title"],
                product["price"],
                product["rating"],
                product["description"],
                product["delivery_info"],
                product["url"],
                pincode,
                query,
                timestamp
            ))
        
        conn.commit()
        conn.close()
            
        
        return products
    
    finally:
        # Always close the browser
        scraper.close()

@app.get("/setup-login/")
async def setup_login(phone_number: str = Query(..., description="Phone number for Meesho login")):
    """
    Opens a browser for user to login to Meesho manually with OTP.
    The user should complete the login process, then close the browser.
    After this setup, the search API will work with the authenticated session.
    """
    scraper = None
    try:
        # Initialize scraper without providing pincode as it's not needed for login
        scraper = MeeshoScraper(
            pincode="",
            chrome_profile_path=chrome_profile
        )
        
        scraper.setup_driver()
        
        # Navigate to Meesho login page
        login_url = "https://www.meesho.com/auth?redirect=https%3A%2F%2Fwww.meesho.com%2F"
        scraper.driver.get(login_url)
        
        # Wait for phone number input field
        phone_input = WebDriverWait(scraper.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='tel']"))
        )
        
        # Enter phone number
        phone_input.clear()
        for digit in phone_number:
            phone_input.send_keys(digit)
            time.sleep(0.1)
        
        # Click continue button
        continue_btn = scraper.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        continue_btn.click()
        
        # Display instructions for the user
        print("OTP sent to your phone. Please enter it in the browser window.")
        print("After successful login, the browser will stay open for 60 seconds.")
        print("Your session will be automatically saved for future API requests.")
        
        # Start time to track how long we've been waiting
        start_time = time.time()
        logged_in = False
        
        # Check for URL change to verify login completion
        # Keep checking for up to 60 seconds
        while time.time() - start_time < 60:
            current_url = scraper.driver.current_url
            
            # Check if URL has changed to homepage (indicating successful login)
            if current_url == "https://www.meesho.com/" or current_url.endswith("meesho.com/"):
                logged_in = True
                # Wait a bit more to ensure cookies are saved
                time.sleep(5)
                break
                
            # Short pause between checks
            time.sleep(2)
        
        if logged_in:
            return {"status": "success", "message": "Login successful. Your session has been saved."}
        else:
            return {"status": "warning", "message": "Login may not have completed. Please try again if search results don't show delivery information."}
        
    except Exception as e:
        if 'id' in scraper.driver.current_url:
            return {"status": "success", "message": f"User Already Logged in you can use search api seamlessly."}

        return {"status": "error", "message": f"Error during login setup: {str(e)}"}
    
    finally:
        # Close the browser after login is complete
        if scraper and scraper.driver:
            scraper.close()


@app.get("/download-csv/")
async def download_csv(rows: int = Query(100, description="Number of recent rows to download", ge=1)):
    """
    Download the most recent scraped data as a CSV file
    """
    try:
        # Connect to the database
        conn = sqlite3.connect('meesho_data.db')
        cursor = conn.cursor()
        
        # Get the most recent rows
        cursor.execute('''
        SELECT product_id, title, price, rating, description, delivery_info, url, pincode, query, timestamp
        FROM products
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (rows,))
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return {"status": "error", "message": "No data available to download"}
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Product ID", "Title", "Price", "Rating", "Description", 
            "Delivery Info", "URL", "Pincode", "Search Query", "Timestamp"
        ])
        
        # Write data rows
        for row in data:
            writer.writerow(row)
        
        # Prepare response
        output.seek(0)
        
        # Generate filename with current date
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meesho_data_{date_str}.csv"
        
        # Return CSV as downloadable file
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
        
    except Exception as e:
        return {"status": "error", "message": f"Error generating CSV: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("fast_app:app", host="0.0.0.0", port=8000, reload=True)