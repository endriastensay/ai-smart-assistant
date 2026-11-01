
/* =========================
   1. SEND MESSAGE TO FLASK
========================= */

async function sendMessage() {

    const input = document.getElementById("userInput");
    const messages = document.getElementById("messages");
    const button = document.getElementById("sendButton");

    const message = input.value.trim();

    if (message === "") {
        return;
    }

    button.disabled = true;

    try {

        // Send message to Python Flask
        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }

        // Create conversation
        const conversation = document.createElement("div");
        conversation.className = "conversation";

        // User message
        const userMessage = document.createElement("p");
        userMessage.className = "user-message";
        userMessage.textContent = "You: " + message;

        // Assistant response
        const botMessage = document.createElement("p");
        botMessage.className = "bot-message";
        botMessage.textContent = "Assistant: " + data.reply;

        // Delete button
        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-button";
        deleteButton.textContent = "Delete";

        deleteButton.onclick = function() {
            deleteMessage(data.id);
        };

        conversation.append(
            userMessage,
            botMessage,
            deleteButton
        );

        messages.appendChild(conversation);

        // Scroll to latest message
        messages.scrollTop = messages.scrollHeight;

        // Clear input
        input.value = "";

    } catch (error) {

        alert("Error: " + error.message);

    } finally {

        button.disabled = false;
        input.focus();

    }
}


/* =========================
   2. DELETE MESSAGE
========================= */

async function deleteMessage(id) {

    if (!confirm("Delete this conversation?")) {
        return;
    }

    try {

        const response = await fetch("/delete/" + id, {
            method: "POST"
        });

        const data = await response.json();

        if (data.success) {
            location.reload();
        }

    } catch (error) {

        alert("Could not delete conversation.");

    }

}


/* =========================
   3. DARK AND LIGHT MODE
========================= */

function toggleTheme() {

    document.body.classList.toggle("dark-mode");

    const isDark =
        document.body.classList.contains("dark-mode");

    localStorage.setItem(
        "theme",
        isDark ? "dark" : "light"
    );

    updateThemeButton();

}


function updateThemeButton() {

    const button = document.getElementById("themeButton");

    const isDark =
        document.body.classList.contains("dark-mode");

    button.textContent =
        isDark ? "☀️ Light Mode" : "🌙 Dark Mode";

}


// Restore theme
if (localStorage.getItem("theme") === "dark") {

    document.body.classList.add("dark-mode");

}

updateThemeButton();


/* =========================
   4. ENTER KEY
========================= */

document.getElementById("userInput")
    .addEventListener("keydown", function(event) {

        if (event.key === "Enter") {
            sendMessage();
        }

    });
