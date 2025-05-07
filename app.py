from flask import Flask, render_template, request, jsonify, session
from openai_client import OpenAIClient  # Utility class
from gpt2 import gpt_v2_interface
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session handling

# Initialize the OpenAI client once
OpenAIClient.initialize()

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["domain_modelling_copilot"]  # Database name
projects_collection = db["projects"]  # Collection name for projects

chat_history = []
scenarios = []  # Stores all scenarios generated during the chat session

@app.route("/")
def home():
    """Render the home page and reset chat history."""
    global chat_history
    chat_history = []  # Reset chat history on page load
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages and classify them as 'general' or 'scenario'."""
    global chat_history, scenarios
    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Message is required. Please enter a valid message."}), 400

        user_name = session.get("user_name")
        if not user_name:
            return jsonify({"error": "User name is not set. Please submit your name first."}), 400

        chat_history.append({"role": "user", "content": user_message})

        classification = classify_input(user_message)

        if classification == "general":
            response = generate_general(user_name, chat_history)
            return response
        elif classification == "scenario":
            detailed_description = generate_scenario(user_message)
            summary = generate_summary(detailed_description)
            scenarios.append(detailed_description)
            chat_history.append({"role": "assistant", "content": summary})
            return jsonify({"scenario": detailed_description, "summary": summary})
        else:
            return jsonify({"error": "Unable to classify the input. Please rephrase your query."}), 400

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@app.route("/submit_name", methods=["POST"])
def submit_name():
    """Store the user's name in the session."""
    try:
        user_name = request.json.get("name", "").strip()
        if not user_name:
            return jsonify({"error": "Name is required"}), 400

        session["user_name"] = user_name
        return jsonify({"message": "Name saved successfully!", "name": user_name})
    except Exception as e:
        print(f"Error storing name: {e}")
        return jsonify({"error": "An error occurred while storing the name"}), 500

