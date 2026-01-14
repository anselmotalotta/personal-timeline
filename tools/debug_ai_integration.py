#!/usr/bin/env python3
"""
Debug AI integration specifically
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def debug_ai_integration():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading frontend...")
        driver.get("http://localhost:52692")
        time.sleep(15)  # Wait longer for everything to load
        
        # Check console errors
        logs = driver.get_log('browser')
        print(f"\n=== CONSOLE LOGS ({len(logs)} entries) ===")
        for log in logs:
            print(f"{log['level']}: {log['message']}")
        
        # Look for AI-specific content
        print(f"\n=== AI CONTENT CHECK ===")
        
        # Look for story cards
        story_cards = driver.find_elements(By.XPATH, "//*[contains(text(), 'Your Stories') or contains(text(), 'stories from your memories')]")
        print(f"Story sections found: {len(story_cards)}")
        
        # Look for people cards
        people_cards = driver.find_elements(By.XPATH, "//*[contains(text(), 'People in Your Life') or contains(text(), 'people in your photos')]")
        print(f"People sections found: {len(people_cards)}")
        
        # Look for gallery cards
        gallery_cards = driver.find_elements(By.XPATH, "//*[contains(text(), 'Smart Photo Galleries') or contains(text(), 'smart galleries')]")
        print(f"Gallery sections found: {len(gallery_cards)}")
        
        # Look for loading indicators
        loading_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Loading') or contains(@class, 'p-progressbar')]")
        print(f"Loading indicators found: {len(loading_elements)}")
        
        # Check if AI status is working
        ai_status_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'AI Features') or contains(text(), 'OpenAI')]")
        print(f"AI status elements found: {len(ai_status_elements)}")
        
        # Get page source to check for specific content
        page_source = driver.page_source
        
        # Check for specific AI content
        ai_content_indicators = [
            "Your Stories",
            "People in Your Life", 
            "Smart Photo Galleries",
            "AI has generated",
            "AI has identified",
            "AI has organized"
        ]
        
        print(f"\n=== AI CONTENT INDICATORS ===")
        for indicator in ai_content_indicators:
            if indicator in page_source:
                print(f"✅ Found: {indicator}")
            else:
                print(f"❌ Missing: {indicator}")
                
        # Check for error messages
        error_indicators = [
            "Failed to load",
            "Error loading",
            "No stories generated",
            "No people detected",
            "No smart galleries"
        ]
        
        print(f"\n=== ERROR INDICATORS ===")
        for indicator in error_indicators:
            if indicator in page_source:
                print(f"⚠️  Found: {indicator}")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_ai_integration()