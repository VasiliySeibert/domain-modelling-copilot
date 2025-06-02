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

@app.route("/generate_uml", methods=["POST"])
def generate_uml():
    """Generate UML endpoint."""
    controller = get_chat_controller()
    return controller.generate_uml()

@app.route("/get_domain_model_descriptions", methods=["GET"])
def get_domain_model_descriptions():
    """Get domain model descriptions endpoint."""
    controller = get_chat_controller()
    return controller.get_current_domain_model_description()

# Project routes (simplified to remove file management)
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

@app.route("/rename_project", methods=["POST"])
def rename_project():
    """Rename project endpoint."""
    controller = get_project_controller()
    return controller.rename_project()

@app.route("/get_project_data", methods=["GET"])
def get_project_data():
    """Get project data endpoint."""
    controller = get_project_controller()
    return controller.get_project_data()

@app.route("/save_project_data", methods=["POST"])
def save_project_data():
    """Save project data endpoint."""
    controller = get_project_controller()
    return controller.save_project_data()

@app.route("/undo_project_change", methods=["POST"])
def undo_project_change():
    """Undo project change endpoint."""
    controller = get_project_controller()
    return controller.undo_project_change()

# Run the application
if __name__ == "__main__":
    app.run(debug=True)