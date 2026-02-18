import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# -----------------------------
# Configuration
# -----------------------------
COURSE_URL = "https://www.udemy.com/course/complete-linux-training-course-to-get-your-dream-it-job/"

ROOT_DIR = "Q_GEN"
SYLLABUS_DIR = os.path.join(ROOT_DIR, "Syllabus")
OUTPUT_FILE = os.path.join(SYLLABUS_DIR, "syllabus.txt")

# Ensure folders exist
os.makedirs(SYLLABUS_DIR, exist_ok=True)

print("Folders ready...")

# -----------------------------
# Launch Browser
# -----------------------------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

print("Opening course page...")
driver.get(COURSE_URL)

time.sleep(8)

# -----------------------------
# Expand curriculum
# -----------------------------
print("Expanding syllabus sections...")

buttons = driver.find_elements(By.TAG_NAME, "button")
for btn in buttons:
    try:
        if "Expand" in btn.text:
            driver.execute_script("arguments[0].click();", btn)
    except:
        pass

time.sleep(3)

# -----------------------------
# Extract Raw Text
# -----------------------------
print("Extracting syllabus...")

elements = driver.find_elements(By.CSS_SELECTOR, "span, div")

raw_data = []
for el in elements:
    text = el.text.strip()
    if 3 < len(text) < 150:
        raw_data.append(text)

driver.quit()

# Remove duplicates
raw_data = list(dict.fromkeys(raw_data))

# -----------------------------
# Clean & Filter Content
# -----------------------------

cleaned_syllabus = []
current_module_found = False

for line in raw_data:

    # Detect module titles
    if re.match(r"Module\s*\d+", line, re.IGNORECASE):
        cleaned_syllabus.append(line)
        current_module_found = True
        continue

    # Ignore noise
    noise_words = [
        "Preview", "min", "students", "ratings",
        "English", "updated", "Role Play",
        "total length", "lectures", "Bestseller"
    ]

    if any(word.lower() in line.lower() for word in noise_words):
        continue

    # Accept lecture titles only after module detected
    if current_module_found and len(line.split()) <= 10:
        cleaned_syllabus.append(f"    {line}")

# Remove duplicates again
cleaned_syllabus = list(dict.fromkeys(cleaned_syllabus))

# -----------------------------
# Save Clean File
# -----------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(cleaned_syllabus))

print("\nClean syllabus saved to:", OUTPUT_FILE)
