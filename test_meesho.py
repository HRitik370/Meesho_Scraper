import ssl
import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import random

# Fix for SSL certificate verification issues
ssl._create_default_https_context = ssl._create_unverified_context

# Path to your Chrome profile - make sure to replace YourUsername with your actual username
chrome_profile = r"/Users/ritikanand/Library/Application Support/Google/Chrome/Default"  # Updated with your actual username

class MeeshoScraper:
    def __init__(self, pincode, chrome_profile_path):
        self.pincode = pincode
        self.chrome_profile_path = chrome_profile_path
        self.driver = None
        
    def setup_driver(self):
        """Set up undetected Chrome driver with your profile"""
        options = uc.ChromeOptions()
        
        options.add_argument(f"--user-data-dir={self.chrome_profile_path}")
        
        options.add_argument("--profile-directory=Default")  # Adjust if needed
        
        # Additional options to avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = uc.Chrome(options=options,
                    version_main=135  # Specify your Chrome version here
)
        
        # Optional: Maximize window to make things more visible
        self.driver.maximize_window()
        
        return self.driver
    
    def scroll_to_element(self, element_locator, max_scrolls=10):
        """
        Scroll until the element is visible
        
        Args:
            element_locator: tuple of (By.X, "locator_string")
            max_scrolls: maximum number of scroll attempts
        
        Returns:
            The found element or None if not found
        """
        scroll_attempts = 0
        
        # First check if the element is already visible
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(element_locator)
            )
            return element
        except:
            pass
        
        # If not visible, start scrolling
        while scroll_attempts < max_scrolls:
            # Scroll down with a random amount to appear more human-like
            scroll_amount = random.randint(300, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            # Add a small random delay between scrolls
            time.sleep(random.uniform(0.5, 1.5))
            
            try:
                # Check if element is now visible
                element = WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located(element_locator)
                )
                # Found the element, return it
                return element
            except:
                # Element not found, continue scrolling
                scroll_attempts += 1
        
        # One last attempt with a longer wait time
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(element_locator)
            )
        except:
            print(f"Element {element_locator} not found after {max_scrolls} scroll attempts")
            return None
    
    def scroll_to_element_smooth(self, element_locator, max_scrolls=10):
        """
        Scroll smoothly until the element is visible, more human-like
        
        Args:
            element_locator: tuple of (By.X, "locator_string")
            max_scrolls: maximum number of scroll attempts
        
        Returns:
            The found element or None if not found
        """
        scroll_attempts = 0
        
        # First check if the element is already visible
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(element_locator)
            )
            return element
        except:
            pass
        
        # If not visible, start scrolling
        actions = ActionChains(self.driver)
        
        while scroll_attempts < max_scrolls:
            # Press and release Page Down key
            actions.send_keys(Keys.PAGE_DOWN).perform()
            
            # Add a small random delay between scrolls
            time.sleep(random.uniform(0.7, 1.8))
            
            try:
                # Check if element is now visible
                element = WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located(element_locator)
                )
                # Found the element, return it
                return element
            except:
                # Element not found, continue scrolling
                scroll_attempts += 1
                
                # Every few scrolls, scroll a bit back up to appear more natural
                if scroll_attempts % 3 == 0:
                    actions.send_keys(Keys.PAGE_UP).perform()
                    time.sleep(random.uniform(0.5, 1.0))
                    actions.send_keys(Keys.PAGE_DOWN).perform()
                    time.sleep(random.uniform(0.5, 1.0))
        
        # One last attempt with a longer wait time
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(element_locator)
            )
        except:
            print(f"Element {element_locator} not found after {max_scrolls} scroll attempts")
            return None
    
    def check_delivery_date(self, product_url):
        """Check delivery date for a product"""
        try:
            # Add random delay before navigating
            time.sleep(2)
            self.driver.get(product_url)
            
            # Wait for pincode input field to be available
            # self.scroll_to_element_smooth((By.CSS_SELECTOR, "input[placeholder*='pincode'], input[placeholder*='PIN']"))
            pincode_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@id='pin']"))
            )
            
            ActionChains(self.driver).move_to_element(pincode_input).perform()
            # pincode_input=self.driver.find_element(By.XPATH,"//input[@id='pin']")
            # self.driver.execute_script("arguments[0].scrollIntoView();", pincode_input)
            time.sleep(0.3)
            
            # Clear the field slowly like a human would
            pincode_input.clear()
            
            # Type pincode slowly
            for digit in self.pincode:
                pincode_input.send_keys(digit)
                time.sleep(0.1)  # Small delay between keystrokes
            
            # Small delay before clicking
            
            
            # Find and click check button
            check_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='CHECK']/ancestor::button"))
            )
            time.sleep(0.5)

            ActionChains(self.driver).move_to_element(check_btn).click().perform()

            # check_btn.click()
            
            # Wait for delivery info to load
            time.sleep(3)
            
            # Extract delivery date (adjust selector based on actual website structure)
            delivery_info = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[starts-with(normalize-space(), 'Delivery') and @color='greyBase']"))
            )
            
            return delivery_info.text
            
        except Exception as e:
            print(f"Error checking delivery date: {e}")
            return None

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    # Initialize scraper with your pincode and Chrome profile path
    scraper = MeeshoScraper(
        pincode="209861",  # Replace with your pincode
        chrome_profile_path=chrome_profile  # Path to your Chrome profile
    )
    
    try:
        # Set up driver
        scraper.setup_driver()

        
        # Example: Check delivery for a single product
        product_url = "https://www.meesho.com/trendy-women-fashion-kurti-trouser-with-dupatta/p/6fa13w"  # Updated with a real Meesho category URL
        delivery_info = scraper.check_delivery_date(product_url)
        
        print(f"Product URL: {product_url}")
        print(f"Delivery Info: {delivery_info}")
        
    finally:
        # Close the browser
        scraper.close()

if __name__ == "__main__":
    main()