def generate_general(user_name, chat_history):
    """Generate a general response using GPT."""
    try:
        prompts = [
            {"role": "system", "content": f"You are a helpful assistant. The user's name is {user_name}."}
        ] + chat_history

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        bot_reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": bot_reply})
        return jsonify({"response": bot_reply, "history": chat_history})
    except Exception as e:
        print(f"Error generating general response: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

def generate_scenario(scenario_text):
    """Generate a detailed scenario from the given user input."""
    try:
        prompts = [
            {
                "role": "system",
                "content": (
                    "You are an expert in domain modeling and UML class diagram generation. "
                    "Your task is to convert user inputs into clear and concise scenarios that include relevant entities, attributes, and relationships."
                    "Do not include Title, or any other unnecessary information in the output."
                )
            },
            {"role": "user", "content": f"Generate a clear and structured scenario for the following input:\n\n{scenario_text}"}
        ]

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating scenario: {e}")
        return "An error occurred while generating the scenario."

@app.route("/generate_uml", methods=["POST"])
def generate_uml():
    """Generate UML text from the given scenario text."""
    try:
        scenario_text = request.json.get("scenarioText", "").strip()
        if not scenario_text:
            return jsonify({"error": "Scenario text is required"}), 400

        client = OpenAIClient.get_client()
        plant_uml = gpt_v2_interface(scenario_text, client)
        return jsonify({"plantuml": plant_uml})
    except Exception as e:
        print(f"Error generating UML: {e}")
        return jsonify({"error": "An error occurred while generating the UML"}), 500

@app.route("/generate_summary", methods=["POST"])
def generate_summary_endpoint():
    """Generate a summary from the given detailed scenario."""
    try:
        detailed_description = request.json.get("detailed_description", "").strip()
        if not detailed_description:
            return jsonify({"error": "Detailed description is required"}), 400

        summary = generate_summary(detailed_description)
        return jsonify({"summary": summary})
    except Exception as e:
        print(f"Error generating summary: {e}")
        return jsonify({"error": "An error occurred while generating the summary"}), 500

def generate_summary(detailed_description):
    """Generate a summary from the given detailed scenario."""
    try:
        prompts = [
            {"role": "system", "content": "Summarize the following scenario in one or two sentences."},
            {"role": "user", "content": f"Summarize the following scenario:\n\n{detailed_description}"}
        ]

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "An error occurred while generating the summary."

def classify_input(user_message):
    """Classify the user input as 'general' or 'scenario'."""
    try:
        prompts = [
            {"role": "system", "content": "Classify the input as either 'general' or 'scenario'."},
            {"role": "user", "content": f"Input: {user_message}"}
        ]

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Error classifying input: {e}")
        return "general"  # Default to "general" in case of an error

@app.route("/get_scenarios", methods=["GET"])
def get_scenarios():
    """Retrieve all stored scenarios."""
    return jsonify({"scenarios": scenarios})

@app.route("/submit_to_database", methods=["POST"])
def submit_to_database():
    """Submit work results to MongoDB."""
    try:
        data = request.json
        project_name = data.get("project_name", "").strip()
        file_name = data.get("file_name", "").strip()
        username = data.get("username", "").strip()
        scenario = data.get("scenario", "").strip()
        plant_uml = data.get("plant_uml", "").strip()
        chat_history = data.get("chat_history", [])

        # Validate required fields
        if not project_name or not file_name:
            return jsonify({"error": "Project name and file name are required."}), 400

        # Check if the project exists
        project = projects_collection.find_one({"project_name": project_name})
        if not project:
            return jsonify({"error": "Project does not exist."}), 404

        # Check if the file exists in the project
        if file_name not in project.get("files", []):
            return jsonify({"error": "File does not exist in the selected project."}), 404

        # Prepare the document to insert
        work_data = {
            "project_name": project_name,
            "file_name": file_name,
            "username": username,
            "scenario": scenario,
            "plant_uml": plant_uml,
            "chat_history": chat_history,
        }

        # Insert into MongoDB
        result = projects_collection.insert_one(work_data)
        return jsonify({"message": "Work result saved successfully!", "id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error saving to database: {e}")
        return jsonify({"error": "An error occurred while saving to the database."}), 500

@app.route("/get_projects", methods=["GET"])
def get_projects():
    """Fetch the list of existing projects from the database."""
    try:
        # Fetch distinct project names from the database
        projects = projects_collection.distinct("project_name")
        return jsonify({"projects": projects})
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return jsonify({"error": "An error occurred while fetching projects."}), 500

@app.route("/create_project", methods=["POST"])
def create_project():
    """Create a new project in the database."""
    try:
        data = request.json
        project_name = data.get("project_name", "").strip()

        # Validate project name
        if not project_name:
            return jsonify({"error": "Project name is required."}), 400

        # Check if the project already exists
        existing_project = projects_collection.find_one({"project_name": project_name})
        if existing_project:
            return jsonify({"error": "Project already exists."}), 400

        # Insert the new project into the database
        projects_collection.insert_one({"project_name": project_name, "files": []})
        return jsonify({"message": "Project created successfully!"})
    except Exception as e:
        print(f"Error creating project: {e}")
        return jsonify({"error": "An error occurred while creating the project."}), 500

@app.route("/create_file", methods=["POST"])
def create_file():
    """Create a new file in the selected project."""
    try:
        data = request.json
        project_name = data.get("project_name", "").strip()
        file_name = data.get("file_name", "").strip()

        # Validate inputs
        if not project_name or not file_name:
            return jsonify({"error": "Project name and file name are required."}), 400

        # Check if the project exists
        project = projects_collection.find_one({"project_name": project_name})
        if not project:
            return jsonify({"error": "Project does not exist."}), 404

        # Check if the file already exists in the project
        if file_name in project.get("files", []):
            return jsonify({"error": "File already exists in this project."}), 400

        # Add the file to the project's file list
        projects_collection.update_one(
            {"project_name": project_name},
            {"$push": {"files": file_name}}
        )
        return jsonify({"message": "File created successfully!"})
    except Exception as e:
        print(f"Error creating file: {e}")
        return jsonify({"error": "An error occurred while creating the file."}), 500

@app.route("/get_files", methods=["GET"])
def get_files():
    """Fetch the list of files for a selected project."""
    try:
        project_name = request.args.get("project_name", "").strip()

        # Validate project name
        if not project_name:
            return jsonify({"error": "Project name is required."}), 400

        # Fetch the project from the database
        project = projects_collection.find_one({"project_name": project_name})
        if not project:
            return jsonify({"error": "Project does not exist."}), 404

        # Return the list of files
        return jsonify({"files": project.get("files", [])})
    except Exception as e:
        print(f"Error fetching files: {e}")
        return jsonify({"error": "An error occurred while fetching files."}), 500

if __name__ == "__main__":
    app.run(debug=True)