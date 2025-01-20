document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const resultsContainer = document.getElementById("results-container");
    const queryDisplay = document.getElementById("search-query");
    const dropdown = document.createElement("ul");
    dropdown.id = "dropdown";
    dropdown.classList.add("dropdown");
    searchInput.parentNode.appendChild(dropdown);

    const exportButton = document.createElement("button");
    exportButton.textContent = "Export to Excel";
    exportButton.classList.add("export-btn");
    exportButton.style.display = "none";
    resultsContainer.parentNode.appendChild(exportButton);

    const clearHistoryButton = document.createElement("button");
    clearHistoryButton.textContent = "Clear History";
    clearHistoryButton.classList.add("clear-history-btn");
    searchInput.parentNode.appendChild(clearHistoryButton);

    const SEARCH_HISTORY_KEY = "searchHistory";

    // Load historical search queries
    function loadSearchHistory() {
        const history = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY)) || [];
        dropdown.innerHTML = history.map((item) => `<li>${item}</li>`).join("");
        dropdown.style.display = history.length ? "block" : "none";
    }

    // Save the search query to history
    function saveSearchQuery(query) {
        let history = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY)) || [];
        if (!history.includes(query)) {
            history = [query, ...history.slice(0, 9)];
            localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(history));
        }
    }

    // Clear search history
    clearHistoryButton.addEventListener("click", () => {
        localStorage.removeItem(SEARCH_HISTORY_KEY);
        loadSearchHistory();
    });

    // Handle dropdown click to autofill search input
    dropdown.addEventListener("click", (event) => {
        if (event.target.tagName === "LI") {
            searchInput.value = event.target.textContent;
            dropdown.style.display = "none";
        }
    });

    // Trigger search on button click or Enter key press
    searchInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            triggerSearch();
        }
    });

    searchButton.addEventListener("click", () => {
        triggerSearch();
    });

    function triggerSearch() {
        const query = searchInput.value.trim();
        if (query) {
            saveSearchQuery(query);
            fetchResults(query);
        } else {
            resultsContainer.innerHTML = "<p>Please enter a search query.</p>";
            exportButton.style.display = "none";
        }
    }

    async function fetchResults(query) {
        queryDisplay.textContent = query;
        resultsContainer.innerHTML = "<p>Loading...</p>";

        try {
            // Use Azure Web App endpoint
            const response = await fetch(`https://lookapp-exdnh0f7h6csajg8.canadacentral-01.azurewebsites.net/search?query=${encodeURIComponent(query)}`);

            if (!response.ok) {
                resultsContainer.innerHTML = `<p>Error fetching results. Status: ${response.status}</p>`;
                exportButton.style.display = "none";
                return;
            }

            const results = await response.json();
            displayResults(results, query);
        } catch (error) {
            resultsContainer.innerHTML = `<p>An error occurred while fetching the results. Error: ${error.message}</p>`;
            exportButton.style.display = "none";
            console.error("Fetch error:", error);
        }
    }

    function displayResults(results, query) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = `<p>No results found for '${query}'.</p>`;
            exportButton.style.display = "none";
            return;
        }

        const table = document.createElement("table");
        table.border = "1";
        table.cellSpacing = "0";
        table.cellPadding = "5";
        table.classList.add("results-table");

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        Object.keys(results[0]).forEach((key) => {
            const th = document.createElement("th");
            th.textContent = key;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        results.forEach((row) => {
            const tr = document.createElement("tr");

            Object.keys(row).forEach((key) => {
                const td = document.createElement("td");

                if (key === "sku_id") {
                    // Update to redirect with query parameter
                    td.innerHTML = `<a href="item_overview.html?sku_id=${row[key]}">${row[key]}</a>`;
                } else {
                    td.textContent = row[key] !== null && row[key] !== undefined ? row[key] : "N/A";
                }

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        resultsContainer.innerHTML = "";
        resultsContainer.appendChild(table);

        exportButton.style.display = "inline-block";
        exportButton.onclick = () => exportToExcel(results, query);
    }

    function exportToExcel(data, query) {
        const headers = Object.keys(data[0]);
        const rows = data.map((row) =>
            headers.map((header) => (row[header] !== null && row[header] !== undefined ? row[header] : ""))
        );

        const csvContent = [headers, ...rows]
            .map((row) => row.map((cell) => `"${cell}"`).join(","))
            .join("\n");

        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.setAttribute("href", url);
        link.setAttribute("download", `search_results_${query}.csv`);
        link.style.display = "none";

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    loadSearchHistory();
});
