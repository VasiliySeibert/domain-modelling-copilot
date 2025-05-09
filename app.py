from flask import Flask, render_template, request, jsonify, session
from models.user import User
from models.chatbot import Chatbot
from models.llm_wrapper import LLMWrapper
from models.project_manager import ProjectManager
from gpt2 import gpt_v2_interface
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session handling

# Singleton instances for the application
_user_instance = None
_chatbot_instance = None
_llm_wrapper_instance = None
_project_manager_instance = None

# Store scenarios across requests
scenarios = []

def get_user(name=None):
    """Get or create a User instance."""
    global _user_instance
    if _user_instance is None:
        _user_instance = User(name)
    elif name and _user_instance.name != name:
        _user_instance.name = name
    return _user_instance

def get_chatbot():
    """Get or create a Chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = Chatbot()
    return _chatbot_instance

def get_llm_wrapper():
    """Get or create an LLMWrapper instance."""
    global _llm_wrapper_instance
    if _llm_wrapper_instance is None:
        _llm_wrapper_instance = LLMWrapper()
    return _llm_wrapper_instance

def get_project_manager():
    """Get or create a ProjectManager instance."""
    global _project_manager_instance
    if _project_manager_instance is None:
        _project_manager_instance = ProjectManager()
    return _project_manager_instance

def reset_instances():
    """Reset all instances."""
    global _user_instance, _chatbot_instance, _llm_wrapper_instance
    _user_instance = None
    _chatbot_instance = None
    _llm_wrapper_instance = None
    # We don't reset the project manager as it's stateless and maintains DB connections

@app.route("/")
def home():
    """Render the home page and reset chat history."""
    # Reset instances for new session
    reset_instances()
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Process user input according to activity diagram flow."""
    global scenarios
    try:
        # Get instances
        user = get_user(session.get("user_name"))
        chatbot = get_chatbot()
        llm_wrapper = get_llm_wrapper()
        
        raw_input = request.json.get("message", "").strip()
        if not raw_input:
            return jsonify({"error": "Message is required. Please enter a valid message."}), 400

        user_name = session.get("user_name")
        if not user_name:
            return jsonify({"error": "User name is not set. Please submit your name first."}), 400
        
        user_input = user.provides_input(raw_input)
        
        chatbot.display_input(user_input)
        
        llm_wrapper.add_to_chat_history("user", user_input)
        
        input_type = llm_wrapper.determine_input_type(user_input)

        if input_type == "general_type":
            # Generate general response
            response = llm_wrapper.generate_response(user_name)
            # Display response
            chatbot.display_response(response)
            return jsonify({"response": response, "history": llm_wrapper.get_chat_history()})
        elif input_type == "scenario_type":
            # Generate scenario
            scenario = llm_wrapper.generate_scenario(user_input)
            scenarios.append(scenario)
            
            # Display scenario (handled by frontend)
            chatbot.display_scenario(scenario)
            
            # Generate summary
            summary = llm_wrapper.generate_summary(scenario)
            
            # Display response (summary)
            chatbot.display_response(summary)
            
            return jsonify({"scenario": scenario, "summary": summary})
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
        # Create user instance with the name
        get_user(user_name)
        return jsonify({"message": "Name saved successfully!", "name": user_name})
    except Exception as e:
        print(f"Error storing name: {e}")
        return jsonify({"error": "An error occurred while storing the name"}), 500

@app.route("/generate_uml", methods=["POST"])
def generate_uml():
    """Generate UML text from the given scenario text."""
    try:
        scenario_text = request.json.get("scenarioText", "").strip()
        if not scenario_text:
            return jsonify({"error": "Scenario text is required"}), 400

        llm_wrapper = get_llm_wrapper()
        client = llm_wrapper.client
        plant_uml = gpt_v2_interface(scenario_text, client)
        return jsonify({"plantuml": plant_uml})
    except Exception as e:
        print(f"Error generating UML: {e}")
        return jsonify({"error": "An error occurred while generating the UML"}), 500

@app.route("/get_scenarios", methods=["GET"])
def get_scenarios():
    """Retrieve all stored scenarios."""
    return jsonify({"scenarios": scenarios})

# Project management routes that use the ProjectManager class
@app.route("/submit_to_database", methods=["POST"])
def submit_to_database():
    """Submit work results to MongoDB using the nested schema."""
    try:
        data = request.json
        project_name = data.get("project_name", "").strip()
        file_name = data.get("file_name", "").strip()
        username = data.get("username", "").strip()
        scenario = data.get("scenario", "")
        plant_uml = data.get("plant_uml", "")
        chat_history = data.get("chat_history", [])
        
        project_manager = get_project_manager()
        result, status_code = project_manager.submit_to_database(
            project_name, file_name, username, scenario, plant_uml, chat_history
        )
        
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in submit_to_database: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route("/get_projects", methods=["GET"])
def get_projects():
    """Fetch the list of existing projects from the database."""
    try:
        project_manager = get_project_manager()
        result, status_code = project_manager.get_projects()
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_projects: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route("/create_project", methods=["POST"])
def create_project():
    """Create a new project in the database with the nested schema."""
    try:
        data = request.json
        project_name = data.get("project_name", "").strip()
        username = data.get("username", session.get("user_name", "Anonymous")).strip()
        
        project_manager = get_project_manager()
        result, status_code = project_manager.create_project(project_name, username)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in create_project: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route("/create_file", methods=["POST"])
def create_file():
    """Create a new file in the selected project using the nested schema."""
    try:
        data = request.json
        project_name = data.get("project_name", "").strip()
        file_name = data.get("file_name", "").strip()
        
        project_manager = get_project_manager()
        result, status_code = project_manager.create_file(project_name, file_name)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in create_file: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route("/get_files", methods=["GET"])
def get_files():
    """Fetch the list of files for a selected project using the nested schema."""
    try:
        project_name = request.args.get("project_name", "").strip()
        
        project_manager = get_project_manager()
        result, status_code = project_manager.get_files(project_name)
        return jsonify(result), status_code
    except Exception as e:
        print(f"Error in get_files: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

if __name__ == "__main__":
    app.run(debug=True)