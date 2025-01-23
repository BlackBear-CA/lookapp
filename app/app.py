from flask import Flask, request, jsonify, send_file, redirect, Response
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

# Azure Blob Storage URLs
MATERIAL_DATA_URL = os.getenv("MATERIAL_DATA_URL", "https://cs210032003bbb220fc.blob.core.windows.net/datasets/material_data.csv")
STATIC_FILE_URL = os.getenv("STATIC_FILE_URL", "https://cs210032003bbb220fc.blob.core.windows.net/$web")

# Cache for filtered data
filtered_df = None

def fetch_material_data():
    """
    Fetches the material data from Azure Blob Storage.

    Returns:
        pandas.DataFrame: Data loaded from the CSV file or an empty DataFrame if an error occurs.
    """
    try:
        response = requests.get(MATERIAL_DATA_URL)
        response.raise_for_status()
        data = pd.read_csv(io.StringIO(response.text))
        return data
    except Exception as e:
        app.logger.error(f"Error fetching material data: {e}")
        return pd.DataFrame()

@app.route("/search", methods=["GET"])
def search_data():
    global filtered_df
    query = request.args.get("query", "").strip().lower()
    app.logger.debug(f"Received query: {query}")

    if not query:
        app.logger.error("Search query is empty.")
        return jsonify({"error": "Query parameter is required"}), 400

    keywords = query.split()
    app.logger.debug(f"Search keywords: {keywords}")

    try:
        app.logger.debug("Fetching material data from Azure Blob Storage.")
        df = fetch_material_data()

        if df.empty:
            app.logger.error("The fetched CSV file is empty or unavailable.")
            return jsonify({"error": "The dataset is empty or unavailable."}), 404

        app.logger.debug(f"DataFrame loaded with {len(df)} rows and {len(df.columns)} columns.")

        search_columns = [
            "sku_id",
            "item_description",
            "detailed_description",
            "manufacturer",
            "mfg_part_nos",
            "item_main_category",
            "item_sub_category"
        ]

        missing_columns = [col for col in search_columns if col not in df.columns]
        if missing_columns:
            app.logger.error(f"Missing required columns: {missing_columns}")
            return jsonify({"error": f"Dataset is missing required columns: {', '.join(missing_columns)}"}), 500

        filtered_df = df[df[search_columns].apply(
            lambda row: all(
                any(keyword in str(value).lower() for value in row if pd.notna(value))
                for keyword in keywords
            ), axis=1
        )]

        filtered_df = filtered_df.fillna("0")
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

@app.route("/", methods=["GET"])
def serve_static_index():
    return redirect(f"{STATIC_FILE_URL}/search.html", code=302)

@app.route("/static/<path:filename>", methods=["GET"])
def fetch_static_file(filename):
    static_file_url = f"{STATIC_FILE_URL}/{filename}"
    try:
        response = requests.get(static_file_url)
        response.raise_for_status()
        return Response(response.content, status=response.status_code, content_type=response.headers['Content-Type'])
    except Exception as e:
        app.logger.error(f"Error fetching static file '{filename}': {e}")
        return jsonify({"error": f"Could not fetch the file '{filename}'."}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
