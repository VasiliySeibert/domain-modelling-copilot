document.addEventListener("DOMContentLoaded", () => {
    const userNameInput = document.getElementById("userName");
    const submitNameBtn = document.getElementById("submitNameBtn"); 

    // Load saved name from sessionStorage
    const savedName = sessionStorage.getItem("userData");
    if (savedName) {
        userNameInput.value = savedName;
    }

    // Save username on button click instead of blur
    submitNameBtn.addEventListener("click", () => {
        const name = userNameInput.value.trim();
        if (name) {
            sessionStorage.setItem("userData", name);
            console.log("Name saved:", name);
        } else {
            alert("Please enter a name.");
        }
    });
});


document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chatBox");
    const loadingIndicator = document.getElementById("loadingIndicator");
    const actionButtons = document.getElementById("actionButtons");
    let isFirstResponse = true; // Track if it's the first response

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
        const message = userInput.value.trim();
        if (message === "") return;

        // Disable input and button while processing
        userInput.disabled = true;
        sendButton.disabled = true;

        // Show the loading indicator
        loadingIndicator.classList.remove("d-none");

        // Send the message to the server
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    renderChatHistory(data.history); // Render the updated chat history

                    // Show action buttons after the first response
                    if (isFirstResponse) {
                        actionButtons.style.visibility = "visible"; // Make visible
                        actionButtons.classList.add("show"); // Add animation class
                        isFirstResponse = false;
                    }
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while processing your request.");
            })
            .finally(() => {
                // Hide the loading indicator
                loadingIndicator.classList.add("d-none");

                // Re-enable input and button
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.value = ""; // Clear the input field
                userInput.focus(); // Focus back on the input field
            });
    }

    // Add event listeners for action buttons
    actionButtons.addEventListener("click", (event) => {
        if (event.target.tagName === "BUTTON") {
            const action = event.target.textContent.trim();
            alert(`Action triggered: ${action}`);
        }
    });

    // Event listeners for sending a message
    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chatBox");
    const plantumlText = document.getElementById("plantumlText");
    const scenarioText = document.getElementById("scenarioText");
    const loadingIndicator = document.getElementById("loadingIndicator");

    // Function to process the scenario
    function processScenario() {
        const scenario = userInput.value.trim();
        if (!scenario) {
            alert("Please enter a scenario.");
            return;
        }

        // Disable input and button while processing
        userInput.disabled = true;
        sendButton.disabled = true;

        // Show the loading indicator
        loadingIndicator.classList.remove("d-none");

        // Send the scenario to the server
        fetch("/process_scenario", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: scenario }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else if (data.plantuml) {
                    // Update the PlantUML content
                    plantumlText.textContent = data.plantuml;

                    // Update the scenario text content
                    scenarioText.textContent = data.scenario;

                    // Display the summary in the chatbox
                    const summaryDiv = document.createElement("div");
                    summaryDiv.classList.add("chat-message", "bot-message");
                    summaryDiv.textContent = data.summary;
                    chatBox.appendChild(summaryDiv);
                    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
                } else {
                    // Display a normal chatbot response
                    const botMessageDiv = document.createElement("div");
                    botMessageDiv.classList.add("chat-message", "bot-message");
                    botMessageDiv.textContent = data.response;
                    chatBox.appendChild(botMessageDiv);
                    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while processing the scenario.");
            })
            .finally(() => {
                // Hide the loading indicator
                loadingIndicator.classList.add("d-none");

                // Re-enable input and button
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.value = ""; // Clear the input field
                userInput.focus(); // Focus back on the input field
            });
    }

    // Event listener for the send button
    sendButton.addEventListener("click", processScenario);

    // Allow pressing Enter to submit the scenario
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            processScenario();
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const plantumlText = document.getElementById("plantumlText");
    const scenarioText = document.getElementById("scenarioText");
    const chatBox = document.getElementById("chatBox");
    const generateScenarioButton = document.createElement("button");

    // // Add a button to generate the scenario
    // generateScenarioButton.textContent = "Generate Scenario";
    // generateScenarioButton.classList.add("btn", "btn-primary", "mt-3");
    // plantumlText.parentElement.appendChild(generateScenarioButton);

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

    // Add event listener to the button
    generateScenarioButton.addEventListener("click", generateScenario);
});

document.addEventListener("DOMContentLoaded", () => {
    const scenarioText = document.getElementById("scenarioText");
    const plantumlText = document.getElementById("plantumlText");
    const generateUMLButton = document.createElement("button");

    // Add a button to generate UML
    generateUMLButton.textContent = "Generate UML";
    generateUMLButton.classList.add("btn", "btn-primary", "mt-3");
    scenarioText.parentElement.appendChild(generateUMLButton);

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

    // Add event listener to the button
    generateUMLButton.addEventListener("click", generateUML);
});
