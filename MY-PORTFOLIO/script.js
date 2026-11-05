
// Welcome message
console.log("Welcome to my portfolio website!");

// Select all navigation links
const links = document.querySelectorAll(".nav-links a");

// Display clicked navigation section
links.forEach(link => {
    link.addEventListener("click", function() {
        console.log("Navigating to: " + this.textContent);
    });
});

// Contact Form Functionality

const contactForm = document.getElementById("contactForm");

if (contactForm) {

    contactForm.addEventListener("submit", function(event) {

        event.preventDefault();

        // Get visitor information
        const name = document.getElementById("visitorName").value.trim();

        const email = document.getElementById("visitorEmail").value.trim();

        const phone = document.getElementById("visitorPhone").value.trim();

        const location = document.getElementById("visitorLocation").value.trim();

        const message = document.getElementById("visitorMessage").value.trim();

        // Validate international phone number format
        const phonePattern = /^\+?[0-9\s()-]{7,20}$/;

        if (!phonePattern.test(phone)) {
            alert("Please enter a valid phone number with country code.");
            return;
        }

        // Your receiving email address
        const receiverEmail = "YOUR_EMAIL@gmail.com";

        // Prepare email subject and body
        const subject = "New Portfolio Message from " + name;

        const body =
            "Name: " + name + "\n" +
            "Email: " + email + "\n" +
            "Phone: " + phone + "\n" +
            "Country / City: " + location + "\n\n" +
            "Message:\n" + message;

        // Open visitor's email application
        const mailtoLink =
            "mailto:" + receiverEmail +
            "?subject=" + encodeURIComponent(subject) +
            "&body=" + encodeURIComponent(body);

        document.getElementById("formMessage").textContent =
            "Opening your email application...";

        window.location.href = mailtoLink;

    });

}
