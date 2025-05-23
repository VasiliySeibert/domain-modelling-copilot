import os
from pymongo import MongoClient
from datetime import datetime

class ProjectService:
    """Service for project database operations with simplified structure."""
    
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
        """Create a new project with auto-generated name."""
        try:
            # Get the count of existing projects to generate the next project number
            project_count = self.projects_collection.count_documents({})
            project_name = f"Project {project_count + 1}"
            
            # Check if this name already exists (unlikely but possible if projects were deleted)
            while self.projects_collection.find_one({"project_name": project_name}):
                project_count += 1
                project_name = f"Project {project_count + 1}"
                
            # Create new project with simplified structure (no files array)
            project = {
                "project_name": project_name,
                "created_at": datetime.now(),
                "domain_model_description": None,
                "plant_uml": None,
                "chat_history": []
            }
                
            result = self.projects_collection.insert_one(project)
            if result.inserted_id:
                return {"message": f"Project '{project_name}' created successfully.", "project_name": project_name}, 201
            else:
                return {"error": "Failed to create project."}, 500
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
        """Get all data for a specific project."""
        try:
            if not project_name:
                return {"error": "Project name is required."}, 400
                
            # Check if MongoDB connection is available
            if self.projects_collection is None:
                return {"error": "Database connection is not available."}, 500
                
            # Get the project data
            project = self.projects_collection.find_one(
                {"project_name": project_name}, 
                {"_id": 0, "domain_model_description": 1, "plant_uml": 1, "chat_history": 1}
            )
            
            if not project:
                return {"error": f"Project '{project_name}' not found."}, 404
                
            print(f"Project data retrieved successfully for '{project_name}'")
            return {"project_data": project}, 200
        except Exception as e:
            print(f"Error retrieving project data: {e}")
            return {"error": f"Failed to retrieve project data: {str(e)}"}, 500
    
    def save_project_data(self, project_name, domain_model_description=None, plant_uml=None, chat_history=None):
        """Save project data directly to the project document."""
        try:
            if not project_name:
                return {"error": "Project name is required."}, 400
                
            # Build update document with only the fields that are provided
            update_doc = {}
            if domain_model_description is not None:
                update_doc["domain_model_description"] = domain_model_description
            if plant_uml is not None:
                update_doc["plant_uml"] = plant_uml
            if chat_history is not None:
                update_doc["chat_history"] = chat_history
                
            if not update_doc:
                return {"error": "No data provided to update."}, 400
                
            # Update the project
            result = self.projects_collection.update_one(
                {"project_name": project_name},
                {"$set": update_doc}
            )
                
            if result.modified_count > 0:
                return {"message": f"Project '{project_name}' updated successfully."}, 200
            else:
                return {"error": f"Project '{project_name}' not found or no changes made."}, 404
        except Exception as e:
            print(f"Error saving project data: {e}")
            return {"error": f"Failed to save project data: {str(e)}"}, 500