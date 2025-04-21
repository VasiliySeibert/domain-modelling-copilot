document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const userNameInput = document.getElementById("userName");
    const submitNameBtn = document.getElementById("submitNameBtn");
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chatBox");
    const loadingIndicator = document.getElementById("loadingIndicator");
    const plantumlText = document.getElementById("plantumlText");
    const scenarioText = document.getElementById("scenarioText");

    // Load saved name from sessionStorage
    const savedName = sessionStorage.getItem("userName");
    if (savedName) {
        userNameInput.value = savedName;
    }

    // Save username on button click
    submitNameBtn.addEventListener("click", () => {
        const name = userNameInput.value.trim();
        if (name) {
            // Save the name in sessionStorage
            sessionStorage.setItem("userName", name);

            // Send the name to the Flask backend
            fetch("/submit_name", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: name }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        alert(data.error); // Show error message if any
                    } else {
                        alert(data.message); // Show success message
                    }
                })
                .catch((err) => {
                    console.error("Error:", err);
                    alert("An error occurred while saving the name.");
                });
        } else {
            alert("Please enter a name.");
        }
    });

    // Function to render the chat history
    function renderChatHistory(history) {
        chatBox.innerHTML = ""; // Clear the chatbox
        history.forEach((message) => {
            const messageDiv = document.createElement("div");
            messageDiv.classList.add("chat-message");

            if (message.role === "user") {
                messageDiv.classList.add("user-message");
                messageDiv.textContent = message.content;
            } else if (message.role === "assistant") {
                messageDiv.classList.add("bot-message");
                messageDiv.innerHTML = message.content; // Render HTML for bot messages
            }

            chatBox.appendChild(messageDiv);
        });
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
    }

    // Function to send a message
    function sendMessage() {
        // Check if the user's name is set in sessionStorage
        const userName = sessionStorage.getItem("userName");
        if (!userName) {
            alert("Please enter your name before starting a conversation.");
            const userNameInput = document.getElementById("userName");
            userNameInput.focus();
            return;
        }

        const message = userInput.value.trim();
        if (message === "") return;

        // Display the user's message immediately in the chat box
        const userMessageDiv = document.createElement("div");
        userMessageDiv.classList.add("chat-message", "user-message");
        userMessageDiv.textContent = message;
        chatBox.appendChild(userMessageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message

        // Clear the input field and disable input and button while processing
        userInput.value = "";
        userInput.disabled = true;
        sendButton.disabled = true;

        // Show the loading indicator
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("chat-message", "loading-message");
        loadingDiv.innerHTML = `
            <span class="loading-dots">
                <span></span><span></span><span></span>
            </span>`;
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message

        // Send the message to the server
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    console.error(data.error);
                    loadingDiv.textContent = "An error occurred while processing your request.";
                } else if (data.scenario) {
                    // Scenario-based response: Display in the scenarioText section
                    scenarioText.textContent = data.scenario || "No detailed description provided.";
                    loadingDiv.remove(); // Remove the loading indicator

                    // Show action buttons
                    showActionButtons();
                } else {
                    // General response: Display in the chat box
                    loadingDiv.classList.remove("loading-message");
                    loadingDiv.classList.add("bot-message");
                    loadingDiv.innerHTML = data.response || "No response provided.";

                    // Hide action buttons if they are visible
                    hideActionButtons();
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                loadingDiv.textContent = "An error occurred while processing your request.";
            })
            .finally(() => {
                // Re-enable input and button
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus(); // Focus back on the input field
            });
    }

    // Function to generate a scenario from PlantUML
    function generateScenario() {
        const plantuml = plantumlText.textContent.trim();
        if (!plantuml) {
            alert("PlantUML text is empty. Please provide a valid diagram.");
            return;
        }

        // Send the PlantUML text to the server
        fetch("/generate_scenario", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ plantuml: plantuml }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    // Display the summary in the chatbox
                    const summaryDiv = document.createElement("div");
                    summaryDiv.classList.add("chat-message", "bot-message");
                    summaryDiv.textContent = data.summary;
                    chatBox.appendChild(summaryDiv);
                    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message

                    // Display the detailed description in the scenarioText element
                    scenarioText.textContent = data.detailed_description;
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while generating the scenario.");
            });
    }

    // Function to generate UML from scenarioText
    function generateUML() {
        const scenario = scenarioText.textContent.trim();
        if (!scenario) {
            alert("Scenario text is empty. Please provide a valid scenario.");
            return;
        }

        // Send the scenario text to the server
        fetch("/generate_uml", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenarioText: scenario }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    // Update the PlantUML content
                    plantumlText.textContent = data.plantuml;
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while generating the UML.");
            });
    }

    // Function to show action buttons
    function showActionButtons() {
        const actionButtons = document.getElementById("actionButtons");
        actionButtons.innerHTML = `
            <button id="feedbackBtn" class="btn btn-outline-warning">Feedback</button>
            <button id="extendBtn" class="btn btn-outline-secondary">Extend</button>
            <button id="reduceBtn" class="btn btn-outline-danger">Reduce</button>
        `;

        // Add the fade-in class for animation
        actionButtons.classList.add("fade-in", "action-buttons");
        actionButtons.style.visibility = "visible"; // Make the buttons visible

        // Add event listeners for the buttons
        document.getElementById("feedbackBtn").addEventListener("click", handleFeedback);
        document.getElementById("extendBtn").addEventListener("click", handleExtend);
        document.getElementById("reduceBtn").addEventListener("click", handleReduce);
    }

    // Function to hide action buttons
    function hideActionButtons() {
        const actionButtons = document.getElementById("actionButtons");
        actionButtons.style.visibility = "hidden"; // Hide the buttons
        actionButtons.innerHTML = ""; // Clear the buttons
        actionButtons.classList.remove("fade-in"); // Remove the fade-in class
    }

    // Event listeners for sending a message
    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
});
