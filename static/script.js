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

        // Show the loading indicator in the chatbox
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("chat-message", "loading-message");
        loadingDiv.innerHTML = `
            <span class="loading-dots">
                <span></span><span></span><span></span>
            </span>`;
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message

        // Get references to the scenario spinner and text
        const scenarioLoading = document.getElementById("scenarioLoading");
        const scenarioText = document.getElementById("scenarioText");

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }),
        })
            .then((response) => response.json())
            .then((data) => {
                loadingDiv.remove();

                if (data.error) {
                    // Show error message word by word
                    displayBotMessageWordByWord(data.error);
                } else if (data.scenario) {
                    // Show the loading spinner only for scenarios
                    scenarioLoading.classList.remove("d-none");
                    scenarioText.textContent = "";

                    // After a short delay, hide spinner and show scenario text
                    setTimeout(() => {
                        scenarioLoading.classList.add("d-none");
                        scenarioText.textContent = data.scenario || "No detailed description provided.";

                        // Show summary in chatbox word by word
                        displayBotMessageWordByWord(data.summary);
                    }, 100); // Adjust delay as needed
                } else {
                    // General response: Show word by word
                    displayBotMessageWordByWord(data.response || "No response provided.");
                }
            })
            .catch((err) => {
                displayBotMessageWordByWord("An error occurred while processing your request.");
            })
            .finally(() => {
                scenarioLoading.classList.add("d-none");
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus();
            });
    }

    // Improved word-by-word fade-in for HTML content
    function displayBotMessageWordByWord(text) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.classList.add("chat-message", "bot-message");
        chatBox.appendChild(botMessageDiv);

        // Format the text as HTML
        const formatted = formatBotResponse(text);

        // Use a temporary div to parse HTML into nodes
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formatted;

        // Helper: Animate text nodes word by word, but append HTML blocks as a whole
        function animateNode(node, parent, cb) {
            if (node.nodeType === Node.TEXT_NODE) {
                const words = node.textContent.split(/(\s+)/); // keep spaces
                let i = 0;
                function nextWord() {
                    if (i < words.length) {
                        const span = document.createElement('span');
                        span.textContent = words[i];
                        span.style.opacity = 0;
                        parent.appendChild(span);
                        setTimeout(() => {
                            span.style.transition = "opacity 0.3s";
                            span.style.opacity = 1;
                            i++;
                            setTimeout(nextWord, 40);
                        }, 10);
                    } else if (cb) {
                        cb();
                    }
                }
                nextWord();
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const el = node.cloneNode(false);
                parent.appendChild(el);
                let child = node.firstChild;
                function nextChild() {
                    if (child) {
                        animateNode(child, el, () => {
                            child = child.nextSibling;
                            nextChild();
                        });
                    } else if (cb) {
                        cb();
                    }
                }
                nextChild();
            } else if (cb) {
                cb();
            }
        }

        // Animate all top-level nodes in order
        let idx = 0, nodes = Array.from(tempDiv.childNodes);
        function nextTopNode() {
            if (idx < nodes.length) {
                animateNode(nodes[idx], botMessageDiv, () => {
                    idx++;
                    nextTopNode();
                });
            }
        }
        nextTopNode();
    }

    // Function to generate a scenario from PlantUML
    function generateScenario() {
        const plantuml = plantumlText.textContent.trim();
        if (!plantuml) {
            alert("PlantUML text is empty. Please provide a valid diagram.");
            return;
        }

        // Show the loading spinner in the scenarioText section
        const scenarioLoading = document.getElementById("scenarioLoading");
        const scenarioText = document.getElementById("scenarioText");
        scenarioLoading.classList.remove("d-none"); // Show the spinner
        scenarioText.textContent = ""; // Clear the scenario text

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
                    // Display the detailed description in the scenarioText element
                    scenarioText.textContent = data.detailed_description;

                    // Display the summary in the chatbox
                    const summaryDiv = document.createElement("div");
                    summaryDiv.classList.add("chat-message", "bot-message");
                    summaryDiv.textContent = data.summary;
                    chatBox.appendChild(summaryDiv);
                    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while generating the scenario.");
            })
            .finally(() => {
                // Hide the loading spinner in the scenarioText section
                scenarioLoading.classList.add("d-none"); // Hide the spinner
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

        // Add buttons dynamically
        actionButtons.innerHTML = `
            <button id="feedbackBtn" class="btn btn-outline-warning">Feedback</button>
            <button id="extendBtn" class="btn btn-outline-secondary">Extend</button>
            <button id="reduceBtn" class="btn btn-outline-danger">Reduce</button>
        `;

        // Make the buttons visible and apply the fade-in animation
        actionButtons.style.visibility = "visible"; // Ensure visibility
        actionButtons.style.opacity = "1"; // Ensure opacity for fade-in effect
        actionButtons.classList.add("fade-in", "action-buttons");

        // Add event listeners for the buttons
        document.getElementById("feedbackBtn").addEventListener("click", handleFeedback);
        document.getElementById("extendBtn").addEventListener("click", handleExtend);
        document.getElementById("reduceBtn").addEventListener("click", handleReduce);
    }

    // Function to hide action buttons
    function hideActionButtons() {
        const actionButtons = document.getElementById("actionButtons");

        // Hide the buttons and reset their content
        actionButtons.style.visibility = "hidden";
        actionButtons.style.opacity = "0"; // Fade out effect
        actionButtons.innerHTML = ""; // Clear the buttons
        actionButtons.classList.remove("fade-in"); // Remove the fade-in class
    }

    // Function to display default PlantUML
    function displayDefaultPlantUML() {
        const plantumlText = document.getElementById("plantumlText");
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

    // Call this function when there is no scenario
    displayDefaultPlantUML();

    // Event listeners for sending a message
    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });
    
    // Improved Markdown to HTML formatter
    function formatBotResponse(text) {
        // Convert **bold** to <strong>
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Convert *italic* to <em>
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Convert numbered lists (1. ...) to <ol>
        html = html.replace(/(?:^|\n)(\d+\..*(?:\n\d+\..*)*)/g, function(match) {
            const items = match.trim().split(/\n/).map(line => {
                const item = line.replace(/^\d+\.\s*/, '');
                return `<li>${item.trim()}</li>`;
            }).join('');
            return `<ol>${items}</ol>`;
        });
        // Convert bullet lists (- ...) to <ul>
        html = html.replace(/(?:^|\n)(-\s.*(?:\n-\s.*)*)/g, function(match) {
            const items = match.trim().split(/\n/).map(line => {
                const item = line.replace(/^-+\s*/, '');
                return `<li>${item.trim()}</li>`;
            }).join('');
            return `<ul>${items}</ul>`;
        });
        // Convert newlines to <br> (but not inside lists)
        html = html.replace(/(?!<\/li>|<\/ol>|<\/ul>)\n/g, '<br>');
        return html;
    }
});
