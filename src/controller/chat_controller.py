from flask import request, jsonify, session
from src.model.llm_service import LLMService
from src.model.gpt2 import gpt_v2_interface 

class ChatController:
    """Controller for chat-related operations"""
    
    def __init__(self):
        self.llm_service = LLMService()
        
    def handle_chat_request(self):
        """Process user input and return domain model with suggestions"""
        try:
            # Get and validate user input
            user_input = request.json.get("message", "").strip()
            if not user_input:
                return jsonify({"error": "User input is required"}), 400

            user_name = session.get("user_name")
            if not user_name:
                return jsonify({"error": "User name is not set"}), 400
            
            # Add current input to chat history
            self.llm_service.add_to_chat_history("user", user_input)

            # Get updated chat history after adding the new message
            updated_chat_history = self.llm_service.chat_history.get_messages()

            # Format chat history as a single string
            chat_history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in updated_chat_history
            ])
            
            # print(f"\n\nChat History: {chat_history_text}\n\n")

            result = self.llm_service.determine_input_type(chat_history_text)
            suggestions = result.get("suggestions", [])
            
            # print decision 
            # print(f"Decision: {result.get('decision')}")
            
            # Check if there's enough info for a domain model based on decision
            if result.get("decision", False):          
                # Generate domain model description using the entire chat history
                domain_model_description = self.llm_service.generate_domain_model_description(chat_history_text)
                formatted_suggestions = "**Suggestions to improve your domain model:**\n" + "\n".join([f"- {suggestion}" for suggestion in suggestions])
                
                # Add suggestions to chat history
                self.llm_service.add_to_chat_history("assistant", formatted_suggestions)
                
                return jsonify({"domain_model_description": domain_model_description, "suggestion": formatted_suggestions})
            
            else:
                # Not enough info for domain modeling - show suggestions for what's needed
                formatted_suggestions = "**To create a domain model, I need more information:**\n" + "\n".join([f"- {suggestion}" for suggestion in suggestions])
                
                # Add suggestions to chat history
                self.llm_service.add_to_chat_history("assistant", formatted_suggestions)
                
                return jsonify({"response": formatted_suggestions, "history": self.llm_service.get_chat_history()})

        except Exception as e:
            print(f"Error in chat request: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    
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