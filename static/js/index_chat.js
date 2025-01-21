 document.addEventListener('DOMContentLoaded', () => {
            const chatButton = document.querySelector('.chat-button');
            const chatPopup = document.querySelector('.chat-popup');
            const animatedMessage = document.getElementById('animated-message');
    
            // The message to be animated
            const message = "Hi there! 👋 How can we assist you today?";
            let charIndex = 0;
    
            // Function to type the message
            function typeMessage() {
                if (charIndex < message.length) {
                    animatedMessage.textContent += message[charIndex];
                    charIndex++;
                    setTimeout(typeMessage, 50); // Adjust typing speed here
                }
            }
    
            // Show chat popup and start animation when chat button is clicked
            chatButton.addEventListener('click', () => {
                chatPopup.style.display = 'flex';
                if (charIndex === 0) { // Ensure animation runs only once
                    typeMessage();
                }
            });
    
            // Optional: Close chat popup when clicking outside
            document.addEventListener('click', (event) => {
                if (!chatPopup.contains(event.target) && !chatButton.contains(event.target)) {
                    chatPopup.style.display = 'none';
                }
            });
        });