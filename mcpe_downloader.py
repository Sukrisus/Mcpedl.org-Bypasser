#!/usr/bin/env python3
"""
MCPE APK Direct Download Link Extractor
Extracts the direct download link from mcpedl.org
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
import json
import sys

# --- Selenium imports are moved to the setup_driver method ---
# This prevents the script from crashing on systems without Selenium, like Termux.

class MCPEDownloadExtractor:
    def __init__(self, use_selenium=False):
        self.session = requests.Session()
        # Set user agent to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.use_selenium = use_selenium
        self.driver = None
        
    def setup_driver(self):
        """Setup Selenium WebDriver for JavaScript-heavy sites"""
        # Only import selenium if it's actually going to be used.
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            print("❌ Selenium library not found. Please install it with 'pip install selenium'.")
            print("   Note: Selenium is not recommended for Termux as it requires a graphical browser.")
            self.use_selenium = False
            return

        if self.driver:
            return
            
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920x1080')
            chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Selenium WebDriver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            print("   Note: You need to install a compatible ChromeDriver for Selenium to work.")
            self.use_selenium = False
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_download_link(self, url):
        """
        Extract the direct download link from the given URL with timed delay support
        """
        try:
            print(f"🔍 Analyzing: {url}")
            
            if self.use_selenium:
                return self._get_download_link_selenium(url)
            else:
                return self._get_download_link_requests(url)
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def _get_download_link_requests(self, url):
        """Enhanced requests method with timer simulation for Termux"""
        try:
            print("⚙️ Using requests/BeautifulSoup method (Termux friendly)")
            # First request to get the page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Look for immediate direct links first
            direct_links = self._extract_direct_links_from_html(response.text, url)
            if direct_links:
                print("✅ Found direct link immediately.")
                return direct_links[0]
            
            # Simulate waiting for timer (since we can't execute JS)
            # Look for timer indicators in the page text
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text_lower = soup.get_text().lower()
            if any(word in page_text_lower for word in ['timer', 'countdown', 'please wait', 'seconds']):
                wait_time = 12 # A reasonable guess for countdown timers
                print(f"⏱️ Timer detected. Waiting for {wait_time} seconds to simulate countdown...")
                time.sleep(wait_time)
                
                # Make another request to the same URL to see if anything changed
                print("🔄 Re-fetching page after wait...")
                response2 = self.session.get(url, timeout=15)
                direct_links2 = self._extract_direct_links_from_html(response2.text, url)
                if direct_links2:
                    print("✅ Found direct link after waiting.")
                    return direct_links2[0]

            print("❌ Could not find a direct link.")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
        except Exception as e:
            print(f"❌ An error occurred in the requests method: {e}")
            return None

    def _extract_direct_links_from_html(self, html_content, base_url):
        """Extract direct download links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Look for your specific URL pattern first as it's most reliable
        pattern = r'https://mcpedl\.org/uploads_files/[^"\'\s<>]*\.apk'
        matches = re.findall(pattern, html_content)
        if matches:
            links.extend(matches)
        
        # Look for any other link ending in .apk
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.apk'):
                full_url = urljoin(base_url, href)
                if full_url not in links:
                    links.append(full_url)
        
        return list(set(links))  # Remove duplicates

    # --- The Selenium-based methods are kept below for completeness, ---
    # --- but they are not expected to work on Termux. ---
    
    def _get_download_link_selenium(self, url):
        """Use Selenium to handle JavaScript and timed delays"""
        try:
            self.setup_driver()
            if not self.driver or not self.use_selenium:
                print("⚠️ Selenium not available. Falling back to requests method...")
                return self._get_download_link_requests(url)
            
            print("🌐 Loading page with Selenium...")
            self.driver.get(url)
            
            # Wait up to 15 seconds for a link to appear
            max_wait_time = 15
            print(f"⏳ Waiting up to {max_wait_time} seconds for download link...")
            time.sleep(max_wait_time)

            page_source = self.driver.page_source
            direct_links = self._extract_direct_links_from_html(page_source, url)
            if direct_links:
                print("✅ Found link with Selenium.")
                return direct_links[0]
            
            print("❌ Could not extract download link using Selenium")
            return None
            
        except Exception as e:
            print(f"❌ Selenium method failed: {e}")
            return None

def main():
    """Main function to run the extractor"""
    if len(sys.argv) < 2:
        print("Usage: python mcpe_downloader.py <URL>")
        print("Example: python mcpe_downloader.py https://mcpedl.org/getfile/5916")
        sys.exit(1)
    
    url = sys.argv[1]
    
    if not url.startswith('http'):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    # The script will default to the Termux-friendly 'requests' method.
    # Selenium will only be attempted if you add a '-s' or '--selenium' flag.
    use_selenium_flag = len(sys.argv) > 2 and sys.argv[2] in ['-s', '--selenium']
    
    extractor = MCPEDownloadExtractor(use_selenium=use_selenium_flag)
    
    try:
        download_link = extractor.get_download_link(url)
        
        if download_link:
            # Print only the final link for easy use in other scripts
            print(download_link)
        else:
            print("❌ No download link found.", file=sys.stderr)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        extractor.close_driver()

if __name__ == "__main__":
    main()

