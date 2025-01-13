    <script>
        const params = new URLSearchParams(window.location.search);
        const sku_id = params.get("sku_id");

        if (sku_id) {
            document.getElementById("sku-id").textContent = sku_id;
            document.getElementById("item-image").src = `../images/items/${sku_id}.png`;
            document.getElementById("barcode-image").src = `../images/barcodes/${sku_id}.png`;

            // Example for dynamically populating other data
            document.getElementById("item-description").textContent = "Dynamic item description for SKU " + sku_id;
            document.getElementById("detailed-description").textContent = "Detailed information for item " + sku_id;
            document.getElementById("manufacturer").textContent = "Manufacturer Name";
            document.getElementById("mfg-part-nos").textContent = "Part Number";
            document.getElementById("manual-link").href = `/manuals/${sku_id}.pdf`;
            document.getElementById("barcode-id").textContent = "Dynamic barcode ID for " + sku_id;
        } else {
            alert("Error: SKU not provided in the query string.");
        }
    </script>
