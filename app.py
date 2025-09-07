from flask import Flask, render_template, request, jsonify
import os
import re
import json
import traceback
import logging
from datetime import datetime
import google.generativeai as genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize Gemini client
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    logging.error(f"Failed to initialize Gemini client: {e}")
    client = None

# Professional infographic generation prompt
NAPKIN_PROMPT = """
You are a professional infographic designer creating business-quality visual diagrams.

Analyze the input content and create a structured visual story. Return valid JSON with this schema:

{
  "title": "string",
  "layout": "process_flow | concept_map | hierarchy | comparison",
  "visual_flow": "top_to_bottom | left_to_right | center_radial | layered",
  "sections": [
    {
      "role": "main_concept | supporting_point | process_step | conclusion | connector",
      "text": "string",
      "color": "blue | green | orange | red | purple | teal",
      "emphasis": "primary | secondary | tertiary",
      "visual_weight": "heavy | medium | light"
    }
  ]
}

CRITICAL DESIGN PRINCIPLES:
1. CREATE VISUAL HIERARCHY: One primary element, 2-4 secondary elements maximum for clean layouts
2. LOGICAL FLOW: Elements should connect meaningfully (cause→effect, step→step, concept→example)
3. CONTENT ANALYSIS: 
   - Process/workflow → "process_flow" layout with sequential steps
   - Multiple concepts → "concept_map" with central theme (MAX 5 sections total)
   - Rankings/levels → "hierarchy" with clear top-down structure
   - Comparisons → "comparison" with balanced sides

LAYOUT CONSTRAINTS:
- concept_map: Use ONLY for 3-5 sections maximum to prevent overlap
- process_flow: Ideal for sequential steps
- hierarchy: Best for 6+ sections with clear levels

4. ROLE ASSIGNMENT:
   - "main_concept": The core idea (1 per infographic)
   - "process_step": Sequential elements in order
   - "supporting_point": Details that support the main concept
   - "conclusion": Final outcome or result
   - "connector": Transition phrases or arrows

5. VISUAL WEIGHT:
   - "heavy": Most important element (largest, central)
   - "medium": Secondary importance (medium size)
   - "light": Supporting details (smaller, peripheral)

6. EMPHASIS LEVELS:
   - "primary": Main focus of the infographic
   - "secondary": Key supporting elements  
   - "tertiary": Additional context/details

Return ONLY valid JSON. Analyze content deeply to create meaningful visual structure.
"""

LOGFILE = "ai_output.log"

def log_raw(user_text: str, raw_output: str, note: str = ""):
    """Log the raw API interaction for debugging"""
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write("\n==== " + str(datetime.now()) + " ====\n")
            if note:
                f.write("NOTE: " + note + "\n")
            f.write("USER INPUT:\n" + user_text + "\n")
            f.write("RAW OUTPUT:\n" + raw_output + "\n")
    except Exception as e:
        logging.error(f"Failed to write to log file: {e}")

def safe_clean(raw: str) -> str:
    """Clean and extract JSON from potentially malformed response"""
    # Remove code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()
    
    # Find first complete JSON object
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1:
        return cleaned[first:last+1]
    return cleaned

def convert_to_professional_schema(parsed_data):
    """Convert old schema format to new professional schema format"""
    
    # If already in new format, return as-is
    if "visual_flow" in parsed_data or (parsed_data.get("sections") and 
                                       any("role" in section for section in parsed_data["sections"])):
        return parsed_data
    
    # Convert old format to new format
    title = parsed_data.get("title", "PROFESSIONAL INFOGRAPHIC")
    old_sections = parsed_data.get("sections", [])
    
    # Determine layout based on old section types
    layout = "process_flow"
    visual_flow = "top_to_bottom"
    
    # Analyze old sections to determine best layout
    section_types = [section.get("type", "") for section in old_sections]
    if "arrow" in section_types:
        layout = "process_flow"
        visual_flow = "left_to_right" if len(old_sections) <= 4 else "top_to_bottom"
    elif any("list" in stype for stype in section_types):
        layout = "concept_map"
    elif len(old_sections) > 4:
        layout = "hierarchy"
    
    # Convert sections to new format
    new_sections = []
    for i, section in enumerate(old_sections):
        old_type = section.get("type", "box")
        
        # Determine role based on old type and position
        if old_type in ["box", "icon_box"] and i == 0:
            role = "main_concept"
            emphasis = "primary"
            visual_weight = "heavy"
        elif old_type in ["arrow", "connector"]:
            role = "connector"
            emphasis = "tertiary"
            visual_weight = "light"
        elif old_type in ["process", "list"]:
            role = "process_step"
            emphasis = "secondary"
            visual_weight = "medium"
        else:
            role = "supporting_point"
            emphasis = "secondary"
            visual_weight = "medium"
        
        new_section = {
            "role": role,
            "text": section.get("text", ""),
            "color": section.get("color", "blue"),
            "emphasis": emphasis,
            "visual_weight": visual_weight
        }
        new_sections.append(new_section)
    
    return {
        "title": title,
        "layout": layout,
        "visual_flow": visual_flow,
        "sections": new_sections
    }

