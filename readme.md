# This project requires Python 3.11.

# Step 1 - Create a venv script 
- python -m venv venv

# Activating your script (Make sure your python interpretor is on Python 3.11 (venv))
- .\venv\Scripts\activate

# Step 2 - Install Relevant Packages
# Upgrade PIP if neccessary 
- python -m pip install --upgrade pip

# Packages
- pip install google-generativeai flask flask-cors python-dotenv

# Step 3 -API Key
- Create a file named .env in your project folder

# Use this format to put your API Key
- GOOGLE_API_KEY=Your_API_KEY

# Step 4 - Run the app
- python app.py

# Additional Info
- To stop running your app, ctrl + c in the terminal once you entered python app.py, and rerun the app using python app.py

- Your terminal will show that the server is running and listening on http://127.0.0.1:5000.
- Or go to your project folder and double-click the index.html file and open as live server
