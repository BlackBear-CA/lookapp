document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const skuId = params.get("sku_id");

    if (!skuId) {
        alert("SKU ID is missing!");
        return;
    }

    // Utility function to dynamically update a section of the page
    function updateSection(elementId, data, template = "") {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = template ? template.replace("{{value}}", data) : data;
        }
    }

    // Centralized function to fetch data from the backend API
    function fetchData(endpoint) {
        return fetch(endpoint)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            });
    }

    // Fetch SKU details from the backend and update the front-end dynamically
    fetchData(`/get_sku_details?sku_id=${skuId}`)
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            // Update stock and purchase details dynamically
            const sections = [
                { id: "stock-on-hand", data: data.stock_on_hand.quantity, template: `Stock on Hand<br>${data.stock_on_hand.info}` },
                { id: "in-transit", data: data.in_transit.quantity, template: `In-Transit<br>Loc: ${data.in_transit.info}` },
                { id: "reserved", data: data.reserved.quantity, template: `Reserved<br>Req Date: ${data.reserved.info}` },
                { id: "on-purchase", data: data.on_purchase.quantity, template: `On-Purchase<br>Est Del: ${data.on_purchase.info}` },
            ];

            sections.forEach(section => {
                updateSection(section.id, section.data, section.template);
            });

            // Update breadcrumbs navigation dynamically
            const breadcrumbs = document.querySelector(".breadcrumbs");
            if (breadcrumbs) {
                breadcrumbs.innerHTML = `
                    <span>Item Overview</span>
                    <a href="explore.html?main_category=${encodeURIComponent(data.item_main_category || "Unknown")}">
                        ${data.item_main_category || "Unknown"}
                    </a> &gt;
                    <a href="explore.html?sub_category=${encodeURIComponent(data.item_sub_category || "Unknown")}">
                        ${data.item_sub_category || "Unknown"}
                    </a> &gt;
                `;
            }

            // Load the item image dynamically
            const imageElement = document.getElementById("item-image");
            if (imageElement) {
                imageElement.src = data.image_url;
                imageElement.onerror = () => {
                    imageElement.src = "../resources/images/placeholder.png"; // Use a placeholder if the image fails to load
                };
            }

            console.log("Successfully loaded data for SKU:", skuId);
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            alert("An error occurred while fetching SKU details. Please try again.");
        });

    // Additional logic (if needed) for front-end behavior
});
