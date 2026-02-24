import json
import yaml
import os
from google import genai 

def generate_assessments(content_file_path="extracted_content.txt", output_yaml_path="assessments.yaml"):
    # Read the extracted Udemy data
    with open(content_file_path, "r", encoding="utf-8") as f:
        course_context = f.read()

    # Highly specific prompt tailored to your L&D requirements
    prompt = f"""
    Act as an Expert Technical Assessor and Senior Software Engineering Interviewer.
    Based strictly on the provided course curriculum and target audience description, generate exactly 50 unique Multiple Choice Questions (MCQs).

    **Constraints & Guidelines:**
    1. **Target Audience:** The questions must be tailored for software engineers with 3 to 7 years of experience. Do not ask trivial "what does this acronym mean" questions. Focus on implementation, architecture tradeoffs, debugging, and advanced workflows specific to the syllabus.
    2. **Strict Adherence:** Formulate questions ONLY based on the topics mentioned in the syllabus. No deviations.
    3. **Options:** - Provide exactly 4 options (A, B, C, D).
       - Options must be plausible, highly relevant, and not glaringly obvious. 
       - Do not use "All of the above" or "None of the above".
    4. **Diversity:** Ensure questions cover the breadth of the entire syllabus evenly. Include a mix of conceptual, scenario-based, and troubleshooting questions.
    5. **Uniqueness:** All 50 questions must be completely unique. No repetitive concepts.

    **Course Context (Syllabus & Audience):**
    {course_context}

    **STRICT OUTPUT FORMAT:**
    You must output ONLY a valid JSON array of objects. Do not include any markdown formatting (like ```json), introductory text, or explanations. Just the raw JSON array.
    
    Follow this exact JSON structure:
    [
      {{
        "id": "q1_topic_name",
        "question": "The scenario-based question text goes here?",
        "options": {{
          "A": "Plausible but incorrect option",
          "B": "The correct technical approach",
          "C": "Common misconception option",
          "D": "Another plausible but incorrect option"
        }},
        "correct_answer": "B"
      }}
    ]
    """

    print("Sending prompt to LLM... (This may take a minute for 50 complex questions)")
    
    # Initialize your client (ensure your API key is set in your environment variables)
    client = genai.Client()
    
    try:
        response = client.models.generate_content(
            model='', # Use a highly capable model for complex formatting and 50 items
            contents=prompt
        )
        
        raw_output = response.text.strip()
        
        # Clean up in case the LLM ignores the rule and wraps in markdown anyway
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
            
        # Parse the JSON
        qa_data = json.loads(raw_output.strip())
        
        # Validate we got 50 questions
        print(f"Successfully generated {len(qa_data)} questions.")

        # Save to YAML
        with open(output_yaml_path, "w", encoding="utf-8") as yaml_file:
            yaml.dump(qa_data, yaml_file, sort_keys=False, default_flow_style=False, allow_unicode=True)
            
        print(f"Assessments saved successfully to {output_yaml_path}")

    except json.JSONDecodeError as e:
        print("Failed to parse the LLM output as JSON. The model may have included conversational text.")
        print(f"Raw output was:\n{raw_output}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_assessments()