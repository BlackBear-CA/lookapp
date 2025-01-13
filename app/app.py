from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import logging
import io

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Local CSV configuration for testing
LOCAL_CSV_PATH = r"D:\lookapp-project\resources\data\material_data.csv"  # Ensure the CSV file is in the same directory as this script

# Cache for filtered data
filtered_df = None

@app.route("/search", methods=["GET"])
def search_data():
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
        app.logger.debug(f"Loading local CSV file from {LOCAL_CSV_PATH}.")
        
        # Load CSV into a DataFrame
        try:
            df = pd.read_csv(LOCAL_CSV_PATH, dtype=str)  # Ensure all columns are treated as strings
        except FileNotFoundError:
            app.logger.error(f"Local file {LOCAL_CSV_PATH} not found.")
            return jsonify({"error": f"Local file {LOCAL_CSV_PATH} not found."}), 404
        except pd.errors.EmptyDataError:
            app.logger.error("The CSV file is empty.")
            return jsonify({"error": "The CSV file is empty."}), 400
        except pd.errors.ParserError as e:
            app.logger.error(f"Error parsing CSV file: {e}")
            return jsonify({"error": "Error parsing CSV file. Ensure the file format is correct."}), 400

        app.logger.debug(f"DataFrame loaded with {len(df)} rows and {len(df.columns)} columns.")

        # Debugging: Log the first 5 rows of the DataFrame
        app.logger.debug(f"Sample DataFrame content:\n{df.head()}")

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

        if not set(search_columns).issubset(df.columns):
            app.logger.error("One or more search columns are missing from the dataset.")
            return jsonify({"error": "Dataset is missing required search columns."}), 500

        # Apply search filter for multiple keywords
        try:
            filtered_df = df[df[search_columns].apply(
                lambda row: all(
                    any(keyword in str(value).lower() for value in row if pd.notna(value))
                    for keyword in keywords
                ), axis=1
            )]
        except Exception as e:
            app.logger.error(f"Error during search filtering: {e}")
            return jsonify({"error": "An error occurred while processing the search query."}), 500

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
    global filtered_df
    if filtered_df is None or filtered_df.empty:
        app.logger.error("No data available to export.")
        return jsonify({"error": "No data available to export."}), 400

    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Search Results")
        output.seek(0)

        return send_file(output, as_attachment=True, download_name="search_results.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        app.logger.error(f"Error exporting data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
