from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import io
import os

app = Flask(__name__)

# Azure Blob Storage URLs and SAS tokens are fetched from environment variables
MATERIAL_DATA_URL = os.getenv("MATERIAL_DATA_URL", "https://cs210032003bbb220fc.blob.core.windows.net/datasets/material_data.csv")
MATERIAL_SAS_TOKEN = os.getenv("MATERIAL_SAS_TOKEN", "?st=2025-01-16T08%3A11%3A49Z&se=2025-02-01T00%3A11%3A49Z&sp=r&spr=https&sv=2022-11-02&sr=b&sig=fmdlHhltCU4vNmLvnzPTbC0inmHLqO03pUW0U0AQrvE%3D")
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://cs210032003bbb220fc.blob.core.windows.net/image-product")
IMAGE_SAS_TOKEN = os.getenv("IMAGE_SAS_TOKEN", "?sv=2023-08-03&se=2025-01-23T20%3A17%3A52Z&sr=c&sp=rwl&sig=f6OLpFNTdOMV5l5zRGWHSnu2phTP9odsIsPG9bDv1Gc%3D")

# Helper function to fetch material data from Azure Blob Storage
def fetch_material_data():
    try:
        response = requests.get(MATERIAL_DATA_URL + MATERIAL_SAS_TOKEN)
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
        image_url = f"{IMAGE_BASE_URL}/{sku_id}.jpg{IMAGE_SAS_TOKEN}"
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
        "image_url": f"{IMAGE_BASE_URL}/{sku_id}.jpg{IMAGE_SAS_TOKEN}"
    }

    return render_template('item_overview.html', **item_data)

if __name__ == '__main__':
    # Use the PORT environment variable assigned by Azure
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
