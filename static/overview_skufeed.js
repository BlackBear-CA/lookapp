// Scroll function
function scrollFeeds(container, direction) {
    const scrollAmount = 50; // Adjust scrolling amount
    if (direction === 'up') {
        container.scrollTop -= scrollAmount;
    } else if (direction === 'down') {
        container.scrollTop += scrollAmount;
    }
}

// Add scroll buttons
document.addEventListener('DOMContentLoaded', () => {
    const feedContainer = document.querySelector('.sku-feed-container');
    const upButton = document.createElement('button');
    const downButton = document.createElement('button');

    upButton.textContent = 'Scroll Up';
    downButton.textContent = 'Scroll Down';

    upButton.addEventListener('click', () => scrollFeeds(feedContainer, 'up'));
    downButton.addEventListener('click', () => scrollFeeds(feedContainer, 'down'));

    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('scroll-button');
    buttonContainer.appendChild(upButton);
    buttonContainer.appendChild(downButton);

    feedContainer.parentNode.insertBefore(buttonContainer, feedContainer);
});
