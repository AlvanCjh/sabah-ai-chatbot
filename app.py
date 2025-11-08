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
    system_instruction="""You are 'Sabah-bot,' a friendly and expert travel planner for Sabah, Malaysia. 
    Your goal is to create a detailed, exciting, and practical day-by-day itinerary.
    Always ask clarifying questions one at a time until you have enough info.
    When you generate the final itinerary, format it *only* as a JSON object as requested.
    If you are just chatting or asking a question, just respond as plain text."""
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
        
        # --- This is where RAG would happen ---
        # 1. Search your sabah_knowledge for relevant info based on user_message
        # 2. Build a new, augmented prompt:
        #    augmented_prompt = f"""
        #    User message: "{user_message}"
        #    Here is some expert data about Sabah to help you answer:
        #    {relevant_sabah_data}
        #    """
        # For now, we'll just send the message directly
        
        # Send the message to the Gemini model
        # The 'chat' object automatically remembers the history
        response = chat.send_message(user_message)
        
        ai_message = response.text
        
        ai_message_cleaned = ai_message.strip() # Start by stripping whitespace

        # 1. Check if the AI wrapped its response in markdown
        if ai_message_cleaned.startswith("```json"):
            # 2. Remove the first line (```json) and last line (```)
            ai_message_cleaned = '\n'.join(ai_message_cleaned.split('\n')[1:-1])

        # Check if the response is JSON (our itinerary)
        try:
            # 3. Try to parse the CLEANED message
            itinerary_json = json.loads(ai_message_cleaned) 
            return jsonify({ "type": "itinerary", "data": itinerary_json })
        except json.JSONDecodeError:
            # It's just a regular text message (or the original message if not JSON)
            return jsonify({ "type": "text", "data": ai_message })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred"}), 500

# --- 4. RUN THE SERVER ---
if __name__ == '__main__':
    app.run(port=5000, debug=True) # Run on port 5000