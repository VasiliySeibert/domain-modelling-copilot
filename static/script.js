document.addEventListener("DOMContentLoaded", () => {
    // ============================
    // DOM Elements
    // ============================
    const userNameInput = document.getElementById("userName");
    const submitNameBtn = document.getElementById("submitNameBtn");
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chatBox");
    const plantumlText = document.getElementById("plantumlText");
    const scenarioText = document.getElementById("scenarioText");
    const actionButtons = document.getElementById("actionButtons");

    // ============================
    // Initialization
    // ============================
    // Load saved name from sessionStorage
    const savedName = sessionStorage.getItem("userName");
    if (savedName) {
        userNameInput.value = savedName;
    }

    // Initialize default PlantUML
    displayDefaultPlantUML();

    // ============================
    // Event Listeners
    // ============================
    submitNameBtn.addEventListener("click", handleNameSubmission);
    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    // ============================
    // Core Functions
    // ============================

    // Handle name submission
    function handleNameSubmission() {
        const name = userNameInput.value.trim();
        if (!name) {
            alert("Please enter a name.");
            return;
        }

        sessionStorage.setItem("userName", name);

        fetch("/submit_name", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert("Name saved successfully! You can now start chatting.");
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while saving the name.");
            });
    }

    // Send a message
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        const userName = sessionStorage.getItem("userName");
        if (!userName) {
            alert("Please enter your name before starting the chat.");
            return;
        }

        // Display the user's message in the chatbox
        appendMessage("user", message);

        // Clear the input field and disable input while processing
        userInput.value = "";
        toggleInput(false); // Disable input and send button

        // Show loading indicator
        const loadingDiv = createLoadingIndicator();
        chatBox.appendChild(loadingDiv);
        autoScrollChatBox();

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                loadingDiv.remove();

                if (data.error) {
                    displayErrorMessage(data.error); // Display error in the chatbox
                } else if (data.scenario) {
                    // Display scenario and summary
                    scenarioText.textContent = data.scenario || "No detailed description provided.";
                    displayBotMessageWordByWord(data.summary, showActionButtons);
                } else {
                    // General response
                    appendMessage("bot", data.response || "No response provided.");
                }
            })
            .catch((err) => {
                loadingDiv.remove();
                displayErrorMessage("An error occurred while processing your request. Please try again.");
                console.error("Error:", err);
            })
            .finally(() => {
                toggleInput(true); // Re-enable input and send button
            });
    }

    // ============================
    // Helper Functions
    // ============================

    // Append a message to the chatbox
    function appendMessage(role, content) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", `${role}-message`);
        messageDiv.textContent = content;
        chatBox.appendChild(messageDiv);
        autoScrollChatBox();
    }

    // Toggle input and send button
    function toggleInput(enable) {
        userInput.disabled = !enable;
        sendButton.disabled = !enable;
        if (enable) userInput.focus();
    }

    // Create a loading indicator
    function createLoadingIndicator() {
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("chat-message", "loading-message");
        loadingDiv.innerHTML = `
            <span class="loading-dots">
                <span></span><span></span><span></span>
            </span>`;
        return loadingDiv;
    }

    // Display bot messages word by word
    function displayBotMessageWordByWord(text, callback) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.classList.add("chat-message", "bot-message");
        chatBox.appendChild(botMessageDiv);

        const words = text.split(" ");
        let index = 0;

        function displayNextWord() {
            if (index < words.length) {
                botMessageDiv.textContent += words[index] + " ";
                index++;
                setTimeout(displayNextWord, 50); // Adjust delay as needed
            } else if (callback) {
                callback();
            }
        }

        displayNextWord();
    }

    // Auto-scroll the chatbox
    function autoScrollChatBox() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Show action buttons
    function showActionButtons() {
        actionButtons.style.visibility = "visible";
        actionButtons.style.opacity = "1";
    }

    // Hide action buttons
    function hideActionButtons() {
        actionButtons.style.visibility = "hidden";
        actionButtons.style.opacity = "0";
    }

    // Display error messages
    function displayErrorMessage(errorText) {
        const errorDiv = document.createElement("div");
        errorDiv.classList.add("chat-message", "error-message");
        errorDiv.textContent = errorText;
        chatBox.appendChild(errorDiv);
        autoScrollChatBox();
    }

    // Display default PlantUML
    function displayDefaultPlantUML() {
        plantumlText.textContent = `@startuml
class User {
    +name: String
    +email: String
    +login(): void
}

class Product {
    +id: int
    +name: String
    +price: float
}

User "1" -- "0..*" Product : purchases
@enduml`;
    }
});
