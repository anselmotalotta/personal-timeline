#!/usr/bin/env python3
"""
Debug the actual page structure to see what's being rendered
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def debug_page_structure():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading frontend...")
        driver.get("http://localhost:52692")
        time.sleep(15)
        
        # Get the full page source
        page_source = driver.page_source
        
        # Look for specific sections
        print("\n=== SEARCHING FOR AI SECTIONS ===")
        
        # Look for the main sections I added
        sections_to_find = [
            "AI-Generated Stories",
            "Your Stories", 
            "People in Your Life",
            "Smart Photo Galleries",
            "AI Features Disabled",
            "loadingAIData",
            "stories.length",
            "people.length",
            "galleries.length"
        ]
        
        for section in sections_to_find:
            if section in page_source:
                print(f"✅ Found: {section}")
                # Get context around the found section
                index = page_source.find(section)
                context = page_source[max(0, index-100):index+200]
                print(f"   Context: ...{context}...")
            else:
                print(f"❌ Missing: {section}")
        
        # Check for React components
        print("\n=== REACT COMPONENTS CHECK ===")
        react_indicators = [
            "react-dom",
            "React",
            "__REACT_DEVTOOLS_GLOBAL_HOOK__",
            "data-reactroot"
        ]
        
        for indicator in react_indicators:
            if indicator in page_source:
                print(f"✅ React indicator found: {indicator}")
            else:
                print(f"❌ React indicator missing: {indicator}")
        
        # Look for the specific cards/sections I added
        print("\n=== CARD SECTIONS CHECK ===")
        
        # Find all Card elements
        cards = driver.find_elements(By.CLASS_NAME, "p-card")
        print(f"Total cards found: {len(cards)}")
        
        for i, card in enumerate(cards[:10]):  # Check first 10 cards
            try:
                card_text = card.text
                print(f"Card {i+1}: {card_text[:100]}...")
            except:
                print(f"Card {i+1}: Could not read text")
        
        # Check for specific AI status
        print("\n=== AI STATUS CHECK ===")
        
        # Execute JavaScript to check AI status
        try:
            ai_status = driver.execute_script("""
                // Try to access the AI status from the React component
                const root = document.getElementById('root');
                if (root && root._reactInternalFiber) {
                    return 'React fiber found';
                }
                return 'No React fiber';
            """)
            print(f"React status: {ai_status}")
        except Exception as e:
            print(f"JavaScript execution failed: {e}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_page_structure()