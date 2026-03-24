import os
import json
import yaml
import time
from google import genai

# --- CONFIGURATION ---
INPUT_DIR = "AI-ML RAG-Gen"
OUTPUT_DIR = "Assessments_YAML"
# Ensure your GOOGLE_API_KEY is set in your environment variables
# or pass it directly to the client: client = genai.Client(api_key="YOUR_KEY")
client = genai.Client(api_key="AIzaSyA1hC1qil5jKSvDfkYbf9XPfeEr_fr9wBE") 

def sanitize_json_response(raw_text):
    """Removes markdown code blocks if the LLM includes them."""
    clean_text = raw_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    return clean_text.strip()

def process_all_courses():
    # 1. Setup Output Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    # 2. Get list of all .txt files from the scraper
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    
    if not files:
        print(f"No text files found in {INPUT_DIR}. Run the extractor first!")
        return

    print(f"Found {len(files)} courses to process.")

    for filename in files:
        course_name = os.path.splitext(filename)[0]
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, f"{course_name}.yaml")

        # Skip if already processed (optional, saves API costs on retry)
        if os.path.exists(output_path):
            print(f"Skipping {course_name} (YAML already exists).")
            continue

        print(f"\n--- Generating Questions for: {course_name} ---")
        
        with open(input_path, "r", encoding="utf-8") as f:
            course_content = f.read()

        # 3. Design the Final Prompt
        prompt = f"""
        Act as a Senior AI Architect and Course Creator.
        Based strictly on the following course details, generate exactly 50 unique Multiple Choice Questions (MCQs).

        **Target Persona:** Software Engineers / Data Scientists with 3-7 years of experience.
        **Question Style:** Highly technical. Avoid "what is" questions. Focus on implementation details, architectural trade-offs, debugging scenarios, and best practices mentioned in the curriculum.
        
        **Constraints:**
        - Exactly 50 questions.
        - Exactly 4 relevant options (A, B, C, D) per question. 
        - Options must be technical and plausible (no obvious 'wrong' answers).
        - Ensure a diverse spread across the entire syllabus.
        - Difficulty: Intermediate to Advanced.

        **Syllabus & Context:**
        {course_content}

        **STRICT OUTPUT FORMAT:**
        Output ONLY a valid JSON array of objects. No intro, no markdown blocks, no chatter.
        Structure:
        [
          {{
            "id": 1,
            "question": "Scenario-based question text?",
            "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
            "correct_answer": "B"
          }}
        ]
        """

        try:
            # Using Gemini 1.5 Flash for the best balance of speed and 50-item output length
            response = client.models.generate_content(
                model='gemma-3-27b-it', 
                contents=prompt
            )

            # 4. Clean and Parse JSON
            raw_json = sanitize_json_response(response.text)
            questions_list = json.loads(raw_json)

            # 5. Save as YAML
            with open(output_path, "w", encoding="utf-8") as yf:
                yaml.dump(questions_list, yf, sort_keys=False, default_flow_style=False, allow_unicode=True)
            
            print(f"SUCCESS: Generated {len(questions_list)} questions in {output_path}")

            # 6. Safety Throttle (prevents hitting rate limits if you have many courses)
            time.sleep(2) 

        except Exception as e:
            print(f"ERROR processing {course_name}: {e}")

if __name__ == "__main__":
    start_time = time.time()
    process_all_courses()
    duration = (time.time() - start_time) / 60
    print(f"\nBatch processing complete! Total time: {duration:.2f} minutes.")