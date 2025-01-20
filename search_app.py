from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import logging
import io
import requests

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for all routes (adjust origins for production)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Azure Blob Storage URL and SAS token for the new data source
MATERIAL_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/material_data.csv"
SAS_TOKEN = "?se=2025-02-28T23%3A59%3A59Z&sp=r&spr=https&sv=2022-11-02&sr=b&sig=6gHA4BclcjFikr9Na3srpUA5RCvdX%2FyNAiJcdMhdEf0%3D"

# Cache for filtered data
filtered_df = None


def fetch_material_data():
    """
    Fetches the material data from Azure Blob Storage.

    Returns:
        pandas.DataFrame: Data loaded from the CSV file or an empty DataFrame if an error occurs.
    """
    try:
        # Fetch data from the blob storage
        response = requests.get(MATERIAL_DATA_URL + SAS_TOKEN)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Convert CSV content to a pandas DataFrame
        data = pd.read_csv(io.StringIO(response.text))
        return data
    except Exception as e:
        app.logger.error(f"Error fetching material data: {e}")
        return pd.DataFrame()


@app.route("/search", methods=["GET"])
def search_data():
    """
    Searches the material data for matching rows based on a query.
    
    Returns:
        JSON response with matching rows or an error message.
    """
    global filtered_df
    query = request.args.get("query", "").strip().lower()
    app.logger.debug(f"Received query: {query}")

    if not query:
        app.logger.error("Search query is empty.")
        return jsonify({"error": "Query parameter is required"}), 400

    # Split the query into keywords
    keywords = query.split()
    app.logger.debug(f"Search keywords: {keywords}")

    try:
        app.logger.debug("Fetching material data from Azure Blob Storage.")

        # Load material data from Azure Blob Storage
        df = fetch_material_data()

        if df.empty:
            app.logger.error("The fetched CSV file is empty or unavailable.")
            return jsonify({"error": "The dataset is empty or unavailable."}), 404

        app.logger.debug(f"DataFrame loaded with {len(df)} rows and {len(df.columns)} columns.")

        # Restrict search to specific columns
        search_columns = [
            "sku_id",
            "item_description",
            "detailed_description",
            "manufacturer",
            "mfg_part_nos",
            "item_main_category",
            "item_sub_category"
        ]

        # Verify required columns exist
        missing_columns = [col for col in search_columns if col not in df.columns]
        if missing_columns:
            app.logger.error(f"Missing required columns: {missing_columns}")
            return jsonify({"error": f"Dataset is missing required columns: {', '.join(missing_columns)}"}), 500

        # Apply search filter for multiple keywords
        filtered_df = df[df[search_columns].apply(
            lambda row: all(
                any(keyword in str(value).lower() for value in row if pd.notna(value))
                for keyword in keywords
            ), axis=1
        )]

        filtered_df = filtered_df.fillna("0")  # Replace NaN with "0"
        app.logger.debug(f"Filtered DataFrame has {len(filtered_df)} rows.")

        results = filtered_df.to_dict(orient="records")
        if not results:
            app.logger.info(f"No results found for query: {query}")
            return jsonify({"message": f"No results found for '{query}'."}), 200

        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Unexpected error during search: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/export", methods=["GET"])
def export_data():
    """
    Exports the filtered data to an Excel file.
    
    Returns:
        An Excel file or an error message.
    """
    global filtered_df
    if filtered_df is None or filtered_df.empty:
        app.logger.error("No data available to export.")
        return jsonify({"error": "No data available to export."}), 400

    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Search Results")
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="search_results.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        app.logger.error(f"Error exporting data: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Allow the app to run externally on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
