#!/usr/bin/env python3
"""
Test AI status directly in the browser
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_ai_status_in_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Loading frontend...")
        driver.get("http://localhost:52692")
        time.sleep(15)
        
        # Execute JavaScript to test AI status API directly
        result = driver.execute_script("""
            return new Promise((resolve) => {
                fetch('http://localhost:8086/status')
                    .then(response => response.json())
                    .then(data => {
                        console.log('AI Status API Response:', data);
                        resolve({
                            success: true,
                            data: data,
                            isAIAvailable: data.ai_status === 'full' || data.ai_status === 'partial',
                            features: data.features
                        });
                    })
                    .catch(error => {
                        console.error('AI Status API Error:', error);
                        resolve({
                            success: false,
                            error: error.toString()
                        });
                    });
            });
        """)
        
        print("AI Status Test Result:")
        print(f"  Success: {result.get('success')}")
        if result.get('success'):
            print(f"  AI Status: {result['data']['ai_status']}")
            print(f"  Is AI Available: {result['isAIAvailable']}")
            print(f"  Features: {result['data']['features']}")
        else:
            print(f"  Error: {result.get('error')}")
        
        # Test stories API
        stories_result = driver.execute_script("""
            return new Promise((resolve) => {
                fetch('http://localhost:8086/stories')
                    .then(response => response.json())
                    .then(data => {
                        resolve({
                            success: true,
                            count: data.stories ? data.stories.length : 0,
                            stories: data.stories ? data.stories.slice(0, 2) : []
                        });
                    })
                    .catch(error => {
                        resolve({
                            success: false,
                            error: error.toString()
                        });
                    });
            });
        """)
        
        print("\nStories API Test Result:")
        print(f"  Success: {stories_result.get('success')}")
        if stories_result.get('success'):
            print(f"  Stories Count: {stories_result['count']}")
            if stories_result['stories']:
                print(f"  First Story: {stories_result['stories'][0]['title']}")
        else:
            print(f"  Error: {stories_result.get('error')}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test_ai_status_in_browser()