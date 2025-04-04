document.addEventListener("DOMContentLoaded", () => {
    const userNameInput = document.getElementById("userName");

    // Load saved name
    const savedName = sessionStorage.getItem("userData");
    if (savedName) {
        userNameInput.value = savedName;
    }

    // Save username on blur
    userNameInput.addEventListener("blur", () => {
        sessionStorage.setItem("userData", userNameInput.value);
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
