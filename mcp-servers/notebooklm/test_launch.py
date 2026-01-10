from playwright.sync_api import sync_playwright
import os
import time

USER_DATA_DIR = r"C:\Users\dell3630\AppData\Local\Google\Chrome\User Data"

def test_launch():
    print(f"Attempting to launch Chrome with profile: {USER_DATA_DIR}")
    if os.path.exists(USER_DATA_DIR):
        print("Profile directory found.")
    else:
        print("Profile directory NOT found!")
        return

    try:
        with sync_playwright() as p:
            # Note: This might fail if Chrome is already open
            print("Launching browser context...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                channel="chrome",
                headless=False,
                args=["--remote-debugging-port=9222"] 
            )
            print("Browser launched!")
            
            page = browser.new_page()
            print("Navigating to NotebookLM...")
            page.goto("https://notebooklm.google.com/")
            
            print("Waiting for page load...")
            page.wait_for_timeout(5000)
            
            title = page.title()
            print(f"Page title: {title}")
            
            # Check for specific visible text to confirm login state
            content = page.content()
            if "Sign in" in title or "Sign in" in content:
                print("STATUS: Login likely required.")
            else:
                print("STATUS: Likely logged in.")

            print("Closing in 5 seconds...")
            time.sleep(5)
            browser.close()
            print("Test complete.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        print("hint: Make sure all Chrome windows are CLOSED before helping.")

if __name__ == "__main__":
    test_launch()
