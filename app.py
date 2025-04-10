from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from gpt2 import gpt_v2_interface

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session handling

# Initialize the OpenAI client
load_dotenv(override=True)
client = AzureOpenAI(
    api_version=os.getenv("GPT_API_VERSION"),
    api_key=os.getenv("API_KEY"),
    azure_endpoint=os.getenv("ENDPOINT"),
)

# Function to get chatbot response from OpenAI API
def chatbot_response(user_input):
    try:
        prompts = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ]

        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Sorry, I couldn't process your request."

# Initialize chat history as a list of dictionaries
chat_history = []

@app.route("/")
def home():
    global chat_history
    chat_history = []  # Reset chat history on page load
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history
    try:
        # Get user message from the request
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Add the user's message to the chat history
        chat_history.append({"role": "user", "content": user_message})

        # Prepare the prompts with the chat history
        prompts = [{"role": "system", "content": "You are a helpful assistant."}] + chat_history

        # Get response from chatbot
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )
        bot_reply = response.choices[0].message.content.strip()

        # Add the bot's response to the chat history
        chat_history.append({"role": "assistant", "content": bot_reply})

        # Example of a formatted response
        formatted_reply = f"""
        <p><b>Response:</b></p>
        <ul>
            <li><i>{bot_reply}</i></li>
        </ul>
        """

        return jsonify({"response": formatted_reply, "history": chat_history})
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": "An error occurred"}), 500

@app.route("/process_scenario", methods=["POST"])
def process_scenario():
    """Process the user-provided scenario and return the PlantUML, summary, and scenario text."""
    try:
        # Get the scenario text from the request
        scenario_text = request.json.get("message", "").strip()
        if not scenario_text:
            return jsonify({"error": "Scenario text is required"}), 400

        # Check if the input is sufficient for generating a scenario
        if len(scenario_text.split()) < 5:  # Example condition: input has fewer than 5 words
            # Return a normal chatbot response
            bot_reply = chatbot_response(scenario_text)
            return jsonify({"response": bot_reply, "history": []})

        # Call gpt_v2_interface to process the scenario and generate PlantUML
        plant_uml = gpt_v2_interface(scenario_text, client)

        # Generate a detailed scenario description from the PlantUML
        prompts = [
            {"role": "system", "content": "You are an expert in converting UML diagrams into natural language scenarios."},
            {"role": "user", "content": f"Convert the following PlantUML diagram into a detailed scenario:\n\n{plant_uml}"}
        ]
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=prompts
        )
        detailed_description = response.choices[0].message.content.strip()

        # Generate a summary from the detailed description
        summary_prompt = [
            {"role": "system", "content": "You are an expert in summarizing text."},
            {"role": "user", "content": f"Summarize the following scenario in one or two sentences:\n\n{detailed_description}"}
        ]
        summary_response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=summary_prompt
        )
        summary = summary_response.choices[0].message.content.strip()

        # Return the PlantUML, summary, and detailed scenario
        return jsonify({"plantuml": plant_uml, "summary": summary, "scenario": detailed_description})
    except Exception as e:
        print(f"Error processing scenario: {e}")
        return jsonify({"error": "An error occurred while processing the scenario"}), 500

@app.route("/generate_scenario", methods=["POST"])
def generate_scenario():
    """Generate a scenario text from the given PlantUML diagram."""
    try:
        # Get the PlantUML text from the request
        plantuml_text = request.json.get("plantuml", "").strip()
        if not plantuml_text:
            return jsonify({"error": "PlantUML text is required"}), 400

        # Use GPT to generate a scenario from the PlantUML
        prompts = [
            {"role": "system", "content": "You are an expert in converting UML diagrams into natural language scenarios."},
            {"role": "user", "content": f"Convert the following PlantUML diagram into a detailed scenario:\n\n{plantuml_text}"}
        ]

        # Call the GPT model
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=prompts
        )

        # Extract the generated scenario
        detailed_description = response.choices[0].message.content.strip()

        # Generate a summary from the detailed description
        summary_prompt = [
            {"role": "system", "content": "You are an expert in summarizing text."},
            {"role": "user", "content": f"Summarize the following scenario in one or two sentences:\n\n{detailed_description}"}
        ]
        summary_response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=summary_prompt
        )
        summary = summary_response.choices[0].message.content.strip()

        # Return both the summary and the detailed description
        return jsonify({"summary": summary, "detailed_description": detailed_description})
    except Exception as e:
        print(f"Error generating scenario: {e}")
        return jsonify({"error": "An error occurred while generating the scenario"}), 500

@app.route("/generate_uml", methods=["POST"])
def generate_uml():
    """Generate UML text from the given scenario text."""
    try:
        # Get the scenario text from the request
        scenario_text = request.json.get("scenarioText", "").strip()
        if not scenario_text:
            return jsonify({"error": "Scenario text is required"}), 400

        # Call gpt_v2_interface to process the scenario and generate PlantUML
        plant_uml = gpt_v2_interface(scenario_text, client)

        # Return the generated PlantUML
        return jsonify({"plantuml": plant_uml})
    except Exception as e:
        print(f"Error generating UML: {e}")
        return jsonify({"error": "An error occurred while generating the UML"}), 500

if __name__ == "__main__":
    app.run(debug=True)