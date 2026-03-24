import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
COURSE_URL = "https://www.udemy.com/course/complete-linux-training-course-to-get-your-dream-it-job/"
ROOT_DIR   = "Q_GEN"
SYLLABUS_DIR = os.path.join(ROOT_DIR, "Syllabus")
OUTPUT_FILE  = os.path.join(SYLLABUS_DIR, "syllabus.txt")

os.makedirs(SYLLABUS_DIR, exist_ok=True)
print("✔  Folders ready →", SYLLABUS_DIR)

# ─────────────────────────────────────────────
# BROWSER SETUP
# ─────────────────────────────────────────────
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# Suppress DevTools / USB noise in console
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--log-level=3")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

print("🌐  Opening course page …")
driver.get(COURSE_URL)

# Wait until the curriculum accordion is present
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-purpose='curriculum-section-container']")
        )
    )
    print("✔  Curriculum container detected.")
except Exception:
    print("⚠   Curriculum container not found via data-purpose; continuing anyway …")
    time.sleep(8)

# ─────────────────────────────────────────────
# EXPAND ALL CURRICULUM SECTIONS
# ─────────────────────────────────────────────
print("🔽  Expanding all syllabus sections …")

def expand_all(driver):
    """Click every 'Expand' button until none are left."""
    max_passes = 10
    for attempt in range(max_passes):
        # Udemy-specific expand buttons
        selectors = [
            "button[data-purpose='expand-toggle']",
            "button.section--section-title--Vm-Mi",
            "button[aria-expanded='false']",
        ]
        clicked = 0
        for sel in selectors:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            for btn in btns:
                try:
                    aria = btn.get_attribute("aria-expanded")
                    if aria == "false" or "Expand" in (btn.text or ""):
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        driver.execute_script("arguments[0].click();", btn)
                        clicked += 1
                except Exception:
                    pass

        # Fallback: any button containing "Expand" in its visible text
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        for btn in all_btns:
            try:
                if "Expand" in (btn.text or ""):
                    driver.execute_script("arguments[0].click();", btn)
                    clicked += 1
            except Exception:
                pass

        if clicked == 0:
            break
        time.sleep(1.5)

expand_all(driver)
time.sleep(2)
print("✔  Sections expanded.")

# ─────────────────────────────────────────────
# EXTRACT CURRICULUM DATA  (targeted selectors)
# ─────────────────────────────────────────────
print("📋  Extracting syllabus …")

# ── Selector priority list (Udemy updates class names periodically) ──────────
SECTION_SELECTORS = [
    "[data-purpose='curriculum-section-container']",
    ".section--section--2UYQU",
    ".curriculum-section",
    "div[class*='section--section']",
]

SECTION_TITLE_SELECTORS = [
    "[data-purpose='section-title']",
    "span[class*='section--section-title']",
    "h3[class*='section--title']",
    "div[class*='section-title']",
    "button[class*='section'] span",
    "span[class*='title']",
]

LECTURE_SELECTORS = [
    "[data-purpose='curriculum-item-title-text']",
    "span[class*='lecture--item-content-title']",
    "span[class*='item-title']",
    "div[class*='item--container'] span",
    "li[class*='curriculum-item'] span[class*='title']",
]

def try_selectors(parent, selectors):
    """Try a list of CSS selectors on a parent element; return first hit(s)."""
    for sel in selectors:
        els = parent.find_elements(By.CSS_SELECTOR, sel)
        if els:
            return els
    return []

def clean_text(raw: str) -> str:
    """Strip timing artifacts like '• 04:32' or '(00:05:30)' from lecture names."""
    text = raw.strip()
    text = re.sub(r"•\s*\d+:\d+", "", text)         # • 04:32
    text = re.sub(r"\(\d{1,2}:\d{2}(:\d{2})?\)", "", text)  # (4:32) or (00:04:32)
    text = re.sub(r"\d{1,2}:\d{2}(:\d{2})?$", "", text)     # trailing timestamp
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

