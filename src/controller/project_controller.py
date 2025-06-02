from flask import request, jsonify, session
from src.model.project_service import ProjectService

class ProjectController:
    """Controller for project management operations"""
    
    def __init__(self):
        self.project_service = ProjectService()
    
    def get_projects(self):
        """Get list of projects from database"""
        try:
            result, status_code = self.project_service.get_projects()
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in get_projects: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def create_project(self):
        """Create a new project with auto-generated name"""
        try:
            result, status_code = self.project_service.create_project()
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in create_project: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def rename_project(self):
        """Rename an existing project"""
        try:
            data = request.json
            old_project_name = data.get("old_project_name", "").strip()
            new_project_name = data.get("new_project_name", "").strip()
            
            result, status_code = self.project_service.rename_project(old_project_name, new_project_name)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in rename_project: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def get_project_data(self):
        """Get project data for the specified project"""
        try:
            project_name = request.args.get("project_name", "").strip()
            
            result, status_code = self.project_service.get_project_data(project_name)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in get_project_data: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def save_project_data(self):
        """Save data for the specified project"""
        try:
            data = request.json
            project_name = data.get("project_name", "").strip()
            domain_model_description = data.get("domain_model_description")
            plant_uml = data.get("plant_uml")
            chat_history = data.get("chat_history")
            
            # Extract last messages from chat history if available
            user_input = None
            assistant = None
            if chat_history and len(chat_history) >= 2:
                # Assuming the last user message and response are at the end of the chat history
                for i in range(len(chat_history)-1, -1, -1):
                    if chat_history[i]["role"] == "assistant" and assistant is None:
                        assistant = chat_history[i]["content"]
                    elif chat_history[i]["role"] == "user" and user_input is None:
                        user_input = chat_history[i]["content"]
                    if user_input and assistant:
                        break
            
            result, status_code = self.project_service.save_version(
                project_name, user_input, assistant, domain_model_description, plant_uml
            )
            
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in save_project_data: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500

    def undo_project_change(self):
        """Handle request to undo the latest version for a project."""
        try:
            data = request.json
            project_name = data.get("project_name", "").strip()
            if not project_name:
                return jsonify({"error": "Project name is required."}), 400
            
            result, status_code = self.project_service.undo_version(project_name)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in undo_project_change controller: {e}")
            return jsonify({"error": "An unexpected error occurred while undoing version."}), 500