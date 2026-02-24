import re
import os
from playwright.sync_api import sync_playwright

def clean_syllabus_text(raw_text):
    """Removes timestamps and empty lines to leave only clean topics."""
    # Remove timestamps like 05:41 or 1:23:45
    no_times = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\b', '', raw_text)
    # Remove 'Preview' text and quiz indicators often found in the list
    no_preview = re.sub(r'Preview|quiz', '', no_times, flags=re.IGNORECASE)
    lines = [line.strip() for line in no_preview.split('\n') if line.strip()]
    return '\n'.join(lines)

def scrape_udemy_course(course_url, email, password):
    # USE YOUR ACTUAL DIRECTORY PATH HERE
    user_data_dir = r"D:\Desktop\Internship\playwright_udemy_session"
    
    # Ensure the directory exists
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    with sync_playwright() as p:
        print("Launching browser...")
        context = p.chromium.launch_persistent_context(
            user_data_dir, 
            headless=False,  # Keep visible for now to ensure session is active
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        print(f"Navigating to: {course_url}")
        page.goto(course_url)

        # 1. Handle Login only if necessary
        # Check for login fields or 'Sign In' buttons
        try:
            if page.locator("input[name='email']").is_visible(timeout=5000):
                print("Session expired or not found. Attempting login...")
                page.fill("input[name='email']", email)
                page.fill("input[name='password']", password)
                page.click("button[type='submit']")
                # Wait for navigation back to the course page after login
                page.wait_for_url(course_url, timeout=60000)
                print("Login successful.")
        except Exception:
            print("Already logged in or login fields not found. Proceeding...")

        # 2. Wait for the Content to load (REPLACED networkidle)
        print("Waiting for course curriculum to load...")
        try:
            # We wait for the specific curriculum container instead of the whole network
            page.wait_for_selector('[data-purpose="course-curriculum"]', timeout=20000)
        except Exception:
            print("Timeout waiting for curriculum. The page might be rendered differently.")

        # 3. Expand the Course Content
        try:
            # Locate the expand button
            expand_btn = page.locator('button[data-purpose="expand-toggle"], button:has-text("Expand all sections")').first
            if expand_btn.is_visible():
                print("Expanding all sections...")
                expand_btn.click()
                # Short sleep to let the accordion animation finish
                page.wait_for_timeout(1500) 
        except Exception:
            print("Could not find 'Expand all sections' button. It might already be expanded.")

        # 4. Extract Data
        print("Extracting content...")
        
        # Syllabus
        curriculum_raw = page.locator('[data-purpose="course-curriculum"]').inner_text()
        clean_curriculum = clean_syllabus_text(curriculum_raw)

        # Target Audience
        audience_raw = ""
        audience_loc = page.locator('[data-purpose="target-audience"]')
        if audience_loc.count() > 0:
            audience_raw = audience_loc.inner_text()

        # Description
        desc_raw = ""
        desc_loc = page.locator('[data-purpose="course-description"]')
        if desc_loc.count() > 0:
            desc_raw = desc_loc.inner_text()

        context.close()

        return {
            "curriculum": clean_curriculum,
            "target_audience": audience_raw,
            "description": desc_raw
        }

if __name__ == "__main__":
    # Test with the specific URL provided
    target_url = "https://azirotechnologies.udemy.com/course/llms-mastery-complete-guide-to-transformers-generative-ai/?kw=LLMs+Mastery%3A+Complete+Guide+to+Transformers+%26+Generative+AI&src=sac"
    # target_url = "https://azirotechnologies.udemy.com/course/claude-code-the-practical-guide/"
    # target_url = "https://azirotechnologies.udemy.com/course/claudecode/"
    # Credentials used only if the persistent session is invalid
    data = scrape_udemy_course(target_url, "your_email@aziro.com", "your_password")
    
    # Save Output
    output_file = "LLMs Mastery_Complete Guide to Transformers and Gen AI.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"--- TARGET AUDIENCE ---\n{data['target_audience']}\n\n")
        f.write(f"--- DESCRIPTION ---\n{data['description']}\n\n")
        f.write(f"--- CURRICULUM ---\n{data['curriculum']}")
    
    print(f"\nSUCCESS! Data saved to {output_file}")
    print("-" * 30)
    print("Preview of cleaned curriculum:")
    print("\n".join(data['curriculum'].split('\n')[:10])) # Print first 10 lines


# import re
# from playwright.sync_api import sync_playwright

# def clean_syllabus_text(raw_text):
#     """Removes timestamps (e.g., 05:41, 1:10) and empty lines to leave only clean topics."""
#     # Remove timestamps like 12:34 or 1:23:45
#     no_times = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\b', '', raw_text)
#     # Remove lines that are just numbers or common boilerplate
#     lines = [line.strip() for line in no_times.split('\n') if line.strip()]
#     return '\n'.join(lines)

# def scrape_udemy_course(course_url, email, password):
#     # We use a user_data_dir to save login state. 
#     # The first time it runs, it will log in. Subsequent runs will use the saved session.
#     # with sync_playwright() as p:
#     #     # Launching with a persistent context avoids having to log in every single time
#     #     browser = p.chromium.launch_persistent_context(
#     #         user_data_dir="./udemy_auth_state", 
#     #         headless=False, # Set to True once you confirm login works perfectly
#     #         viewport={"width": 1280, "height": 720}
#     #     )
#     #     page = browser.new_page()

#     #     # 1. Handle Login (Modify selectors based on your company's specific SSO)
#     #     page.goto("https://azirotechnologies.udemy.com")
    
#     with sync_playwright() as p:
#     # Use the SAME path here
#         user_data_dir = r"D:\Desktop\Internship\playwright_udemy_session"
        
#         browser = p.chromium.launch_persistent_context(
#             user_data_dir, 
#             headless=True
#         )
#         page = browser.new_page()
        
#         page.goto("https://azirotechnologies.udemy.com/course/claude-code-the-practical-guide/")
            
#         # Check if we are already logged in by looking for a login input
#         if page.locator("input[name='email']").is_visible(timeout=5000):
#             print("Logging in...")
#             page.fill("input[name='email']", email)
#             page.fill("input[name='password']", password)
#             page.click("button[type='submit']")
#             # Wait for successful login (e.g., waiting for the avatar or 'My learning' to appear)
#             page.wait_for_selector("text=My learning", timeout=30000)
#             print("Login successful.")

#         # 2. Navigate to the agnostic Course URL
#         print(f"Navigating to course: {course_url}")
#         page.goto(course_url)

#         # Wait for the DOM to settle
#         page.wait_for_load_state("networkidle")

#         # 3. Expand the Course Content
#         try:
#             expand_btn = page.locator('button:has-text("Expand all sections")').first
#             if expand_btn.is_visible(timeout=5000):
#                 expand_btn.click()
#                 print("Clicked 'Expand all sections'.")
#                 page.wait_for_timeout(2000) # Give it a moment to render the expanded DOM
#         except Exception as e:
#             print("Could not find or click 'Expand all sections'. It may already be expanded.")

#         # 4. Extract "Course Content" (Syllabus)
#         print("Extracting Curriculum...")
#         # Targeting the data-purpose attribute is usually the safest bet on Udemy
#         curriculum_locator = page.locator('[data-purpose="course-curriculum"]')
#         raw_curriculum = curriculum_locator.inner_text() if curriculum_locator.count() > 0 else ""
#         clean_curriculum = clean_syllabus_text(raw_curriculum)

#         # 5. Extract "Who this course is for" & "Description"
#         print("Extracting Audience and Description...")
#         target_audience_locator = page.locator('[data-purpose="target-audience"]')
#         target_audience = target_audience_locator.inner_text() if target_audience_locator.count() > 0 else ""

#         description_locator = page.locator('[data-purpose="course-description"]')
#         description = description_locator.inner_text() if description_locator.count() > 0 else ""

#         browser.close()

#         return {
#             "curriculum": clean_curriculum,
#             "target_audience": target_audience,
#             "description": description
#         }

# if __name__ == "__main__":
#     url = "https://azirotechnologies.udemy.com/course/claude-code-the-practical-guide/"
#     # Warning: Hardcoding enterprise credentials can be risky. See notes above about SSO.
#     data = scrape_udemy_course(url, "your_email@aziro.com", "your_password")
    
#     # Save the extracted data to text files for the LLM to pick up
#     with open("extracted_content.txt", "w", encoding="utf-8") as f:
#         f.write(f"--- TARGET AUDIENCE ---\n{data['target_audience']}\n\n")
#         f.write(f"--- DESCRIPTION ---\n{data['description']}\n\n")
#         f.write(f"--- CURRICULUM ---\n{data['curriculum']}")
#     print("Extraction complete. Saved to extracted_content.txt")