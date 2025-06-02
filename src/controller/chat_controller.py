from flask import request, jsonify, session
from src.model.llm_service import LLMService
from src.model.gpt2 import gpt_v2_interface 
from src.model.project_service import ProjectService

class ChatController:
    """Controller for chat-related operations and version saving"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.project_service = ProjectService()
        
    def handle_chat_request(self):
        """Process user input and generate response with version saving"""
        try:
            data = request.json
            user_input = data.get("message", "").strip()
            project_name = data.get("project_name", "").strip()

            if not user_input:
                return jsonify({"error": "User input is required"}), 400
            if not project_name:
                return jsonify({"error": "Project name is required to save version"}), 400
            
            # Get the current state before processing new input
            # This ensures we always have the latest domain model and PlantUML
            project_result, _ = self.project_service.get_project_data(project_name)
            current_project_data = project_result.get("project_data", {})
            
            # Get existing domain model description and PlantUML from project data
            # These will be used as fallbacks if nothing new is generated
            existing_dmd = current_project_data.get("domain_model_description", "Welcome to your new project! Start by describing your domain.")
            existing_plant_uml = current_project_data.get("plant_uml", "@startuml\nskinparam monochrome true\ntitle Your New Project\n\nclass ExampleEntity {\n  +id: string\n  +name: string\n}\n\nnote \"Start building your domain model!\" as N1\n@enduml")
            
            self.llm_service.add_to_chat_history("user", user_input)
            updated_chat_history = self.llm_service.chat_history.get_messages()
            chat_history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in updated_chat_history
            ])
            
            classification_result = self.llm_service.determine_input_type(chat_history_text)
            
            decision = classification_result.get("decision", False)
            is_casual_comment = classification_result.get("is_casual_comment", False)
            suggestions = classification_result.get("suggestions", [])
            assistant_response = "\n".join(suggestions) if isinstance(suggestions, list) else suggestions

            # Set initial state using existing values to ensure we never store nulls
            current_dmd = self.llm_service.get_current_domain_model_description() or existing_dmd
            current_plant_uml = existing_plant_uml

            if is_casual_comment:
                self.llm_service.add_to_chat_history("assistant", assistant_response)
                
                # Use existing domain model and PlantUML (already set above)
                # If DMD exists but PlantUML doesn't, generate PlantUML
                if current_dmd and not current_plant_uml:
                    client = self.llm_service.client
                    current_plant_uml = gpt_v2_interface(current_dmd, client)
                
                self.project_service.save_version(
                    project_name,
                    user_input,
                    assistant_response,
                    current_dmd,
                    current_plant_uml
                )
                return jsonify({
                    "response": assistant_response,
                    "history": self.llm_service.get_chat_history(),
                    "domain_model_description": current_dmd,
                    "plant_uml": current_plant_uml
                })
                
            elif decision: # Enough information for domain modeling (new or update)
                new_dmd = self.llm_service.generate_domain_model_description(chat_history_text)
                self.llm_service.add_to_chat_history("assistant", assistant_response)
                
                # Generate PlantUML for the new/updated DMD
                client = self.llm_service.client
                new_plant_uml = ""
                if new_dmd:
                    new_plant_uml = gpt_v2_interface(new_dmd, client)
                else:
                    new_dmd = current_dmd  # Fallback to existing DMD
                    new_plant_uml = current_plant_uml  # Fallback to existing PlantUML

                self.project_service.save_version(
                    project_name,
                    user_input,
                    assistant_response,
                    new_dmd,
                    new_plant_uml
                )
                
                return jsonify({
                    "domain_model_description": new_dmd, 
                    "suggestion": assistant_response,
                    "plant_uml": new_plant_uml
                })
                
            else: # Not enough info for domain modeling
                self.llm_service.add_to_chat_history("assistant", assistant_response)
                
                # Use existing domain model and PlantUML
                # If we have a domain model but no PlantUML, generate it
                if current_dmd and not current_plant_uml:
                    client = self.llm_service.client
                    current_plant_uml = gpt_v2_interface(current_dmd, client)

                self.project_service.save_version(
                    project_name,
                    user_input,
                    assistant_response,
                    current_dmd,
                    current_plant_uml
                )
                
                return jsonify({
                    "response": assistant_response, 
                    "history": self.llm_service.get_chat_history(),
                    "domain_model_description": current_dmd,
                    "plant_uml": current_plant_uml
                })

        except Exception as e:
            print(f"Error in chat request: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "An unexpected error occurred"}), 500
    
    def generate_uml(self):
        """Generate UML diagram from domain model description"""
        try:
            domain_model_description_text = request.json.get("domainModelDescriptionText", "").strip()
            if not domain_model_description_text:
                return jsonify({"error": "Domain Model Description is required"}), 400

            client = self.llm_service.client
            plant_uml = gpt_v2_interface(domain_model_description_text, client)
            return jsonify({"plantuml": plant_uml})
        except Exception as e:
            print(f"Error generating UML: {e}")
            return jsonify({"error": "An error occurred while generating the UML"}), 500
    
    def get_current_domain_model_description(self):
        """Retrieve the current domain model description"""
        domain_model_description = self.llm_service.get_current_domain_model_description()
        return jsonify({"domain_model_description": domain_model_description})