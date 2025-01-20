from flask import Flask, request, jsonify, render_template, redirect, Response
import pandas as pd
import requests
import io
import os

app = Flask(__name__)

# Azure Blob Storage URLs
MATERIAL_DATA_URL = "https://cs210032003bbb220fc.blob.core.windows.net/datasets/material_data.csv"
IMAGE_BASE_URL = "https://cs210032003bbb220fc.blob.core.windows.net/image-product"
STATIC_FILE_URL = "https://cs210032003bbb220fc.blob.core.windows.net/$web/item overview.html"

# Helper function to fetch material data from Azure Blob Storage
def fetch_material_data():
    try:
        response = requests.get(MATERIAL_DATA_URL)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        print(f"Error fetching material data: {e}")
        return pd.DataFrame()

@app.route('/get_sku_details', methods=['GET'])
def get_sku_details():
    sku_id = request.args.get('sku_id')
    if not sku_id:
        return jsonify({"error": "SKU ID is required"}), 400

    # Fetch material data
    material_data = fetch_material_data()
    if material_data.empty:
        return jsonify({"error": "Material data could not be loaded"}), 500

    # Find SKU row
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
        }

        # Construct image URL
        image_url = f"{IMAGE_BASE_URL}/{sku_id}.jpg"
        sku_details["image_url"] = image_url

        return jsonify(sku_details)
    except Exception as e:
        print(f"Error processing SKU details: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/item_overview', methods=['GET'])
def item_overview():
    sku_id = request.args.get('sku_id')
    if not sku_id:
        return "Error: SKU ID is required", 400

    # Fetch material data
    material_data = fetch_material_data()
    if material_data.empty:
        return "Error: Material data could not be loaded", 500

    # Find SKU details
    sku_data = material_data.loc[material_data['sku_id'] == int(sku_id)]
    if sku_data.empty:
        return f"Error: SKU {sku_id} not found", 404

    # Prepare data for rendering
    item_data = {
        "sku_id": sku_id,
        "item_description": sku_data.iloc[0].get("item_description", "N/A"),
        "detailed_description": sku_data.iloc[0].get("detailed_description", "N/A"),
        "manufacturer": sku_data.iloc[0].get("manufacturer", "N/A"),
        "mfg_part_nos": sku_data.iloc[0].get("mfg_part_nos", "N/A"),
        "item_main_category": sku_data.iloc[0].get("item_main_category", "N/A"),
        "item_sub_category": sku_data.iloc[0].get("item_sub_category", "N/A"),
        "image_url": f"{IMAGE_BASE_URL}/{sku_id}.jpg"
    }

    return render_template('item_overview.html', **item_data)

@app.route('/static/item_overview', methods=['GET'])
def serve_static_item_overview():
    """
    Redirect to the static 'item_overview.html' hosted in Azure Blob Storage.
    """
    item_overview_url = f"{STATIC_FILE_URL}/item%20overview.html"
    return redirect(item_overview_url, code=302)

@app.route('/static/<path:filename>', methods=['GET'])
def fetch_static_file(filename):
    """
    Fetch static files from Azure Blob Storage via proxy.
    """
    static_file_url = f"{STATIC_FILE_URL}/{filename}"
    try:
        response = requests.get(static_file_url)
        response.raise_for_status()
        return Response(response.content, status=response.status_code, content_type=response.headers['Content-Type'])
    except Exception as e:
        print(f"Error fetching static file '{filename}': {e}")
        return jsonify({"error": f"Could not fetch the file '{filename}'."}), 500

if __name__ == '__main__':
    # Use the PORT environment variable assigned by Azure
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
