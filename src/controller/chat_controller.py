from flask import request, jsonify
from src.model.llm_service import LLMService
from src.model.gpt2 import gpt_v2_interface 
from src.model.project_service import ProjectService

class ChatController:
    """Controller for chat-related operations using agent-based architecture"""
    
    def __init__(self):
        # Create agents
        print("Initializing ChatController with three specialized agents")
        self.chat_agent = AgentChat()
        self.domain_model_agent = AgentDomainModelDescription()
        self.visualization_agent = AgentDomainModelVisualization()
        
        # Connect agents in a bidirectional network
        self.chat_agent.connect("DomainModelAgent", self.domain_model_agent)
        self.chat_agent.connect("VisualizationAgent", self.visualization_agent)
        
        self.domain_model_agent.connect("ChatAgent", self.chat_agent)
        self.domain_model_agent.connect("VisualizationAgent", self.visualization_agent)
        
        self.visualization_agent.connect("ChatAgent", self.chat_agent)
        self.visualization_agent.connect("DomainModelAgent", self.domain_model_agent)
        
        print("Agent network initialized with bidirectional connections")
    
    def handle_chat_request(self):
        """Process user input using the ChatAgent"""
        try:
            data = request.json
            user_input = data.get("message", "").strip()
            project_name = data.get("project_name", "").strip()

            if not user_input:
                return jsonify({"error": "User input is required"}), 400
            if not project_name:
                return jsonify({"error": "Project name is required"}), 400
            
            # Get the current state before processing new input
            project_result, _ = self.project_service.get_project_data(project_name)
            current_project_data = project_result.get("project_data", {})
            
            # Get existing domain model description and PlantUML from project data
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
                
            elif decision:
                new_dmd = self.llm_service.generate_domain_model_description(chat_history_text)
                self.llm_service.add_to_chat_history("assistant", assistant_response)
                
                client = self.llm_service.client
                new_plant_uml = ""
                if new_dmd:
                    new_plant_uml = gpt_v2_interface(new_dmd, client)
                else:
                    new_dmd = current_dmd 
                    new_plant_uml = current_plant_uml  
                    
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
                
            else: 
                self.llm_service.add_to_chat_history("assistant", assistant_response)
                
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
            traceback.print_exc()
            return jsonify({"error": "An unexpected error occurred"}), 500
    
    def generate_uml(self):
        """Generate UML diagram from domain model description using VisualizationAgent"""
        try:
            domain_model_description_text = request.json.get("domainModelDescriptionText", "").strip()
            if not domain_model_description_text:
                return jsonify({"error": "Domain Model Description is required"}), 400

            # Use visualization agent to generate PlantUML
            result = self.visualization_agent.generate_plantuml(domain_model_description_text)
            
            if "error" in result:
                return jsonify({"error": result["error"]}), 400
                
            return jsonify({"plantuml": result["plant_uml"]})
        except Exception as e:
            print(f"Error generating UML: {e}")
            return jsonify({"error": "An error occurred while generating the UML"}), 500
    
    def get_current_domain_model_description(self):
        """Retrieve the current domain model description from DomainModelAgent"""
        result = self.domain_model_agent.get_domain_model()
        return jsonify({"domain_model_description": result.get("domain_model_description")})