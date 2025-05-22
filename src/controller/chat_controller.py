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
            
            # Add current input to chat history
            self.llm_service.add_to_chat_history("user", user_input)

            # Get updated chat history after adding the new message
            updated_chat_history = self.llm_service.chat_history.get_messages()

            # Format chat history as a single string
            chat_history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in updated_chat_history
            ])
            
            # Determine input type with enhanced analysis
            result = self.llm_service.determine_input_type(chat_history_text)
            
            # Extract all classification fields
            decision = result.get("decision", False)
            is_update = result.get("is_update", False)
            is_casual_comment = result.get("is_casual_comment", False)
            suggestions = result.get("suggestions", [])
            
            # Format the response from the suggestions array
            formatted_suggestions = "\n".join(suggestions) if isinstance(suggestions, list) else suggestions
            
            # Handle each case appropriately
            if is_casual_comment:
                # Casual comment - don't regenerate the domain model
                self.llm_service.add_to_chat_history("assistant", formatted_suggestions)
                return jsonify({
                    "response": formatted_suggestions, 
                    "history": self.llm_service.get_chat_history()
                })
                
            elif decision:
                # Enough information for domain modeling (either new model or update)
                domain_model_description = self.llm_service.generate_domain_model_description(chat_history_text)
                
                # Add response to chat history
                self.llm_service.add_to_chat_history("assistant", formatted_suggestions)
                
                return jsonify({
                    "domain_model_description": domain_model_description, 
                    "suggestion": formatted_suggestions
                })
                
            else:
                # Not enough info for domain modeling
                self.llm_service.add_to_chat_history("assistant", formatted_suggestions)
                
                return jsonify({
                    "response": formatted_suggestions, 
                    "history": self.llm_service.get_chat_history()
                })

        except Exception as e:
            print(f"Error in chat request: {e}")
            import traceback
            traceback.print_exc() # Add traceback for better error debugging
            return jsonify({"error": "An unexpected error occurred"}), 500
    
    # Remove submit_name method
    
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