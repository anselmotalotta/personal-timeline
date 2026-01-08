#!/usr/bin/env python3
"""
Debug frontend issues by checking what's actually happening
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def debug_frontend():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading frontend...")
        driver.get("http://localhost:52692")
        time.sleep(10)
        
        # Check console errors
        logs = driver.get_log('browser')
        print(f"\n=== CONSOLE LOGS ({len(logs)} entries) ===")
        for log in logs:
            if log['level'] in ['SEVERE', 'WARNING']:
                print(f"{log['level']}: {log['message']}")
        
        # Check page content
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"\n=== PAGE CONTENT SAMPLE ===")
        print(body_text[:500] + "..." if len(body_text) > 500 else body_text)
        
        # Check for specific elements
        print(f"\n=== ELEMENT CHECK ===")
        
        # Stories
        story_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'story') or contains(text(), 'Story')]")
        print(f"Story elements found: {len(story_elements)}")
        
        # People
        people_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'people') or contains(text(), 'People')]")
        print(f"People elements found: {len(people_elements)}")
        
        # Photos/Gallery
        photo_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'photo') or contains(text(), 'Photo') or contains(text(), 'gallery') or contains(text(), 'Gallery')]")
        print(f"Photo elements found: {len(photo_elements)}")
        
        # Check network requests
        print(f"\n=== NETWORK ACTIVITY ===")
        performance_logs = driver.get_log('performance')
        api_requests = []
        for log in performance_logs:
            message = log.get('message', {})
            if isinstance(message, str):
                import json
                try:
                    message = json.loads(message)
                except:
                    continue
            
            if message.get('message', {}).get('method') == 'Network.responseReceived':
                url = message['message']['params']['response']['url']
                status = message['message']['params']['response']['status']
                if 'localhost:8086' in url:
                    api_requests.append(f"{status} {url}")
        
        print("API requests made:")
        for req in api_requests[-10:]:  # Last 10 requests
            print(f"  {req}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_frontend()