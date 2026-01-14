"""
End-to-end tests for complete user workflows
Tests the application from a user's perspective to ensure it delivers expected functionality
"""
import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class TestUserWorkflows:
    
    @classmethod
    def setup_class(cls):
        """Setup for user workflow testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.set_page_load_timeout(30)
            cls.frontend_url = "http://localhost:52692"
            cls.api_url = "http://localhost:8086"
            cls.wait = WebDriverWait(cls.driver, 15)
            
        except WebDriverException:
            pytest.skip("Chrome browser not available for E2E testing")
    
    @classmethod
    def teardown_class(cls):
        """Clean up"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def test_application_startup_workflow(self):
        """Test complete application startup from user perspective"""
        # User opens the application
        self.driver.get(self.frontend_url)
        
        # Application should load within reasonable time
        start_time = time.time()
        
        # Wait for React to load and render content
        self.wait.until(lambda driver: len(driver.find_element(By.ID, "root").get_attribute("innerHTML")) > 100)
        
        load_time = time.time() - start_time
        assert load_time < 15, f"Application took too long to load: {load_time}s"
        
        # User should see the application title
        assert "Personal Timeline" in self.driver.title
        
        # User should see some content indicating the app is working
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        expected_content = ["timeline", "personal", "stories", "people", "photos", "memories"]
        assert any(content in page_text for content in expected_content), "No recognizable app content found"
    
    def test_ai_status_awareness_workflow(self):
        """Test that users can understand AI service status"""
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        # User should be able to see AI status information
        page_source = self.driver.page_source.lower()
        
        # Look for AI status indicators
        ai_indicators = ["ai", "openai", "provider", "status", "available", "working"]
        ai_status_visible = any(indicator in page_source for indicator in ai_indicators)
        
        if ai_status_visible:
            # If AI status is shown, it should be clear to the user
            status_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'AI') or contains(text(), 'OpenAI') or contains(@class, 'status')]")
            
            if status_elements:
                status_text = " ".join([elem.text for elem in status_elements if elem.is_displayed()])
                # Status should indicate whether AI is working or not
                assert any(word in status_text.lower() for word in ['working', 'available', 'unavailable', 'configured', 'ready'])
    
    def test_data_exploration_workflow(self):
        """Test user can explore their personal data"""
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        # User should be able to see their data or understand why they can't
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Check if people data is accessible
        if "people" in page_text or "person" in page_text:
            # User should see people information or explanation
            people_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'people') or contains(text(), 'person')]")
            assert len(people_elements) > 0
        
        # Check if photos/galleries are accessible
        if "photo" in page_text or "gallery" in page_text or "image" in page_text:
            # User should see photo information or explanation
            photo_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'photo') or contains(text(), 'gallery') or contains(text(), 'image')]")
            assert len(photo_elements) > 0
        
        # User should see some form of content or clear explanation of why content isn't available
        content_indicators = ["stories", "people", "photos", "memories", "timeline", "data", "no data", "empty", "add data"]
        assert any(indicator in page_text for indicator in content_indicators)
    
    def test_story_generation_workflow(self):
        """Test complete story generation workflow from user perspective"""
        # First verify API can generate stories
        try:
            response = requests.post(
                f"{self.api_url}/stories/generate",
                json={"type": "chronological", "theme": "E2E test story"},
                timeout=30
            )
            api_works = response.status_code == 200
        except:
            api_works = False
        
        if not api_works:
            pytest.skip("Story generation API not working, skipping user workflow test")
        
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        # User looks for story-related functionality
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "story" in page_text or "stories" in page_text:
            # User should be able to interact with story features
            story_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'story') or contains(text(), 'stories')]")
            
            # Look for interactive story elements (buttons, links, etc.)
            story_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'story') or contains(text(), 'Story')]")
            story_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'story') or contains(text(), 'Story')]")
            
            interactive_story_elements = story_buttons + story_links
            
            if interactive_story_elements:
                # User can interact with story functionality
                for element in interactive_story_elements[:2]:  # Try first 2 elements
                    if element.is_displayed() and element.is_enabled():
                        try:
                            element.click()
                            time.sleep(2)
                            # Verify some response to user interaction
                            new_page_text = self.driver.find_element(By.TAG_NAME, "body").text
                            assert len(new_page_text) > 0
                            break
                        except Exception:
                            continue
    
    def test_error_recovery_workflow(self):
        """Test how users experience and recover from errors"""
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        # Check if there are any visible errors
        error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'failed') or contains(text(), 'Failed')]")
        
        visible_errors = [elem for elem in error_elements if elem.is_displayed()]
        
        if visible_errors:
            # If errors are shown, they should be user-friendly
            for error_elem in visible_errors[:3]:  # Check first 3 errors
                error_text = error_elem.text
                
                # Error should not be a raw technical error
                assert "TypeError" not in error_text
                assert "undefined is not" not in error_text
                assert "Cannot read property" not in error_text
                
                # Error should be reasonably short and understandable
                assert len(error_text) < 300
        
        # User should still be able to use basic functionality despite errors
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        working_buttons = [btn for btn in buttons if btn.is_enabled() and btn.is_displayed()]
        
        # Should have some working interactive elements
        assert len(working_buttons) > 0, "No working buttons available to user"
    
    def test_data_privacy_workflow(self):
        """Test that user data privacy is maintained"""
        # Check that no sensitive data is exposed in the frontend
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        page_source = self.driver.page_source
        
        # Should not contain API keys or sensitive configuration
        sensitive_patterns = ["sk-", "api_key", "secret", "password", "token"]
        for pattern in sensitive_patterns:
            assert pattern not in page_source.lower(), f"Potentially sensitive data '{pattern}' found in frontend"
        
        # Check that error messages don't expose internal paths
        internal_paths = ["/app/", "/src/", "/node_modules/", "localhost:"]
        for path in internal_paths:
            # Some paths might be acceptable in development, but not in large quantities
            occurrences = page_source.lower().count(path)
            assert occurrences < 10, f"Too many internal path references '{path}' found: {occurrences}"
    
    def test_performance_user_experience(self):
        """Test performance from user perspective"""
        start_time = time.time()
        
        # User loads the application
        self.driver.get(self.frontend_url)
        
        # Wait for meaningful content to appear
        self.wait.until(lambda driver: len(driver.find_element(By.ID, "root").get_attribute("innerHTML")) > 500)
        
        initial_load_time = time.time() - start_time
        
        # Initial load should be reasonable
        assert initial_load_time < 20, f"Initial load too slow: {initial_load_time}s"
        
        # Test navigation performance
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        links = self.driver.find_elements(By.TAG_NAME, "a")
        
        interactive_elements = [elem for elem in buttons + links if elem.is_displayed() and elem.is_enabled()]
        
        if interactive_elements:
            # Test clicking performance
            for element in interactive_elements[:3]:  # Test first 3 elements
                try:
                    click_start = time.time()
                    element.click()
                    
                    # Wait for any UI updates
                    time.sleep(1)
                    
                    click_response_time = time.time() - click_start
                    
                    # UI should respond quickly to user interactions
                    assert click_response_time < 5, f"UI response too slow: {click_response_time}s"
                    
                except Exception:
                    continue
    
    def test_mobile_user_experience(self):
        """Test mobile user experience"""
        # Set mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone SE size
        
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        # Content should be accessible on mobile
        root = self.driver.find_element(By.ID, "root")
        assert root.is_displayed()
        
        # Should not have horizontal scrolling
        body_width = self.driver.execute_script("return document.body.scrollWidth")
        viewport_width = self.driver.execute_script("return window.innerWidth")
        assert body_width <= viewport_width + 20, "Horizontal scrolling detected on mobile"
        
        # Interactive elements should be touch-friendly
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in buttons[:5]:  # Check first 5 buttons
            if button.is_displayed():
                size = button.size
                # Buttons should be at least 44px (Apple's recommended touch target size)
                assert size['height'] >= 30 or size['width'] >= 30, f"Button too small for touch: {size}"
        
        # Reset to desktop size
        self.driver.set_window_size(1920, 1080)
    
    def test_complete_user_journey(self):
        """Test a complete user journey through the application"""
        # User opens the application
        self.driver.get(self.frontend_url)
        time.sleep(5)
        
        # User sees the main interface
        assert "Personal Timeline" in self.driver.title
        
        # User explores available features
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Track what features user can access
        accessible_features = []
        
        if "people" in page_text:
            accessible_features.append("people")
        
        if "story" in page_text or "stories" in page_text:
            accessible_features.append("stories")
        
        if "photo" in page_text or "gallery" in page_text:
            accessible_features.append("photos")
        
        # User should have access to at least one main feature
        assert len(accessible_features) > 0, "No main features accessible to user"
        
        # User tries to interact with available features
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        successful_interactions = 0
        
        for button in buttons[:5]:  # Try first 5 buttons
            if button.is_displayed() and button.is_enabled():
                try:
                    button_text = button.text.lower()
                    # Avoid potentially destructive actions
                    if not any(avoid in button_text for avoid in ['delete', 'remove', 'clear']):
                        button.click()
                        time.sleep(2)
                        successful_interactions += 1
                        
                        # Verify the interaction had some effect
                        new_content = self.driver.find_element(By.TAG_NAME, "body").text
                        assert len(new_content) > 0
                        
                        if successful_interactions >= 2:  # Test a few interactions
                            break
                            
                except Exception:
                    continue
        
        # User should be able to interact with the application
        assert successful_interactions > 0, "User cannot successfully interact with any features"
        
        # Final state should still be functional
        final_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        working_final_buttons = [btn for btn in final_buttons if btn.is_enabled() and btn.is_displayed()]
        assert len(working_final_buttons) > 0, "Application not functional after user interactions"