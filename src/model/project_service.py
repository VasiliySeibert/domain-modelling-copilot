import os
from pymongo import MongoClient
from datetime import datetime

class ProjectService:
    """Service for project database operations with embedded version history."""
    
    def __init__(self):
        """Initialize connection to MongoDB."""
        try:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            print(f"Connecting to MongoDB at: {mongo_uri}")
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            print("MongoDB connection successful")
            self.db = self.client.get_database("domain_modelling_copilot")
            self.projects_collection = self.db.get_collection("projects")
        except Exception as e:
            print(f"MongoDB connection error: {str(e)}")
            self.client = None
            self.db = None
            self.projects_collection = None
    
    def get_projects(self):
        """Get list of all projects."""
        try:
            projects = self.projects_collection.find({}, {"project_name": 1, "_id": 0})
            project_names = [project["project_name"] for project in projects]
            return {"projects": project_names}, 200
        except Exception as e:
            print(f"Error retrieving projects: {e}")
            return {"error": "Failed to retrieve projects."}, 500
    
    def create_project(self):
        """Create a new project with an initial version."""
        try:
            if self.projects_collection is None:
                return {"error": "Database connection not available."}, 500

            project_count = self.projects_collection.count_documents({})
            project_name = f"Project {project_count + 1}"
            
            while self.projects_collection.find_one({"project_name": project_name}):
                project_count += 1
                project_name = f"Project {project_count + 1}"
                
            # Initial version data
            initial_dmd = "Welcome to your new project! Start by describing your domain."
            initial_plant_uml = "@startuml\nskinparam monochrome true\ntitle Your New Project\n\nclass ExampleEntity {\n  +id: string\n  +name: string\n}\n\nnote \"Start building your domain model!\" as N1\n@enduml"
            initial_assistant = "Welcome to your new project! How can I help you model your domain?"

            # Create project with embedded initial version
            project_doc = {
                "project_name": project_name,
                "created_at": datetime.now(),
                "versions": [
                    {
                        "version": 1,
                        "user_input": None,  # No user input for initial version
                        "assistant": initial_assistant,
                        "domain_model_description": initial_dmd,
                        "plant_uml": initial_plant_uml,
                        "timestamp": datetime.now()
                    }
                ]
            }
            
            self.projects_collection.insert_one(project_doc)
            return {"message": f"Project '{project_name}' created successfully.", "project_name": project_name}, 201
        except Exception as e:
            print(f"Error creating project: {e}")
            return {"error": f"Failed to create project: {str(e)}"}, 500
    
    def rename_project(self, old_project_name, new_project_name):
        """Rename an existing project."""
        try:
            if not new_project_name or not old_project_name:
                return {"error": "Both old and new project names are required."}, 400
                
            # Check if the new name already exists
            if self.projects_collection.find_one({"project_name": new_project_name}):
                return {"error": f"Project '{new_project_name}' already exists."}, 409
                
            # Update the project name
            result = self.projects_collection.update_one(
                {"project_name": old_project_name},
                {"$set": {"project_name": new_project_name}}
            )
                
            if result.modified_count > 0:
                return {"message": f"Project renamed from '{old_project_name}' to '{new_project_name}' successfully."}, 200
            else:
                return {"error": f"Project '{old_project_name}' not found."}, 404
        except Exception as e:
            print(f"Error renaming project: {e}")
            return {"error": f"Failed to rename project: {str(e)}"}, 500
    
    def get_project_data(self, project_name):
        """Get the latest project state and reconstructed chat history."""
        try:
            if not project_name:
                return {"error": "Project name is required."}, 400
            if self.projects_collection is None:
                return {"error": "Database connection is not available."}, 500
                
            project_doc = self.projects_collection.find_one({"project_name": project_name})
            if not project_doc:
                return {"error": f"Project '{project_name}' not found."}, 404
            
            versions = project_doc.get("versions", [])
            if not versions:
                return {"error": f"No version data found for project '{project_name}'."}, 404

            # The latest version represents the current state
            latest_version = versions[-1]
            
            current_domain_model = latest_version.get("domain_model_description")
            current_plant_uml = latest_version.get("plant_uml")
            
            # Reconstruct chat history from all versions
            chat_history = []
            for version in versions:
                if version.get("user_input"):
                    chat_history.append({"role": "user", "content": version["user_input"]})
                if version.get("assistant"):
                    chat_history.append({"role": "assistant", "content": version["assistant"]})
            
            project_data = {
                "domain_model_description": current_domain_model,
                "plant_uml": current_plant_uml,
                "chat_history": chat_history
            }
            
            print(f"Project data retrieved successfully for '{project_name}'")
            return {"project_data": project_data}, 200
        except Exception as e:
            print(f"Error retrieving project data: {e}")
            return {"error": f"Failed to retrieve project data: {str(e)}"}, 500
    
    def save_version(self, project_name, user_input, assistant, domain_model_description, plant_uml):
        """Add a new version to the project's versions array."""
        try:
            if not project_name:
                return {"error": "Project name is required."}, 400
            if self.projects_collection is None:
                return {"error": "Database connection not available."}, 500

            # Find the project
            project_doc = self.projects_collection.find_one({"project_name": project_name})
            if not project_doc:
                return {"error": f"Project '{project_name}' not found."}, 404
            
            # Get versions array or initialize if not exists
            versions = project_doc.get("versions", [])
            
            # If there are existing versions, use their values as fallbacks
            if versions:
                latest_version = versions[-1]
                # Ensure we're not saving null values by using the previous version as fallback
                if domain_model_description is None:
                    domain_model_description = latest_version.get("domain_model_description", "Welcome to your new project! Start by describing your domain.")
                
                if plant_uml is None:
                    plant_uml = latest_version.get("plant_uml", "@startuml\nskinparam monochrome true\ntitle Your New Project\n\nclass ExampleEntity {\n  +id: string\n  +name: string\n}\n\nnote \"Start building your domain model!\" as N1\n@enduml")
            else:
                # Initialize with defaults if this is somehow the first version
                if domain_model_description is None:
                    domain_model_description = "Welcome to your new project! Start by describing your domain."
                
                if plant_uml is None:
                    plant_uml = "@startuml\nskinparam monochrome true\ntitle Your New Project\n\nclass ExampleEntity {\n  +id: string\n  +name: string\n}\n\nnote \"Start building your domain model!\" as N1\n@enduml"
            
            # Determine next version number
            next_version = len(versions) + 1
            
            # Create new version object
            new_version = {
                "version": next_version,
                "user_input": user_input,
                "assistant": assistant,
                "domain_model_description": domain_model_description,
                "plant_uml": plant_uml,
                "timestamp": datetime.now()
            }
            
            # Add the new version to the versions array
            result = self.projects_collection.update_one(
                {"project_name": project_name},
                {"$push": {"versions": new_version}}
            )
            
            if result.modified_count > 0:
                return {"message": f"Version {next_version} for project '{project_name}' saved successfully.", "version": next_version}, 200
            else:
                return {"error": "Failed to save version."}, 500
        except Exception as e:
            print(f"Error saving project version: {e}")
            return {"error": f"Failed to save project version: {str(e)}"}, 500

    def undo_version(self, project_name):
        """Remove the latest version from the project's versions array."""
        try:
            if not project_name:
                return {"error": "Project name is required."}, 400
            if self.projects_collection is None:
                return {"error": "Database connection not available."}, 500

            # Find the project
            project_doc = self.projects_collection.find_one({"project_name": project_name})
            if not project_doc:
                return {"error": f"Project '{project_name}' not found."}, 404
            
            versions = project_doc.get("versions", [])
            if len(versions) <= 1:
                return {"error": "Cannot undo the initial project version."}, 400
            
            # Remove the last element from the versions array using $pop operation
            result = self.projects_collection.update_one(
                {"project_name": project_name},
                {"$pop": {"versions": 1}}  # 1 to remove the last element
            )
            
            if result.modified_count == 0:
                return {"error": "Failed to undo version."}, 500

            # After removing, get the project data with the previous version
            return self.get_project_data(project_name)
            
        except Exception as e:
            print(f"Error undoing version: {e}")
            return {"error": f"Failed to undo version: {str(e)}"}, 500