def fallback_from_text(user_text: str):
    """Generate a fallback professional infographic when API fails"""
    # Split text into sentences
    sentences = [s.strip() for s in re.split(r'[.\n!?]\s*', user_text) if s.strip()]
    
    # Generate title from first sentence or first 40 characters
    title = (sentences[0][:40] if sentences else user_text[:40]).upper()
    if not title:
        title = "PROFESSIONAL INFOGRAPHIC"
    
    # Determine layout based on content characteristics
    layout = "process_flow"
    visual_flow = "top_to_bottom"
    
    if any(word in user_text.lower() for word in ['vs', 'versus', 'compare', 'comparison', 'difference']):
        layout = "comparison"
    elif any(word in user_text.lower() for word in ['hierarchy', 'priority', 'level', 'rank', 'tier']):
        layout = "hierarchy"
    elif any(word in user_text.lower() for word in ['concept', 'idea', 'central', 'core', 'main']):
        layout = "concept_map"
    
    sections = []
    colors = ["blue", "green", "orange", "red", "purple", "teal"]
    
    # Create sections with proper roles and emphasis
    if sentences:
        # First sentence as main concept with primary emphasis
        sections.append({
            "role": "main_concept",
            "text": sentences[0][:120], 
            "color": colors[0],
            "emphasis": "primary",
            "visual_weight": "heavy"
        })
    
    if len(sentences) > 1:
        # Remaining sentences as supporting points or process steps
        for i, sentence in enumerate(sentences[1:5], 1):
            role = "process_step" if layout == "process_flow" else "supporting_point"
            sections.append({
                "role": role,
                "text": sentence[:100], 
                "color": colors[i % len(colors)],
                "emphasis": "secondary",
                "visual_weight": "medium"
            })
    
    # Ensure at least one section exists
    if not sections:
        sections.append({
            "role": "main_concept",
            "text": user_text[:120] if user_text else "No meaningful content found.", 
            "color": "blue",
            "emphasis": "primary",
            "visual_weight": "heavy"
        })
    
    return {
        "title": title,
        "layout": layout,
        "visual_flow": visual_flow,
        "sections": sections,
        "note": "LOCAL FALLBACK - API unavailable"
    }

@app.route("/")
def home():
    """Serve the main application page"""
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    """Generate napkin infographic from text input"""
    try:
        # Get and validate input
        data = request.get_json()
        if not data:
            return jsonify({
                "title": "ERROR",
                "sections": [{"type": "box", "text": "No data received.", "color": "red"}]
            })
        
        user_text = data.get("text", "").strip()
        if not user_text:
            return jsonify({
                "title": "ERROR",
                "sections": [{"type": "box", "text": "No input provided.", "color": "red"}]
            })
        
        # Try to generate with Gemini API
        if client:
            try:
                # Try gemini-2.5-flash first
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=NAPKIN_PROMPT + "\n\n" + user_text,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    raw = response.text or ""
                    source = "gemini-2.5-flash"
                except Exception as flash_error:
                    logging.warning(f"Flash model failed: {flash_error}")
                    # Fallback to gemini-2.5-pro
                    response = client.models.generate_content(
                        model="gemini-2.5-pro",
                        contents=NAPKIN_PROMPT + "\n\n" + user_text,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    raw = response.text or ""
                    source = "gemini-2.5-pro"
                
                log_raw(user_text, raw, note=f"Used {source}")
                
                # Clean and parse JSON
                cleaned = safe_clean(raw)
                parsed = json.loads(cleaned)
                
                # Validate required fields
                if "title" not in parsed or "sections" not in parsed:
                    raise ValueError("Invalid JSON schema - missing required fields")
                
                # Convert old schema to new professional schema if needed
                converted_result = convert_to_professional_schema(parsed)
                
                return jsonify(converted_result)
                
            except json.JSONDecodeError as json_error:
                logging.error(f"JSON parsing failed: {json_error}")
                log_raw(user_text, f"JSON Error: {str(json_error)}", note="JSON_PARSE_FALLBACK")
            except Exception as api_error:
                logging.error(f"API call failed: {api_error}")
                log_raw(user_text, f"API Error: {str(api_error)}", note="API_FALLBACK")
        
        # Use fallback generator
        logging.info("Using fallback generator")
        fallback_result = fallback_from_text(user_text)
        log_raw(user_text, json.dumps(fallback_result), note="FALLBACK_USED")
        return jsonify(fallback_result)
        
    except Exception as e:
        # Final error handler
        error_traceback = traceback.format_exc()
        logging.error(f"Unexpected error in generate: {e}\n{error_traceback}")
        
        try:
            log_raw(request.get_json().get("text", ""), f"Fatal Error: {str(e)}\n{error_traceback}", note="FATAL_ERROR")
        except:
            pass
        
        return jsonify({
            "title": "SYSTEM ERROR",
            "sections": [
                {"type": "box", "text": "An unexpected error occurred.", "color": "red"},
                {"type": "box", "text": "Please try again or contact support.", "color": "orange"}
            ],
            "note": "SYSTEM_ERROR"
        })

if __name__ == "__main__":
    print("🚀 Napkin.ai Clone running at http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