NOISE = re.compile(
    r"^("
    r"preview|quiz|test|students|ratings?|english|updated|bestseller|"
    r"total\s+length|lectures?|questions?|sections?|resources?|"
    r"\d+\s*(min|hr|lecture|section|quiz|question)"
    r")",
    re.IGNORECASE,
)

def is_noise(text: str) -> bool:
    return bool(NOISE.match(text)) or len(text) < 3

# ── Try structured approach first ────────────────────────────────────────────
structured_results = []

for sec_sel in SECTION_SELECTORS:
    sections = driver.find_elements(By.CSS_SELECTOR, sec_sel)
    if sections:
        print(f"   ✔  Found {len(sections)} section containers via '{sec_sel}'")
        for sec in sections:
            # Get section/module title
            title_els = try_selectors(sec, SECTION_TITLE_SELECTORS)
            section_title = ""
            for tel in title_els:
                t = clean_text(tel.text)
                if t and not is_noise(t) and len(t) > 4:
                    section_title = t
                    break

            # Get lectures in this section
            lecture_els = try_selectors(sec, LECTURE_SELECTORS)
            lectures = []
            for lel in lecture_els:
                t = clean_text(lel.text)
                if t and not is_noise(t) and len(t) > 2:
                    lectures.append(t)
            lectures = list(dict.fromkeys(lectures))  # dedupe

            if section_title or lectures:
                structured_results.append((section_title, lectures))

        break  # stop trying selectors once we found sections

# ── Fallback: full-page text heuristic ───────────────────────────────────────
fallback_results = []

if not structured_results:
    print("   ⚠   Structured selectors found nothing; using heuristic fallback …")

    all_spans = driver.find_elements(By.CSS_SELECTOR, "span, li, h3")
    raw_lines = []
    for el in all_spans:
        t = clean_text(el.text)
        if 3 < len(t) < 160 and not is_noise(t):
            raw_lines.append(t)
    raw_lines = list(dict.fromkeys(raw_lines))

    MODULE_RE = re.compile(
        r"(module|section|chapter|part|week|lesson)\s*\d+|"
        r"^\d+\s*[.:\-]\s*[A-Z]",
        re.IGNORECASE,
    )

    current_module = None
    current_lectures = []

    for line in raw_lines:
        if MODULE_RE.search(line):
            if current_module is not None:
                fallback_results.append((current_module, current_lectures))
            current_module = line
            current_lectures = []
        elif current_module is not None and len(line.split()) <= 15:
            current_lectures.append(line)

    if current_module:
        fallback_results.append((current_module, current_lectures))

driver.quit()
print("✔  Browser closed.")

# ─────────────────────────────────────────────
# BUILD CLEAN OUTPUT
# ─────────────────────────────────────────────
results = structured_results if structured_results else fallback_results

if not results:
    print("❌  No content extracted. The page structure may have changed.")
    print("    Try running with headful mode and inspecting the HTML manually.")
    exit(1)

lines = []
for idx, (module_title, lectures) in enumerate(results, start=1):
    # Normalise the module heading
    if module_title:
        # If it already starts with "Module N", keep it; otherwise add prefix
        if re.match(r"(module|section|chapter)\s*\d+", module_title, re.IGNORECASE):
            heading = module_title
        else:
            heading = f"Module {idx} - {module_title}"
    else:
        heading = f"Module {idx}"

    lines.append(heading)

    seen = set()
    for lec in lectures:
        if lec.lower() not in seen and lec.lower() != heading.lower():
            lines.append(f"    {lec}")
            seen.add(lec.lower())

    lines.append("")  # blank line between modules

# Strip trailing blank lines
while lines and lines[-1] == "":
    lines.pop()

output_text = "\n".join(lines)

# ─────────────────────────────────────────────
# SAVE TO FILE
# ─────────────────────────────────────────────
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(output_text)

print("\n" + "═" * 55)
print(f"✅  Syllabus saved → {OUTPUT_FILE}")
print(f"    Modules extracted : {len(results)}")
total_lecs = sum(len(l) for _, l in results)
print(f"    Lectures extracted: {total_lecs}")
print("═" * 55)
print("\n── Preview (first 30 lines) ──────────────────────────")
for line in output_text.splitlines()[:30]:
    print(line)
print("…")