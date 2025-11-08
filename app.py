from dotenv import load_dotenv
import os
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # To allow your frontend to call this
import json

# --- 1. SETUP ---
load_dotenv() # Load environment variables from .env

app = Flask(__name__, static_folder="")

CORS(app) # Allow cross-origin requests

# Configure the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Create the model instance
# We use Gemini 2.5* Pro for its larger context window and JSON mode
model = genai.GenerativeModel(
    'models/gemini-2.5-pro',
    # This is your "persona" from Step 4
    system_instruction="""You are 'Sabah-bot,' a friendly travel planner for Sabah, Malaysia.
    
    RULES:
    1. Always ask clarifying questions one at a time until you have enough info.
    2. When you have enough info, generate the itinerary.
    3. When you generate the final itinerary, you MUST format it *ONLY* as a JSON object. 
    4. **DO NOT** include *any* introductory text, markdown backticks (```json), or any other text outside of the JSON object itself. Your response MUST be *only* the valid JSON.
    
    JSON FORMAT TO FOLLOW:
    {
      "title": "Your 5-Day Sabah Adventure",
      "tripDetails": {
        "duration": "5 Days / 4 Nights",
        "travelerProfile": "Solo Traveler",
        "budget": "Mid-Range"
      },
      "days": [
        {
          "day": 1,
          "theme": "Arrival & City Exploration",
          "activities": [
            { "time": "Afternoon", "activity": "Arrive at Kota Kinabalu (KK)." },
            { "time": "Evening", "activity": "Dinner at the Night Market." }
          ]
        },
        {
          "day": 2,
          "theme": "Island Hopping",
          "activities": [
            { "time": "Morning", "activity": "Island hopping at Tunku Abdul Rahman Park." }
          ]
        }
      ]
    }
    """
)

# Start a new chat session (this will hold the memory)
chat = model.start_chat(history=[])

# --- 2. LOAD YOUR SABAH DATA (RAG) ---
# (In a real app, you'd do a smart vector search, but for now, we'll just load it)
# For simplicity, we'll just keep this in memory.
# In a real app, you would 'inject' this info into the prompt dynamically.
try:
    with open('sabah_data.json', 'r') as f:
        sabah_knowledge = json.load(f)
    # You would typically pass relevant parts of this to the prompt
    # e.g., "Use this list of attractions: [data]"
except FileNotFoundError:
    print("WARNING: sabah_data.json not found. AI will use general knowledge.")
    sabah_knowledge = {}

# --- Serve index.html ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')  # serve index.html from current folder   


# --- 3. CREATE THE API ENDPOINT ---
@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        user_message = request.json['message']
        
        # Send the message to the Gemini model
        response = chat.send_message(user_message)
        ai_message = response.text
        
        # --- New Robust JSON Extractor ---
        try:
            # Find the first '{' and the last '}'
            start_index = ai_message.find('{')
            end_index = ai_message.rfind('}')
            
            if start_index != -1 and end_index != -1 and end_index > start_index:
                # Extract the JSON string
                json_string = ai_message[start_index:end_index+1]
                # Try to parse it
                itinerary_json = json.loads(json_string)
                # If it parses, send it as an itinerary
                return jsonify({ "type": "itinerary", "data": itinerary_json })
            else:
                # If no JSON block is found, treat as text
                return jsonify({ "type": "text", "data": ai_message })
        
        except json.JSONDecodeError:
            # If it finds a block but can't parse it, treat as text
            return jsonify({ "type": "text", "data": ai_message })
        # --- End of New Parser ---

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred"}), 500

# --- 4. RUN THE SERVER ---
if __name__ == '__main__':
    app.run(port=5000, debug=True) # Run on port 5000