from flask import request, jsonify
from src.model.AgentChat import AgentChat
from src.model.AgentDomainModelDescription import AgentDomainModelDescription
from src.model.AgentDomainModelVisualization import AgentDomainModelVisualization
import traceback

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
            
            # Delegate handling to the ChatAgent
            result = self.chat_agent.handle_user_input(user_input, project_name)
            
            if "error" in result:
                return jsonify({"error": result["error"]}), 400
                
            return jsonify(result)

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