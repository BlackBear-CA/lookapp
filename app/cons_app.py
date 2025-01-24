from flask import Flask, request, jsonify, render_template, redirect, Response, send_file
from flask_cors import CORS
import pandas as pd
import os
import logging
import io
import requests

# Initialize Flask application
app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Azure Blob Storage URLs
MATERIAL_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/materialBasicData.csv"
WAREHOUSE_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/warehouseData.csv"
LOGISTICS_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/stockLogisticsData.csv"
REQ_INTERNAL_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/reservationData.csv"
P2P_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/purchaseRecords.csv"
BARCODES_CSV_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/barcodes.csv"
IMAGE_BASE_URL = "https://cs210032003bbb220fc.blob.core.windows.net/barcodes"
STATIC_FILE_URL = "https://cs210032003bbb220fc.blob.core.windows.net/$web"

# Cache for filtered data
filtered_df = None

# Helper function to fetch data from Azure Blob Storage
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        app.logger.error(f"Error fetching data from {url}: {e}")
        return pd.DataFrame()

# Route: Get Barcode Image
@app.route("/get_barcode_image", methods=["GET"])
def get_barcode_image():
    sku_id = request.args.get("sku_id")
    if not sku_id:
        return jsonify({"error": "SKU ID is required"}), 400

    try:
        # Fetch the barcodes.csv file
        barcodes_data = fetch_data(BARCODES_CSV_URL)
        if barcodes_data.empty:
            return jsonify({"error": "Barcodes data could not be loaded"}), 500

        # Ensure the SKU ID is numeric and present in the dataset
        try:
            sku_id = int(sku_id)
        except ValueError:
            return jsonify({"error": "Invalid SKU ID format"}), 400

        # Lookup the barcode UID using SKU ID
        barcode_uid_row = barcodes_data.loc[barcodes_data["sku_id"] == sku_id, "barcode_uid"]
        if barcode_uid_row.empty:
            return jsonify({"error": f"No barcode found for SKU {sku_id}"}), 404

        # Extract the barcode UID
        barcode_uid = barcode_uid_row.iloc[0]

        # Construct the barcode image URL
        barcode_image_url = f"{IMAGE_BASE_URL}/{barcode_uid}.png"

        return jsonify({"barcode_image_url": barcode_image_url})
    except pd.errors.EmptyDataError:
        app.logger.error("Barcodes CSV file is empty or invalid")
        return jsonify({"error": "Barcodes data is empty or invalid"}), 500
    except KeyError:
        app.logger.error("Barcode UID column or SKU ID column not found in CSV file")
        return jsonify({"error": "Required columns missing in barcodes data"}), 500
    except Exception as e:
        app.logger.error(f"Error fetching barcode image: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Route: Search Functionality
@app.route("/search", methods=["GET"])
def search_data():
    global filtered_df
    query = request.args.get("query", "").strip().lower()

    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    keywords = query.split()
    try:
        df = fetch_data(MATERIAL_DATA_URL)
        if df.empty:
            return jsonify({"error": "The dataset is empty or unavailable."}), 404

        search_columns = [
            "sku_id",
            "item_description",
            "detailed_description",
            "manufacturer",
            "mfg_part_nos",
            "item_main_category",
            "item_sub_category",
        ]

        filtered_df = df[df[search_columns].apply(
            lambda row: all(
                any(keyword in str(value).lower() for value in row if pd.notna(value))
                for keyword in keywords
            ), axis=1
        )]

        filtered_df = filtered_df.fillna("0")
        results = filtered_df.to_dict(orient="records")
        if not results:
            return jsonify({"message": f"No results found for '{query}'."}), 200

        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Unexpected error during search: {e}")
        return jsonify({"error": str(e)}), 500

# Route: Export Data
@app.route("/export", methods=["GET"])
def export_data():
    global filtered_df
    if filtered_df is None or filtered_df.empty:
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
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        app.logger.error(f"Error exporting data: {e}")
        return jsonify({"error": str(e)}), 500

# Route: Get SKU Details
@app.route("/get_sku_details", methods=["GET"])
def get_sku_details():
    sku_id = request.args.get("sku_id")
    if not sku_id:
        return jsonify({"error": "SKU ID is required"}), 400

    material_data = fetch_data(MATERIAL_DATA_URL)
    if material_data.empty:
        return jsonify({"error": "Material data could not be loaded"}), 500

    try:
        sku_data = material_data.loc[material_data['sku_id'] == int(sku_id)]
        if sku_data.empty:
            return jsonify({"error": f"SKU {sku_id} not found"}), 404

        sku_details = {
            "sku_id": sku_id,
            "item_description": sku_data.iloc[0].get("item_description", "N/A"),
            "detailed_description": sku_data.iloc[0].get("detailed_description", "N/A"),
            "manufacturer": sku_data.iloc[0].get("manufacturer", "N/A"),
            "mfg_part_nos": sku_data.iloc[0].get("mfg_part_nos", "N/A"),
            "item_main_category": sku_data.iloc[0].get("item_main_category", "N/A"),
            "item_sub_category": sku_data.iloc[0].get("item_sub_category", "N/A"),
            "image_url": f"{IMAGE_BASE_URL}/{sku_id}.jpg",
        }

        return jsonify(sku_details)
    except Exception as e:
        app.logger.error(f"Error processing SKU details: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Route: Fetch Quantity Details
@app.route("/quantity_details", methods=["GET"])
def get_quantity_details():
    sku_id = request.args.get("sku_id")
    if not sku_id:
        return jsonify({"error": "SKU ID is required"}), 400

    try:
        # Fetch data from each dataset
        warehouse_data = fetch_data(WAREHOUSE_DATA_URL)
        logistics_data = fetch_data(LOGISTICS_DATA_URL)
        req_internal_data = fetch_data(REQ_INTERNAL_DATA_URL)
        p2p_data = fetch_data(P2P_DATA_URL)

        if warehouse_data.empty or logistics_data.empty or req_internal_data.empty or p2p_data.empty:
            return jsonify({"error": "One or more datasets could not be loaded"}), 500

        sku_id = int(sku_id)

        # Sum quantities for the given SKU ID
        stock_on_hand = warehouse_data.loc[warehouse_data["sku_id"] == sku_id, "soh"].sum() or 0
        storage_bins = warehouse_data.loc[warehouse_data["sku_id"] == sku_id, "storage_bin"].tolist()

        in_transit_qty = logistics_data.loc[logistics_data["sku_id"] == sku_id, "shipped_qty"].sum() or 0
        shipment_locs = logistics_data.loc[logistics_data["sku_id"] == sku_id, "shipment_location"].tolist()

        reserved_qty = req_internal_data.loc[req_internal_data["sku_id"] == sku_id, "requirement_qty"].sum() or 0
        closest_requirement_date = (
            req_internal_data.loc[req_internal_data["sku_id"] == sku_id, "requirement_date"]
            .min()
        )

        on_purchase_qty = p2p_data.loc[p2p_data["sku_id"] == sku_id, "order_qty"].sum() or 0
        closest_delivery_date = (
            p2p_data.loc[p2p_data["sku_id"] == sku_id, "delivery_date"]
            .min()
        )

        # Prepare the response data
        quantity_details = {
            "stock_on_hand": str(stock_on_hand),
            "storage_bin": ", ".join(storage_bins) if storage_bins else "N/A",
            "in_transit": str(in_transit_qty),
            "shipment_loc": ", ".join(shipment_locs) if shipment_locs else "N/A",
            "reserved": str(reserved_qty),
            "requirement_date": closest_requirement_date if pd.notna(closest_requirement_date) else "N/A",
            "on_purchase": str(on_purchase_qty),
            "delivery_date": closest_delivery_date if pd.notna(closest_delivery_date) else "N/A",
        }

        return jsonify(quantity_details)
    except Exception as e:
        app.logger.error(f"Error processing quantity details: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Route: Static File Redirection
@app.route("/")
def serve_static_index():
    return redirect(f"{STATIC_FILE_URL}/search.html", code=302)

@app.route("/static/<path:filename>")
def fetch_static_file(filename):
    static_file_url = f"{STATIC_FILE_URL}/{filename}"
    try:
        response = requests.get(static_file_url)
        response.raise_for_status()
        return Response(response.content, status=response.status_code, content_type=response.headers["Content-Type"])
    except Exception as e:
        app.logger.error(f"Error fetching static file '{filename}': {e}")
        return jsonify({"error": f"Could not fetch the file '{filename}'."}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
