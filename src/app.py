from flask import Flask, render_template
from src.controller.chat_controller import ChatController
from src.controller.project_controller import ProjectController
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__, 
            template_folder='view/templates', 
            static_folder='view/static')
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Initialize controllers
chat_controller = None
project_controller = None

def get_chat_controller():
    """Get or create a ChatController instance."""
    global chat_controller
    if chat_controller is None:
        chat_controller = ChatController()
    return chat_controller

def get_project_controller():
    """Get or create a ProjectController instance."""
    global project_controller
    if project_controller is None:
        project_controller = ProjectController()
    return project_controller

def reset_controllers():
    """Reset all controllers."""
    global chat_controller
    chat_controller = None
    # Don't reset project_controller as it maintains DB connections

# Routes
@app.route("/")
def home():
    """Home page route."""
    reset_controllers()
    return render_template("index.html")

# Chat routes
@app.route("/chat", methods=["POST"])
def chat():
    """Chat endpoint."""
    controller = get_chat_controller()
    return controller.handle_chat_request()

@app.route("/submit_name", methods=["POST"])
def submit_name():
    """Submit name endpoint."""
    controller = get_chat_controller()
    return controller.submit_name()

@app.route("/generate_uml", methods=["POST"])
def generate_uml():
    """Generate UML endpoint."""
    controller = get_chat_controller()
    return controller.generate_uml()

@app.route("/get_scenarios", methods=["GET"])
def get_scenarios():
    """Get scenarios endpoint."""
    controller = get_chat_controller()
    return controller.get_current_scenario()

# Project routes
@app.route("/save_to_database", methods=["POST"])
def save_to_database():
    """Save to database endpoint."""
    controller = get_project_controller()
    return controller.submit_to_database()  # Keep the controller method name the same

@app.route("/get_projects", methods=["GET"])
def get_projects():
    """Get projects endpoint."""
    controller = get_project_controller()
    return controller.get_projects()

@app.route("/create_project", methods=["POST"])
def create_project():
    """Create project endpoint."""
    controller = get_project_controller()
    return controller.create_project()

@app.route("/create_file", methods=["POST"])
def create_file():
    """Create file endpoint."""
    controller = get_project_controller()
    return controller.create_file()

@app.route("/get_files", methods=["GET"])
def get_files():
    """Get files endpoint."""
    controller = get_project_controller()
    return controller.get_files()

# Run the application
if __name__ == "__main__":
    app.run(debug=True)