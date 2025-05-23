class ChatView {
    constructor() {
        this.elements = {
            chatBox: document.getElementById("chatBox"),
            userInput: document.getElementById("userInput"),
            sendButton: document.getElementById("sendButton"),
           
            actionButtons: document.getElementById("actionButtons")
        };
    }
    
    
    bindSendMessage(handler) {
        // Button click handler
        this.elements.sendButton.addEventListener("click", () => {
            handler(this.elements.userInput.value.trim());
        });
        
        // Enter key handler
        this.elements.userInput.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                handler(this.elements.userInput.value.trim());
            }
        });
    }
    
    display_input(message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", "user-message");
        messageDiv.textContent = message;
        this.elements.chatBox.appendChild(messageDiv);
        this.autoScrollChatBox();
    }
    
    displayBotMessage(content) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.classList.add("chat-message", "bot-message");
        botMessageDiv.innerHTML = marked.parse(content);
        this.elements.chatBox.appendChild(botMessageDiv);
        this.autoScrollChatBox();
        
        // Dispatch event for chat message received
        document.dispatchEvent(new CustomEvent('chatMessageReceived'));
    }
    
    displayErrorMessage(errorText) {
        const errorDiv = document.createElement("div");
        errorDiv.classList.add("chat-message", "error-message");
        errorDiv.textContent = errorText;
        this.elements.chatBox.appendChild(errorDiv);
        this.autoScrollChatBox();
    }
    
    showLoadingIndicator() {
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("chat-message", "loading-message");
        loadingDiv.innerHTML = `<span class="loading-dots"><span></span><span></span><span></span></span>`;
        this.elements.chatBox.appendChild(loadingDiv);
        this.autoScrollChatBox();
        return loadingDiv;
    }
    
    clearInput() {
        this.elements.userInput.value = "";
    }
    
    disableInput() {
        this.elements.userInput.disabled = true;
        this.elements.sendButton.disabled = true;
    }
    
    enableInput() {
        this.elements.userInput.disabled = false;
        this.elements.sendButton.disabled = false;
        this.elements.userInput.focus();
    }
    
    autoScrollChatBox() {
        this.elements.chatBox.scrollTop = this.elements.chatBox.scrollHeight;
    }
    
    showActionButtons() {
        this.elements.actionButtons.style.visibility = "visible";
        this.elements.actionButtons.style.opacity = "1";
    }
    
    hideActionButtons() {
        this.elements.actionButtons.style.visibility = "hidden";
        this.elements.actionButtons.style.opacity = "0";
    }
    
    getChatHistory() {
        const chatHistory = [];
        document.querySelectorAll(".chat-message").forEach(msg => {
            if (msg.classList.contains("user-message")) {
                chatHistory.push({
                    "role": "user", 
                    "content": msg.textContent.trim()
                });
            } else if (msg.classList.contains("bot-message")) {
                chatHistory.push({
                    "role": "assistant", 
                    "content": msg.textContent.trim()
                });
            }
        });
        return chatHistory;
    }
}