import uuid
from src.model.llm_service import LLMService
from src.model.project_service import ProjectService

class AgentChat:
    """Central agent for handling user interactions and coordinating with specialized agents"""
    
    def __init__(self):
        """Initialize chat agent with required services"""
        self._connected_agents = {}
        self._llm_service = LLMService()
        self._project_service = ProjectService()
        self._current_project_name = None
        self._chat_history = []
    
    def connect(self, agent_name, agent_instance):
        """Connect this agent to another agent"""
        self._connected_agents[agent_name] = agent_instance
        print(f"AgentChat connected to {agent_name}")
    
    def send_message(self, to_agent_name, message_type, content):
        """Send a message to another agent"""
        if to_agent_name not in self._connected_agents:
            raise ValueError(f"Agent {to_agent_name} not connected")
            
        message = {
            "from": "ChatAgent",
            "type": message_type,
            "content": content
        }
        
        print(f"ChatAgent → {to_agent_name}: {message_type}")
        return self._connected_agents[to_agent_name].receive_message(message)
    
    def receive_message(self, message):
        """Receive and process a message from another agent"""
        from_agent = message["from"]
        msg_type = message["type"]
        print(f"{from_agent} → DomainModelAgent: {msg_type}")
        
        if msg_type == "generate_domain_model":
            # Generate domain model based on chat history
            chat_history_text = message["content"].get("chat_history_text", "")
            return self.generate_domain_model(chat_history_text)
            
        elif msg_type == "generate_domain_model_only":
            # Generate only domain model description without requesting visualization
            chat_history_text = message["content"].get("chat_history_text", "")
            return self.generate_domain_model_description_only(chat_history_text)
            
        elif msg_type == "get_domain_model":
            # Return current domain model
            return {"domain_model_description": self._current_domain_model}
            
        elif msg_type == "refine_domain_model":
            # Receive feedback from VisualizationAgent and refine model
            uml_feedback = message["content"].get("uml_feedback", "")
            plant_uml = message["content"].get("plant_uml", "")
            return self.refine_domain_model(uml_feedback, plant_uml)
            
        return {"status": "error", "message": f"Unknown message type: {msg_type}"}
    
    def handle_user_input(self, user_input, project_name):
        """Main entry point: Process user input and coordinate with specialized agents based on request classification"""
        if not user_input or not project_name:
            return {"error": "Both user input and project name are required"}
            
        self._current_project_name = project_name
        print(f"ChatAgent handling input for project: {project_name}")
            
        # Get current project state
        project_result, _ = self._project_service.get_project_data(project_name)
        current_project_data = project_result.get("project_data", {})
        
        # Get existing domain model and PlantUML
        existing_dmd = current_project_data.get("domain_model_description", 
            "Welcome to your new project! Start by describing your domain.")
        existing_plant_uml = current_project_data.get("plant_uml", 
            "@startuml\nleft to right direction\nskinparam monochrome true\ntitle Your New Project\n\nclass ExampleEntity {\n  +id: string\n  +name: string\n}\n\nnote \"Start building your domain model!\" as N1\n@enduml")
        
        # Add user input to chat history
        self._llm_service.add_to_chat_history("user", user_input)
        self._chat_history.append({"role": "user", "content": user_input})
        
        # Build chat history text for classification
        chat_history = self._llm_service.get_chat_history()
        chat_history_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in chat_history
        ])
        
        # Classify the input with enhanced request classification
        classification = self._llm_service.determine_input_type(chat_history_text)
        request_type = classification.get("request_type", "OFF_TOPIC")
        print(f"Request classification: {request_type}")
        
        # Format the assistant's response
        assistant_response = "\n".join(classification.get("suggestions", [])) if isinstance(
            classification.get("suggestions"), list) else classification.get("suggestions", "")
        
        # Add assistant response to chat history
        self._llm_service.add_to_chat_history("assistant", assistant_response)
        self._chat_history.append({"role": "assistant", "content": assistant_response})
        
        # Current domain model (may be None if not yet created)
        current_dmd = self._llm_service.get_current_domain_model_description() or existing_dmd
        
        # Handle the request based on classification type
        if request_type == "UPDATE_DESCRIPTION_ONLY" or classification.get("description_only_update", False):
            print("ChatAgent: User requested to update only the domain model description")
            
            # Generate new domain model description but keep existing PlantUML
            domain_model_result = self.send_message(
                "DomainModelAgent",
                "generate_domain_model_only",
                {"chat_history_text": chat_history_text}
            )
            
            # Get the new domain model description
            new_domain_model = domain_model_result.get("domain_model_description", existing_dmd)
            
            # Save with new description but existing PlantUML
            self._project_service.save_version(
                project_name,
                user_input,
                assistant_response,
                new_domain_model,
                existing_plant_uml  # Keep existing PlantUML
            )
            
            # Return the results
            return {
                "domain_model_description": new_domain_model,
                "suggestion": assistant_response,
                "plant_uml": existing_plant_uml  # Return existing PlantUML
            }
        
        elif request_type == "PLANTUML_ADJUSTMENT":
            print("ChatAgent: User requested PlantUML visualization adjustment")
            
            # Ask visualization agent to adjust the PlantUML without changing the domain model
            visualization_result = self.send_message(
                "VisualizationAgent",
                "adjust_plantuml",
                {
                    "domain_model_description": current_dmd,
                    "existing_plant_uml": existing_plant_uml,
                    "adjustment_request": user_input
                }
            )
            
            # Get the adjusted PlantUML
            new_plant_uml = visualization_result.get("plant_uml", existing_plant_uml)
            
            # Save with existing description but new PlantUML
            self._project_service.save_version(
                project_name,
                user_input,
                assistant_response,
                current_dmd,
                new_plant_uml
            )
            
            # Return the results
            return {
                "domain_model_description": current_dmd,
                "suggestion": assistant_response,
                "plant_uml": new_plant_uml
            }
        
        elif request_type in ["INITIAL_DOMAIN_MODEL", "UPDATE_DOMAIN_MODEL"] or classification.get("requires_domain_model_update", False):
            print("ChatAgent: Domain modeling required - initiating collaborative process")
            
            # Step 1: Request domain model generation from DomainModelAgent
            domain_model_result = self.send_message(
                "DomainModelAgent",
                "generate_domain_model",
                {"chat_history_text": chat_history_text}
            )
            
            # Extract domain model (DomainModelAgent has already initiated visualization)
            new_domain_model = domain_model_result.get("domain_model_description", existing_dmd)
            new_plant_uml = domain_model_result.get("plant_uml", existing_plant_uml)
            
            # Save the finalized version
            self._project_service.save_version(
                project_name,
                user_input,
                assistant_response,
                new_domain_model,
                new_plant_uml
            )
            
            # Return the results
            return {
                "domain_model_description": new_domain_model,
                "suggestion": assistant_response,
                "plant_uml": new_plant_uml
            }
            
        elif request_type == "DOMAIN_MODEL_QUESTION":
            print("ChatAgent: User asked question about the domain model")
            
            # For questions, we return the assistant response without changing the model
            self._project_service.save_version(
                project_name,
                user_input,
                assistant_response,
                current_dmd,
                existing_plant_uml
            )
            
            return {
                "response": assistant_response,
                "history": self._llm_service.get_chat_history(),
                "domain_model_description": current_dmd,
                "plant_uml": existing_plant_uml
            }
            
        else:  # CASUAL_COMMENT, OFF_TOPIC or any other type
            print("ChatAgent: Processing casual conversation (no domain modeling)")
            # For casual messages or insufficient info, keep existing model
            self._project_service.save_version(
                project_name,
                user_input,
                assistant_response,
                current_dmd,
                existing_plant_uml
            )
            
            # Return the results
            return {
                "response": assistant_response,
                "history": self._llm_service.get_chat_history(),
                "domain_model_description": current_dmd,
                "plant_uml": existing_plant_uml
            }
    
    def generate_domain_model_description_only(self, chat_history_text):
        """Generate only the domain model description without requesting visualization"""
        try:
            print("DomainModelAgent: Generating domain model description only (no visualization)")
            # Use LLM service to generate domain model description
            domain_model_description = self._llm_service.generate_domain_model_description(chat_history_text)
            
            # Store the domain model locally
            self._current_domain_model = domain_model_description
            
            # Notify the chat agent about the new domain model
            if "ChatAgent" in self._connected_agents:
                print("DomainModelAgent: Notifying ChatAgent about new domain model description")
                self.send_message(
                    "ChatAgent",
                    "domain_model_updated",
                    {"domain_model_description": domain_model_description}
                )
            
            # Return only the domain model description
            return {"domain_model_description": domain_model_description}
        except Exception as e:
            print(f"Error generating domain model description: {e}")
            return {"error": "Failed to generate domain model description"}