import pandas as pd
from flask import Flask, render_template
import requests
import io
import os

app = Flask(__name__)

# Azure Blob Storage URL and SAS token for the new data source
MATERIAL_DATA_URL = os.getenv("MATERIAL_DATA_URL", "https://cs210032003bbb220fc.blob.core.windows.net/datasets/material_data.csv")
SAS_TOKEN = os.getenv("SAS_TOKEN", "?se=2025-02-28T23%3A59%3A59Z&sp=r&spr=https&sv=2022-11-02&sr=b&sig=6gHA4BclcjFikr9Na3srpUA5RCvdX%2FyNAiJcdMhdEf0%3D")

# Load material data from Azure Blob Storage
def load_material_data():
    try:
        print(f"Fetching data from: {MATERIAL_DATA_URL}")  # Debugging: Confirm URL
        response = requests.get(MATERIAL_DATA_URL + SAS_TOKEN)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = pd.read_csv(io.StringIO(response.text))
        print("File loaded successfully. Columns:", data.columns)  # Debugging: Print column names
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Azure Blob Storage: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    except Exception as e:
        print(f"An error occurred while processing the data: {e}")
        return pd.DataFrame()  # Handle other potential errors gracefully

@app.route('/item/<sku>')
def item_overview(sku):
    # Load material data
    data = load_material_data()

    # Check if the DataFrame is empty
    if data.empty:
        print("Error: Data is empty. Ensure the CSV file has data.")
        return "Error: No data available. Please check the data source.", 500

    # Debugging: Print available columns
    print("Available columns in data:", data.columns)

    # Find the row corresponding to the SKU
    try:
        item = data.loc[data['sku_id'] == int(sku)]  # Adjust 'sku_id' to match your CSV column name
    except KeyError as e:
        print(f"Error: Column not found - {e}")
        return f"Error: Column 'sku_id' not found in data. Available columns: {data.columns}", 500

    # If item is found
    if not item.empty:
        item_data = {
            'sku_id': item.iloc[0]['sku_id'],
            'item_description': item.iloc[0]['item_description'],
            'detailed_description': item.iloc[0]['detailed_description'],
            'manufacturer': item.iloc[0]['manufacturer'],
            'mfg_part_nos': item.iloc[0]['mfg_part_nos'],
            'item_main_category': item.iloc[0]['item_main_category'],
            'item_sub_category': item.iloc[0]['item_sub_category'],
            'image_file_name': "SPEMGS4-004-S.jpg"  # This should match the file name in your folder
        }
    else:
        # Handle item not found
        print(f"Item with SKU {sku} not found.")
        item_data = {
            'sku_id': sku,
            'item_description': "Item not found",
            'detailed_description': "No detailed description available",
            'manufacturer': "N/A",
            'mfg_part_nos': "N/A",
            'item_main_category': "N/A",
            'item_sub_category': "N/A",
            'image_file_name': "not_found.jpg"  # Placeholder for missing image
        }

    return render_template('item_overview.html', **item_data)

if __name__ == '__main__':
    # Use the PORT environment variable assigned by Azure
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
