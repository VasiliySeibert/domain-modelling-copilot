from pymongo import MongoClient
from flask import jsonify

class ProjectManager:
    """Manages project and file operations in the database."""
    
    def __init__(self):
        """Initialize the project manager with MongoDB connection."""
        # MongoDB setup
        MONGO_URI = "mongodb://localhost:27017/"
        self.client = MongoClient(MONGO_URI)
        self.db = self.client["domain_modelling_copilot"]
        self.projects_collection = self.db["projects"]
    
    def submit_to_database(self, project_name, file_name, username, scenario, plant_uml, chat_history):
        """Submit work results to MongoDB."""
        try:
            # Validate required fields
            if not project_name or not file_name:
                return {"error": "Project name and file name are required."}, 400

            # Check if the project exists
            project = self.projects_collection.find_one({"project_name": project_name})
            if not project:
                # Create project if it doesn't exist
                self.projects_collection.insert_one({
                    "project_name": project_name,
                    "username": username,
                    "files": []
                })
                project = self.projects_collection.find_one({"project_name": project_name})

            # Prepare file data
            file_data = {
                "file_name": file_name,
                "scenario": scenario,
                "plant_uml": plant_uml,
                "chat_history": chat_history  # Direct assignment of chat_history array
            }

            # Check if file exists
            file_exists = False
            for i, file in enumerate(project.get("files", [])):
                if file.get("file_name") == file_name:
                    file_exists = True
                    # Update existing file
                    self.projects_collection.update_one(
                        {"project_name": project_name},
                        {"$set": {f"files.{i}": file_data}}
                    )
                    break

            # Add new file if it doesn't exist
            if not file_exists:
                self.projects_collection.update_one(
                    {"project_name": project_name},
                    {"$push": {"files": file_data}}
                )

            return {"message": "Work result saved successfully!"}, 200
        except Exception as e:
            print(f"Error saving to database: {e}")
            return {"error": "An error occurred while saving to the database."}, 500
    
    def get_projects(self):
        """Fetch the list of existing projects from the database."""
        try:
            # Fetch distinct project names from the database
            projects = self.projects_collection.distinct("project_name")
            return {"projects": projects}, 200
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return {"error": "An error occurred while fetching projects."}, 500
    
    def create_project(self, project_name, username):
        """Create a new project in the database with the nested schema."""
        try:
            # Validate project name
            if not project_name:
                return {"error": "Project name is required."}, 400

            # Check if the project already exists
            existing_project = self.projects_collection.find_one({"project_name": project_name})
            if existing_project:
                return {"error": "Project already exists."}, 400

            # Insert the new project with the nested schema
            self.projects_collection.insert_one({
                "project_name": project_name,
                "username": username,
                "files": []  # Empty files array initially
            })
            return {"message": "Project created successfully!"}, 200
        except Exception as e:
            print(f"Error creating project: {e}")
            return {"error": "An error occurred while creating the project."}, 500
    
    def create_file(self, project_name, file_name):
        """Create a new file in the selected project using the nested schema."""
        try:
            # Validate inputs
            if not project_name or not file_name:
                return {"error": "Project name and file name are required."}, 400

            # Check if the project exists
            project = self.projects_collection.find_one({"project_name": project_name})
            if not project:
                return {"error": "Project does not exist."}, 404

            # Check if the file already exists in the project
            if project.get("files"):
                for file in project.get("files", []):
                    if file.get("file_name") == file_name:
                        return {"error": "File already exists in this project."}, 400

            # Add the file to the project's file list
            result = self.projects_collection.update_one(
                {"project_name": project_name},
                {"$push": {"files": {
                    "file_name": file_name,
                    "scenario": None,
                    "plant_uml": None,
                    "chat_history": []
                }}}
            )
            
            if result.modified_count == 0:
                return {"error": "Failed to create file."}, 500
                
            return {"message": "File created successfully!"}, 200
        except Exception as e:
            print(f"Error creating file: {e}")
            return {"error": "An error occurred while creating the file."}, 500
    
    def get_files(self, project_name):
        """Fetch the list of files for a selected project using the nested schema."""
        try:
            # Validate project name
            if not project_name:
                return {"error": "Project name is required."}, 400

            # Fetch the project from the database
            project = self.projects_collection.find_one({"project_name": project_name})
            if not project:
                return {"error": "Project does not exist."}, 404

            # Extract file names from the nested structure
            file_names = [file.get("file_name") for file in project.get("files", [])]
            return {"files": file_names}, 200
        except Exception as e:
            print(f"Error fetching files: {e}")
            return {"error": "An error occurred while fetching files."}, 500