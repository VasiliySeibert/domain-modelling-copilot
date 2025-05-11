from flask import request, jsonify, session
from src.model.llm_service import LLMService
from src.model.chat_history import ChatHistory
from src.model.scenario import Scenario
from src.model.gpt2 import gpt_v2_interface 

class ChatController:
    """Controller for chat-related operations"""
    
    def __init__(self):
        self.llm_service = LLMService()
        
    def handle_chat_request(self):
        """Process user input and return appropriate response"""
        try:
            raw_input = request.json.get("message", "").strip()
            if not raw_input:
                return jsonify({"error": "Message is required. Please enter a valid message."}), 400

            user_name = session.get("user_name")
            if not user_name:
                return jsonify({"error": "User name is not set. Please submit your name first."}), 400
            
            # Validate input
            if not isinstance(raw_input, str):
                return jsonify({"error": "User input must be a string"}), 400
            user_input = raw_input.strip()
            
            # Add to chat history
            self.llm_service.add_to_chat_history("user", user_input)
            
            # Determine input type
            input_type = self.llm_service.determine_input_type(user_input)

            if input_type == "general":
                # Generate general response
                response = self.llm_service.generate_response(user_name)
                return jsonify({"response": response, "history": self.llm_service.get_chat_history()})
            
            elif input_type == "scenario":
                # Generate scenario
                scenario = self.llm_service.generate_scenario(user_input)
                
                # Generate summary
                summary = self.llm_service.generate_summary(scenario)
                
                return jsonify({"scenario": scenario, "summary": summary})
            else:
                return jsonify({"error": "Unable to classify the input. Please rephrase your query."}), 400

        except Exception as e:
            print(f"Error in chat request: {e}")
            return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500
    
    def submit_name(self):
        """Store user's name in session"""
        try:
            user_name = request.json.get("name", "").strip()
            if not user_name:
                return jsonify({"error": "Name is required"}), 400

            session["user_name"] = user_name
            return jsonify({"message": "Name saved successfully!", "name": user_name})
        except Exception as e:
            print(f"Error storing name: {e}")
            return jsonify({"error": "An error occurred while storing the name"}), 500
    
    def generate_uml(self):
        """Generate UML diagram from scenario"""
        try:
            scenario_text = request.json.get("scenarioText", "").strip()
            if not scenario_text:
                return jsonify({"error": "Domain Model Description is required"}), 400

            client = self.llm_service.client
            plant_uml = gpt_v2_interface(scenario_text, client)
            return jsonify({"plantuml": plant_uml})
        except Exception as e:
            print(f"Error generating UML: {e}")
            return jsonify({"error": "An error occurred while generating the UML"}), 500
    
    def get_current_scenario(self):
        """Retrieve the current scenario"""
        scenario = self.llm_service.get_current_scenario()
        return jsonify({"scenario": scenario})