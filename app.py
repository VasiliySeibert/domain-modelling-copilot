from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

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

if __name__ == "__main__":
    app.run(debug=True)