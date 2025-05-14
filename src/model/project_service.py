import os
from pymongo import MongoClient
from datetime import datetime  # Add this import

class ProjectService:
    """Service for project database operations."""
    
    def __init__(self):
        """Initialize connection to MongoDB."""
        try:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            print(f"Connecting to MongoDB at: {mongo_uri}")
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            print("MongoDB connection successful")
            self.db = self.client.get_database("domain_modelling_copilot")
            self.projects_collection = self.db.get_collection("projects")
        except Exception as e:
            print(f"MongoDB connection error: {str(e)}")
            self.client = None
            self.db = None
            self.projects_collection = None
    
    def save_to_database(self, project_name, file_name, username, domain_model_description, plant_uml, chat_history):
        """Save work results to the database."""
        if not project_name or not file_name:
            return {"error": "Project name and file name are required."}, 400
            
        # Check if project exists
        project = self.projects_collection.find_one({"project_name": project_name})
        if not project:
            return {"error": f"Project '{project_name}' not found."}, 404
            
        # Check if file exists in the project
        file_exists = False
        for file in project.get("files", []):
            if file.get("file_name") == file_name:
                file_exists = True
                break
                
        if not file_exists:
            return {"error": f"File '{file_name}' not found in project '{project_name}'."}, 404
            
        # Update file content
        result = self.projects_collection.update_one(
            {"project_name": project_name, "files.file_name": file_name},
            {
                "$set": {
                    "files.$.domain_model_description": domain_model_description,
                    "files.$.plant_uml": plant_uml,
                    "files.$.chat_history": chat_history,
                    "files.$.last_modified_by": username,
                    "files.$.last_modified_at": datetime.now()
                }
            }
        )
            
        if result.modified_count > 0:
            return {"message": "File updated successfully."}, 200
        else:
            return {"error": "Failed to update file."}, 500
    
    def get_projects(self):
        """Get list of all projects."""
        try:
            projects = self.projects_collection.find({}, {"project_name": 1, "_id": 0})
            project_names = [project["project_name"] for project in projects]
            return {"projects": project_names}, 200
        except Exception as e:
            print(f"Error retrieving projects: {e}")
            return {"error": "Failed to retrieve projects."}, 500
    
    def create_project(self, project_name, username):
        """Create a new project."""
        if not project_name:
            return {"error": "Project name is required."}, 400
            
        # Check if project already exists
        existing_project = self.projects_collection.find_one({"project_name": project_name})
        if existing_project:
            return {"error": f"Project '{project_name}' already exists."}, 409
            
        # Create new project
        project = {
            "project_name": project_name,
            "created_by": username,
            "created_at": datetime.now(),
            "files": []
        }
            
        result = self.projects_collection.insert_one(project)
        if result.inserted_id:
            return {"message": f"Project '{project_name}' created successfully."}, 201
        else:
            return {"error": "Failed to create project."}, 500
    
    def create_file(self, project_name, file_name):
        """Create a new file within a project."""
        if not project_name or not file_name:
            return {"error": "Project name and file name are required."}, 400
            
        # Check if project exists
        project = self.projects_collection.find_one({"project_name": project_name})
        if not project:
            return {"error": f"Project '{project_name}' not found."}, 404
            
        # Check if file already exists in the project
        for file in project.get("files", []):
            if file.get("file_name") == file_name:
                return {"error": f"File '{file_name}' already exists in project '{project_name}'."}, 409
            
        # Create new file
        new_file = {
            "file_name": file_name,
            "created_at": datetime.now(),
            "domain_model_description": None,
            "plant_uml": None,
            "chat_history": []
        }
            
        result = self.projects_collection.update_one(
            {"project_name": project_name},
            {"$push": {"files": new_file}}
        )
            
        if result.modified_count > 0:
            return {"message": f"File '{file_name}' created successfully in project '{project_name}'."}, 201
        else:
            return {"error": "Failed to create file."}, 500
    
    def get_files(self, project_name):
        """Get list of files for a project."""
        if not project_name:
            return {"error": "Project name is required."}, 400
            
        # Get project with files
        project = self.projects_collection.find_one({"project_name": project_name})
        if not project:
            return {"error": f"Project '{project_name}' not found."}, 404
            
        # Extract file names
        file_names = [file["file_name"] for file in project.get("files", [])]
        return {"files": file_names}, 200