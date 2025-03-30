from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from Adapters.GPT_v2.gpt2 import *
import plantuml
from flask import Flask, render_template, request
import shutil

app = Flask(__name__)

# Initialize the OpenAI client
load_dotenv(override=True)
client = AzureOpenAI(
    api_version=os.getenv("GPT_API_VERSION"),
    api_key=os.getenv("API_KEY"),
    azure_endpoint=os.getenv("ENDPOINT"),
)

@app.route('/', methods=['GET', 'POST'])
def index():
    plantuml_image = None
    if request.method == 'POST':
        user_prompt = request.form['prompt']

        # Prepare prompt
        prompts = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_prompt},
        ]

        # Generate response
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"), messages=prompts
        )

        # Extracted description
        uml_text = response.choices[0].message.content
        print("Generated UML Text: ", uml_text)

        # Generate PlantUML from GPT-2 interface
        plantuml_output = gpt_v2_interface(uml_text, client)
        print("Generated PlantUML Output: ", plantuml_output)

        # Ensure the static folder exists
        static_folder = "static"
        if not os.path.exists(static_folder):
            os.makedirs(static_folder)

        # Save the PlantUML output to a file
        uml_file_path = os.path.join(static_folder, "domain_model.txt")
        with open(uml_file_path, "w") as file:
            file.write(plantuml_output)

        # Generate the PlantUML image and save it
        plantuml_image_path = os.path.join(static_folder, "domain_model.png")
        
        try:
            # Create the PlantUML object with URL
            plantuml_instance = plantuml.PlantUML(url="http://www.plantuml.com/plantuml/png/")
            
            # Process the UML content and save it as a .png file
            with open(uml_file_path, "r") as file:
                uml_content = file.read()

            # Generate and save the image to the static folder
            with open(plantuml_image_path, "wb") as img_file:
                img_file.write(plantuml_instance.processes(uml_content))
            print("PlantUML image saved successfully.")

            # Image is now saved as static/domain_model.png
            plantuml_image = "/static/domain_model.png"
            
        except Exception as e:
            print(f"Error generating PlantUML image: {e}")
        
        # Optional: Delete the temporary text file after processing
        if os.path.exists(uml_file_path):
            os.remove(uml_file_path)

    return render_template('index.html', plantuml_image=plantuml_image)

if __name__ == "__main__":
    app.run(debug=True)
