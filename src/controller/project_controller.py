from flask import request, jsonify, session
from src.model.project_service import ProjectService

class ProjectController:
    """Controller for project management operations"""
    
    def __init__(self):
        self.project_service = ProjectService()
        
    def submit_to_database(self):
        """Submit work results to the database"""
        try:
            data = request.json
            project_name = data.get("project_name", "").strip()
            file_name = data.get("file_name", "").strip()
            username = data.get("username", "").strip()
            scenario = data.get("scenario", "")
            plant_uml = data.get("plant_uml", "")
            chat_history = data.get("chat_history", [])
            
            result, status_code = self.project_service.submit_to_database(
                project_name, file_name, username, scenario, plant_uml, chat_history
            )
            
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in submit_to_database: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def get_projects(self):
        """Get list of projects from database"""
        try:
            result, status_code = self.project_service.get_projects()
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in get_projects: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def create_project(self):
        """Create a new project in the database"""
        try:
            data = request.json
            project_name = data.get("project_name", "").strip()
            username = data.get("username", session.get("user_name", "Anonymous")).strip()
            
            result, status_code = self.project_service.create_project(project_name, username)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in create_project: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def create_file(self):
        """Create a new file within a project"""
        try:
            data = request.json
            project_name = data.get("project_name", "").strip()
            file_name = data.get("file_name", "").strip()
            
            result, status_code = self.project_service.create_file(project_name, file_name)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in create_file: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500
    
    def get_files(self):
        """Get list of files for a project"""
        try:
            project_name = request.args.get("project_name", "").strip()
            
            result, status_code = self.project_service.get_files(project_name)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error in get_files: {e}")
            return jsonify({"error": "An unexpected error occurred."}), 500