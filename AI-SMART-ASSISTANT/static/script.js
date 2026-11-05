// ========================================
// 1. GET HTML ELEMENTS
// ========================================

const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const chatContainer = document.getElementById("chatContainer");
const themeButton = document.getElementById("themeButton");


// ========================================
// 2. ADD MESSAGE TO SCREEN
// ========================================

function addMessage(text, className) {

    const message = document.createElement("div");

    message.className = className;

    // textContent prevents HTML injection.
    message.textContent = text;

    messages.appendChild(message);

    chatContainer.scrollTop = chatContainer.scrollHeight;

    return message;
}


// ========================================
// 3. SEND MESSAGE TO GEMINI
// ========================================

chatForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const userMessage = messageInput.value.trim();

    if (!userMessage) {
        return;
    }

    // Display user message.
    addMessage(userMessage, "user-message");

    messageInput.value = "";

    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    const loadingMessage = addMessage(
        "Gemini is preparing your answer...",
        "bot-message"
    );

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                message: userMessage,

                conversation_id: Number(CONVERSATION_ID)

            })

        });

        const data = await response.json();

        loadingMessage.remove();

        if (!response.ok) {

            addMessage(
                data.error || "Something went wrong.",
                "bot-message"
            );

            return;
        }

        // Display Gemini response.
        addMessage(data.reply, "bot-message");

    }

    catch (error) {

        loadingMessage.remove();

        addMessage(
            "Unable to connect to the server. Please try again.",
            "bot-message"
        );

        console.error(error);

    }

    finally {

        sendButton.disabled = false;
        sendButton.textContent = "Send";

        messageInput.focus();

    }

});


// ========================================
// 4. DARK AND LIGHT MODE (CORRECTED CLASS NAME)
// ========================================

const savedTheme = localStorage.getItem("assistant-theme");

// Your style.css runs Dark Mode by default, so we look for 'light' preference
if (savedTheme === "light") {
    document.body.classList.add("light-theme");
}

themeButton.addEventListener("click", function() {

    // Matches the 'body.light-theme' rule in your CSS
    document.body.classList.toggle("light-theme");

    const currentTheme =
        document.body.classList.contains("light-theme")
        ? "light"
        : "dark";

    localStorage.setItem("assistant-theme", currentTheme);

});


// ========================================
// 5. AUTOMATIC SCROLL
// ========================================

window.addEventListener("load", function() {

    chatContainer.scrollTop = chatContainer.scrollHeight;

});
// ========================================
// 4. DARK AND LIGHT MODE
// ========================================

// Run theme detection as soon as the file loads
(function() {
    const savedTheme = localStorage.getItem("assistant-theme");
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
    }
})();

// Attach click event listener to the toggle button
themeButton.addEventListener("click", function() {
    // Toggle the class name directly on the body element
    document.body.classList.toggle("light-theme");

    // Save the active preference to localStorage so it stays active
    const currentTheme = document.body.classList.contains("light-theme") ? "light" : "dark";
    localStorage.setItem("assistant-theme", currentTheme);
});
