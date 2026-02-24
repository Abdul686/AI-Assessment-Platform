import os
import json
import time
from google import genai
from dotenv import load_dotenv

# 1. Load API Key
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. The Raw Syllabus Data
SYLLABUS_CONTENT = """Course name: Complete Python with AI Skills to Get Your Dream IT Job
Master Python for Data Science, AI, Machine Learning, Web Development, Game Development, Cybersecurity, and GUI!
53 sections • 361 lectures • 40h 32m total length

Introduction: Course Overview, What is a Computer Language?, Types of Programming Languages, What is Object Oriented Programming?, Programming Applications Examples, Programmer vs. Developer, History of Python, Importance of Python, What Can I Build Using Python?, How to Succeed as a Python Developer.

Development Environment Setup: Lab Design, Software Tools, Installation of Python on Windows/Linux, Installation of PyCharm on Windows/Linux, Online Python Practice Tool.

Implementing Python Programming Basics: Programming using Notepad, Introduction to IDE, Python's Syntax and Structure, Basic Input and Output Operations, Code Comments, Code Errors and Debugging Basics, Python Style Guide (PEP 8), Navigating Interactive Shell.

Variables & Data: Variables, Constants, Naming Conventions, Assigning Multiple Values, Memory Management, Displaying Output, Basic Math, Global vs. Local Variables. Built-in Data Types, Type Conversion, Strings, String Slicing, Escape Characters, Substrings, Regular Expressions.

Logic & Flowcharts: Flowcharts, Symbols, Flow direction, Converting Flowcharts to Python Code, Decision Making, Pseudocode.

Operators: Assignment, Conditional (if-else), Comparison, Logical, Identity, Membership, Ternary.

AI Tools: ChatGPT in Python, Generating Programs, Debugging. Copilots, Paid vs Free, Setting Up Copilot, Generating Code from English, Fixing Syntax Errors, Copilot Chat.

Conditional Statements: if-elif-else Ladder, Nested Conditional Statements."""

# 3. Step 1: Store syllabus in a text file
def create_syllabus_file(filename="udemy_syllabus.txt"):
    print(f"---  Step 1: Saving syllabus to {filename} ---")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(SYLLABUS_CONTENT)
    return filename

# 4. Clean JSON helper (removes markdown block ticks if AI adds them)
def clean_json(raw_text):
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# 5. Step 2 & 3: Generate MCQs in batches and save to JSON
def generate_mcqs(syllabus_file):
    with open(syllabus_file, "r", encoding="utf-8") as f:
        syllabus = f.read()

    total_questions = 200
    batch_size = 50
    batches = total_questions // batch_size
    all_mcqs = []

    print(f"\n---  Step 2: Generating {total_questions} MCQs in {batches} batches ---")
    print("Using model: gemma-3-27b-it")

    for i in range(batches):
        print(f"Processing Batch {i+1} of {batches} (Questions {i*batch_size + 1} to {(i+1)*batch_size})...")
        
        prompt = f"""
        Act as an Expert Python Instructor and Course Creator.
        Based strictly on the following course syllabus, generate {batch_size} unique Multiple Choice Questions (MCQs).
        
        **Batch Constraint:** Ensure these {batch_size} questions are diverse and cover random parts of the syllabus so we get broad coverage.
        **Difficulty:** Mix of Beginner and Intermediate.

        **Syllabus:**
        {syllabus}

        **STRICT OUTPUT FORMAT:**
        You must output ONLY a valid JSON array of objects. Do not include any introductory text, markdown formatting, or explanations. Just the raw JSON.
        
        Follow this exact JSON structure:
        [
          {{
            "id": "generate_a_unique_number",
            "question": "The question text goes here?",
            "options": {{
              "A": "Option 1",
              "B": "Option 2",
              "C": "Option 3",
              "D": "Option 4"
            }},
            "correct_answer": "A"
          }}
        ]
        """

        try:
            response = client.models.generate_content(
                model='gemma-3-27b-it',
                contents=prompt
            )
            
            # Clean and parse the JSON string into a Python list
            clean_text = clean_json(response.text)
            batch_data = json.loads(clean_text)
            all_mcqs.extend(batch_data)
            
            print(f" Batch {i+1} successful! Retrieved {len(batch_data)} questions.")
            
            # Pause briefly to respect free-tier rate limits (15 requests per minute)
            time.sleep(3) 

        except json.JSONDecodeError:
            print(f" Error decoding JSON on Batch {i+1}. The AI format broke.")
        except Exception as e:
            print(f" API Error on Batch {i+1}: {e}")

    # Step 3: Save to JSON file
    output_filename = "udemy_course_mcqs.json"
    print(f"\n---  Step 3: Saving all questions to {output_filename} ---")
    
    # Update IDs to be perfectly sequential from 1 to 200
    for idx, q in enumerate(all_mcqs):
        q["id"] = idx + 1

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_mcqs, f, indent=4)
        
    print(f" Success! {len(all_mcqs)} questions successfully saved to {output_filename}.")

if __name__ == "__main__":
    txt_file = create_syllabus_file()
    generate_mcqs(txt_file)