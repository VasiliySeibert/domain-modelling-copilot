from flask import Flask, render_template, request, jsonify, session
from openai_client import OpenAIClient  # Utility class
from gpt2 import gpt_v2_interface
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session handling

# Initialize the OpenAI client once
OpenAIClient.initialize()

chat_history = []
scenarios = []  # Stores all scenarios generated during the chat session

@app.route("/")
def home():
    """Render the home page and reset chat history."""
    global chat_history
    chat_history = []  # Reset chat history on page load
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages and classify them as 'general' or 'scenario'."""
    global chat_history, scenarios
    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Message is required. Please enter a valid message."}), 400

        user_name = session.get("user_name")
        if not user_name:
            return jsonify({"error": "User name is not set. Please submit your name first."}), 400

        chat_history.append({"role": "user", "content": user_message})

        classification = classify_input(user_message)

        if classification == "general":
            response = generate_general(user_name, chat_history)
            return response
        elif classification == "scenario":
            detailed_description = generate_scenario(user_message)
            summary = generate_summary(detailed_description)
            scenarios.append(detailed_description)
            chat_history.append({"role": "assistant", "content": summary})
            return jsonify({"scenario": detailed_description, "summary": summary})
        else:
            return jsonify({"error": "Unable to classify the input. Please rephrase your query."}), 400

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@app.route("/submit_name", methods=["POST"])
def submit_name():
    """Store the user's name in the session."""
    try:
        user_name = request.json.get("name", "").strip()
        if not user_name:
            return jsonify({"error": "Name is required"}), 400

        session["user_name"] = user_name
        return jsonify({"message": "Name saved successfully!", "name": user_name})
    except Exception as e:
        print(f"Error storing name: {e}")
        return jsonify({"error": "An error occurred while storing the name"}), 500

def generate_general(user_name, chat_history):
    """Generate a general response using GPT."""
    try:
        prompts = [
            {"role": "system", "content": f"You are a helpful assistant. The user's name is {user_name}."}
        ] + chat_history

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        bot_reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": bot_reply})
        return jsonify({"response": bot_reply, "history": chat_history})
    except Exception as e:
        print(f"Error generating general response: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

def generate_scenario(scenario_text):
    """Generate a detailed scenario from the given user input."""
    try:
        prompts = [
            {
                "role": "system",
                "content": (
                    "You are an expert in domain modeling and UML class diagram generation. "
                    "Your task is to convert user inputs into clear and concise scenarios that include relevant entities, attributes, and relationships."
                    "Do not include Title, or any other unnecessary information in the output."
                )
            },
            {"role": "user", "content": f"Generate a clear and structured scenario for the following input:\n\n{scenario_text}"}
        ]

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating scenario: {e}")
        return "An error occurred while generating the scenario."

@app.route("/generate_uml", methods=["POST"])
def generate_uml():
    """Generate UML text from the given scenario text."""
    try:
        scenario_text = request.json.get("scenarioText", "").strip()
        if not scenario_text:
            return jsonify({"error": "Scenario text is required"}), 400

        client = OpenAIClient.get_client()
        plant_uml = gpt_v2_interface(scenario_text, client)
        return jsonify({"plantuml": plant_uml})
    except Exception as e:
        print(f"Error generating UML: {e}")
        return jsonify({"error": "An error occurred while generating the UML"}), 500

@app.route("/generate_summary", methods=["POST"])
def generate_summary_endpoint():
    """Generate a summary from the given detailed scenario."""
    try:
        detailed_description = request.json.get("detailed_description", "").strip()
        if not detailed_description:
            return jsonify({"error": "Detailed description is required"}), 400

        summary = generate_summary(detailed_description)
        return jsonify({"summary": summary})
    except Exception as e:
        print(f"Error generating summary: {e}")
        return jsonify({"error": "An error occurred while generating the summary"}), 500

def generate_summary(detailed_description):
    """Generate a summary from the given detailed scenario."""
    try:
        prompts = [
            {"role": "system", "content": "Summarize the following scenario in one or two sentences."},
            {"role": "user", "content": f"Summarize the following scenario:\n\n{detailed_description}"}
        ]

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "An error occurred while generating the summary."

def classify_input(user_message):
    """Classify the user input as 'general' or 'scenario'."""
    try:
        prompts = [
            {"role": "system", "content": "Classify the input as either 'general' or 'scenario'."},
            {"role": "user", "content": f"Input: {user_message}"}
        ]

        client = OpenAIClient.get_client()
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Error classifying input: {e}")
        return "general"  # Default to "general" in case of an error

@app.route("/get_scenarios", methods=["GET"])
def get_scenarios():
    """Retrieve all stored scenarios."""
    return jsonify({"scenarios": scenarios})

if __name__ == "__main__":
    app.run(debug=True)