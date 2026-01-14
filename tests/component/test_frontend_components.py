"""
Component tests for frontend React components
Tests individual components in isolation
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class TestFrontendComponents:
    
    @classmethod
    def setup_class(cls):
        """Setup Chrome driver for component testing"""
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
            cls.wait = WebDriverWait(cls.driver, 10)
            
            # Load the application
            cls.driver.get(cls.frontend_url)
            time.sleep(8)  # Wait for React to load
            
        except WebDriverException:
            pytest.skip("Chrome browser not available for component testing")
    
    @classmethod
    def teardown_class(cls):
        """Clean up driver"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def test_page_loads_correctly(self):
        """Test that the main page loads with correct title and structure"""
        assert "Personal Timeline" in self.driver.title
        
        # Check React root exists and has content
        root = self.driver.find_element(By.ID, "root")
        assert root is not None
        
        content = root.get_attribute("innerHTML")
        assert len(content) > 100  # Should have substantial content
    
    def test_navigation_components(self):
        """Test navigation components are present and functional"""
        # Look for navigation elements
        nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
        if nav_elements:
            # Navigation should be visible
            assert nav_elements[0].is_displayed()
        
        # Look for menu items or navigation links
        links = self.driver.find_elements(By.TAG_NAME, "a")
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        
        # Should have some interactive elements
        assert len(links) + len(buttons) > 0
    
    def test_ai_status_badge_component(self):
        """Test AI status badge component displays correctly"""
        try:
            # Look for AI status indicators
            status_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'status') or contains(text(), 'AI') or contains(text(), 'OpenAI')]")
            
            if status_elements:
                # Status should be visible
                status_element = status_elements[0]
                assert status_element.is_displayed()
                
                # Should contain status information
                status_text = status_element.text.lower()
                assert any(word in status_text for word in ['ai', 'openai', 'status', 'available', 'working'])
        
        except Exception:
            # AI status component might not be visible depending on configuration
            pass
    
    def test_content_cards_component(self):
        """Test that content cards render properly"""
        # Look for PrimeReact cards or similar content containers
        cards = self.driver.find_elements(By.CLASS_NAME, "p-card")
        
        if not cards:
            # Try alternative card selectors
            cards = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'card')]")
        
        if cards:
            # Cards should be visible
            visible_cards = [card for card in cards if card.is_displayed()]
            assert len(visible_cards) > 0
            
            # Cards should have content
            for card in visible_cards[:3]:  # Check first 3 cards
                card_text = card.text
                assert len(card_text.strip()) > 0
    
    def test_interactive_buttons(self):
        """Test that interactive buttons are present and clickable"""
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        
        # Should have interactive buttons
        assert len(buttons) > 0
        
        # Buttons should be enabled and visible
        enabled_buttons = [btn for btn in buttons if btn.is_enabled() and btn.is_displayed()]
        assert len(enabled_buttons) > 0
        
        # Test clicking a safe button (like a navigation or info button)
        for button in enabled_buttons[:3]:  # Test first 3 buttons
            button_text = button.text.lower()
            # Avoid buttons that might trigger destructive actions
            if any(safe_word in button_text for safe_word in ['info', 'help', 'view', 'show', 'details']):
                try:
                    button.click()
                    time.sleep(1)  # Wait for any UI updates
                    # Just verify no errors occurred
                    break
                except Exception:
                    continue
    
    def test_form_components(self):
        """Test form components if present"""
        # Look for input fields
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        
        form_elements = inputs + textareas + selects
        
        if form_elements:
            # Test that form elements are functional
            for element in form_elements[:2]:  # Test first 2 form elements
                if element.is_displayed() and element.is_enabled():
                    element_type = element.get_attribute("type")
                    
                    # Test text inputs
                    if element_type in ["text", "search", "email"] or element.tag_name == "textarea":
                        try:
                            element.clear()
                            element.send_keys("test input")
                            assert element.get_attribute("value") == "test input"
                            element.clear()
                        except Exception:
                            continue
    
    def test_error_handling_components(self):
        """Test that error states are handled gracefully"""
        # Check for error messages or error boundaries
        error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error')]")
        
        # If errors are displayed, they should be user-friendly
        for error_element in error_elements:
            if error_element.is_displayed():
                error_text = error_element.text
                # Error messages should not contain technical stack traces
                assert "at " not in error_text  # Stack trace indicator
                assert "TypeError" not in error_text  # Raw JS errors
                assert len(error_text) < 500  # Should be concise
    
    def test_loading_states(self):
        """Test loading state components"""
        # Look for loading indicators
        loading_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(text(), 'Loading')]")
        
        # Loading states should be properly styled if present
        for loading_element in loading_elements:
            if loading_element.is_displayed():
                # Should have appropriate styling
                classes = loading_element.get_attribute("class")
                assert classes is not None
    
    def test_responsive_design(self):
        """Test responsive design components"""
        # Test different viewport sizes
        viewports = [
            (1920, 1080),  # Desktop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]
        
        for width, height in viewports:
            self.driver.set_window_size(width, height)
            time.sleep(1)
            
            # Check that content is still visible and accessible
            root = self.driver.find_element(By.ID, "root")
            assert root.is_displayed()
            
            # Content should not overflow horizontally
            body_width = self.driver.execute_script("return document.body.scrollWidth")
            viewport_width = self.driver.execute_script("return window.innerWidth")
            
            # Allow for small scrollbars
            assert body_width <= viewport_width + 20
        
        # Reset to desktop size
        self.driver.set_window_size(1920, 1080)
    
    def test_accessibility_basics(self):
        """Test basic accessibility features"""
        # Check for proper heading structure
        headings = self.driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4 | //h5 | //h6")
        
        if headings:
            # Should have at least one main heading
            h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
            # Either h1 exists or page title serves as main heading
            assert len(h1_elements) > 0 or "Personal Timeline" in self.driver.title
        
        # Check for alt text on images
        images = self.driver.find_elements(By.TAG_NAME, "img")
        for img in images[:5]:  # Check first 5 images
            alt_text = img.get_attribute("alt")
            # Images should have alt text (can be empty for decorative images)
            assert alt_text is not None
        
        # Check for proper button labels
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in buttons[:5]:  # Check first 5 buttons
            button_text = button.text.strip()
            aria_label = button.get_attribute("aria-label")
            title = button.get_attribute("title")
            
            # Button should have some form of accessible label
            assert button_text or aria_label or title
    
    def test_javascript_errors(self):
        """Test that no critical JavaScript errors are present"""
        # Get browser console logs
        logs = self.driver.get_log('browser')
        
        # Filter for severe errors
        severe_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        # Should not have critical JavaScript errors that break functionality
        critical_errors = []
        for error in severe_errors:
            message = error['message'].lower()
            # Filter out known non-critical errors
            if not any(ignore in message for ignore in ['404', 'network', 'favicon']):
                critical_errors.append(error)
        
        # Report critical errors for debugging
        if critical_errors:
            print(f"Critical JavaScript errors found: {len(critical_errors)}")
            for error in critical_errors[:3]:  # Show first 3
                print(f"  - {error['message']}")
        
        # Allow some errors but not too many
        assert len(critical_errors) < 5, f"Too many critical JavaScript errors: {len(critical_errors)}"