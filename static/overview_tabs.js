// Select all tab links and modals
const tabLinks = document.querySelectorAll('.tab-link');
const modals = document.querySelectorAll('.modal');
const closeButtons = document.querySelectorAll('.close-btn');

// Function to fetch inventory data from CSV
async function fetchInventoryData() {
    const response = await fetch('D:\lookapp-project\resources\data\inventory_data.csv'); // Update with the actual CSV file path
    const data = await response.text();
    const rows = data.split('\n').slice(1); // Skip header
    const inventory = rows.map(row => {
        const columns = row.split(',');
        return {
            clientId: columns[0],
            storage: columns[1],
            sku: columns[2],
            description: columns[3],
            stockType: columns[4],
            mrpType: columns[5],
            rop: columns[6],
            roq: columns[7],
            movingCode: columns[8],
            owner: columns[9]
        };
    });
    return inventory;
}

// Function to populate modal content with inventory data
async function populateInventoryModal(modalId) {
    const inventoryData = await fetchInventoryData();
    const modal = document.getElementById(modalId);

    // Assume we match SKU for simplicity (e.g., 10271)
    const currentSKU = '10271'; // This can be dynamic based on the context
    const item = inventoryData.find(data => data.sku === currentSKU);

    if (item && modal) {
        modal.querySelector('.modal-content').innerHTML = `
            <span class="close-btn" data-modal="${modalId}">&times;</span>
            <h2>Inventory Information</h2>
            <p><strong>Client ID:</strong> ${item.clientId}</p>
            <p><strong>Storage:</strong> ${item.storage}</p>
            <p><strong>Stock Type:</strong> ${item.stockType}</p>
            <p><strong>MRP Type:</strong> ${item.mrpType}</p>
            <p><strong>ROP:</strong> ${item.rop}</p>
            <p><strong>ROQ:</strong> ${item.roq}</p>
            <p><strong>Moving Code:</strong> ${item.movingCode}</p>
            <p><strong>Owner:</strong> ${item.owner}</p>
        `;
    }
}

// Function to open the corresponding modal
tabLinks.forEach((tab) => {
    tab.addEventListener('click', async (event) => {
        const modalId = event.target.getAttribute('data-modal');
        const modal = document.getElementById(modalId);
        if (modal) {
            if (modalId === 'inventory-modal') {
                await populateInventoryModal(modalId); // Populate modal dynamically for inventory
            }
            modal.style.display = 'flex'; // Show the modal
        }
    });
});

// Function to close the modal when the close button is clicked
closeButtons.forEach((button) => {
    button.addEventListener('click', (event) => {
        const modalId = event.target.getAttribute('data-modal');
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none'; // Hide the modal
        }
    });
});

// Close modal if clicked outside modal content
window.addEventListener('click', (event) => {
    modals.forEach((modal) => {
        if (event.target === modal) {
            modal.style.display = 'none'; // Hide the modal
        }
    });
});
