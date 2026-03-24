from playwright.sync_api import sync_playwright

def run_manual_login():
    user_data_dir = r"D:\Desktop\Internship\playwright_udemy_session"

    with sync_playwright() as p:
        # Launching with a persistent context
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,  # We NEED to see it to log in
            args=["--start-maximized"] 
        )
        
        page = context.new_page()
        page.goto("https://azirotechnologies.udemy.com")

        print("\n" + "="*50)
        print("ACTION REQUIRED: Please log in manually in the browser window.")
        print("Complete your SSO, 2FA, and whatever else Udemy throws at you.")
        print("Once you are on the Udemy Dashboard, come back here and press Enter.")
        print("="*50 + "\n")

        input("Press Enter here ONLY after you have successfully logged in...")
        
        # Save storage state is an extra safety measure, but the folder usually handles it.
        context.storage_state(path="auth.json") 
        context.close()
        print("Session saved! You can now close this script.")

if __name__ == "__main__":
    run_manual_login()