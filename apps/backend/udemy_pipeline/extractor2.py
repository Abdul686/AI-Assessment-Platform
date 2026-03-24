import re
import os
from playwright.sync_api import sync_playwright

def sanitize_filename(text):
    """Removes characters that are illegal in Windows filenames."""
    # Keep only alphanumeric, spaces, and hyphens/underscores
    return re.sub(r'[\\/*?:"<>|]', "", text).strip()

def clean_syllabus_text(raw_text):
    """Removes timestamps and empty lines to leave only clean topics."""
    no_times = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\b', '', raw_text)
    no_preview = re.sub(r'Preview|quiz', '', no_times, flags=re.IGNORECASE)
    lines = [line.strip() for line in no_preview.split('\n') if line.strip()]
    return '\n'.join(lines)

def process_courses(urls, email, password):
    # Setup directory
    output_dir = "AI-ML RAG-Gen"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    user_data_dir = r"D:\Desktop\Internship\Aziro-L-D-AI-Assessment\playwright_udemy_session"

    with sync_playwright() as p:
        print("Launching browser context...")
        context = p.chromium.launch_persistent_context(
            user_data_dir, 
            headless=False, # Set to True for background operation
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        for url in urls:
            url = url.strip()
            if not url: continue
            
            print(f"\n--- Processing: {url} ---")
            try:
                page.goto(url, timeout=60000)
                
                # Check for login only if it hits a login wall
                if "login" in page.url or page.locator("input[name='email']").is_visible(timeout=3000):
                    print("Prompted for login. Attempting automated entry...")
                    page.fill("input[name='email']", email)
                    page.fill("input[name='password']", password)
                    page.click("button[type='submit']")
                    page.wait_for_url(url, timeout=60000)

                # 1. Get Course Title for the Filename
                # Udemy titles are usually in an h1 with data-purpose="course-title"
                title_loc = page.locator('h1[data-purpose="course-title"], h1').first
                course_title = title_loc.inner_text() if title_loc.is_visible() else "Unknown_Course"
                safe_name = sanitize_filename(course_title)
                
                # 2. Expand Curriculum
                page.wait_for_selector('[data-purpose="course-curriculum"]', timeout=15000)
                expand_btn = page.locator('button[data-purpose="expand-toggle"], button:has-text("Expand all sections")').first
                if expand_btn.is_visible():
                    expand_btn.click()
                    page.wait_for_timeout(1500)

                # 3. Extract Data
                curriculum_raw = page.locator('[data-purpose="course-curriculum"]').inner_text()
                clean_curriculum = clean_syllabus_text(curriculum_raw)

                audience_loc = page.locator('[data-purpose="target-audience"]')
                audience = audience_loc.inner_text() if audience_loc.count() > 0 else "N/A"

                description_loc = page.locator('[data-purpose="course-description"]')
                description = description_loc.inner_text() if description_loc.count() > 0 else "N/A"

                # 4. Save to File
                file_path = os.path.join(output_dir, f"{safe_name}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"COURSE: {course_title}\nURL: {url}\n\n")
                    f.write(f"--- TARGET AUDIENCE ---\n{audience}\n\n")
                    f.write(f"--- DESCRIPTION ---\n{description}\n\n")
                    f.write(f"--- CURRICULUM ---\n{clean_curriculum}")
                
                print(f"SUCCESS: Saved to {file_path}")

            except Exception as e:
                print(f"FAILED to process {url}: {e}")

        context.close()

if __name__ == "__main__":
    # Cleaned list of your URLs
    course_urls = [
        "https://azirotechnologies.udemy.com/course/llms-mastery-complete-guide-to-transformers-generative-ai/",
        "https://azirotechnologies.udemy.com/course/fastapi-the-complete-course/",
        "https://azirotechnologies.udemy.com/course/vector-databases-ai/",
        "https://azirotechnologies.udemy.com/course/vector-db/",
        "https://azirotechnologies.udemy.com/course/langchain/",
        "https://azirotechnologies.udemy.com/course/basic-to-advanced-retreival-augmented-generation-rag-course/",
        "https://azirotechnologies.udemy.com/course/hands-on-rag-with-langchain-build-real-world-projects/",
        "https://azirotechnologies.udemy.com/course/advanced-retrieval-augmented-generation/",
        "https://azirotechnologies.udemy.com/course/advanced-langchain-techniques-mastering-rag-applications/",
        "https://azirotechnologies.udemy.com/course/master-langchain-pinecone-openai-build-llm-applications/",
        "https://azirotechnologies.udemy.com/course/ollama-and-langchain/",
        "https://azirotechnologies.udemy.com/course/zero-to-hero-in-langchain/",
        "https://azirotechnologies.udemy.com/course/nlp-with-bert-in-python/",
        "https://azirotechnologies.udemy.com/course/langgraph-mastery-develop-llm-agents-with-langgraph/",
        "https://azirotechnologies.udemy.com/course/rag-llm-evaluation-ai-test/",
        "https://azirotechnologies.udemy.com/course/owasp-llm-security-learnit/"
    ]

    process_courses(course_urls, "your_email@aziro.com", "your_password")