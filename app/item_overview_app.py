import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

# Load material data from CSV
def load_material_data():
    file_path = r'C:\Users\Francis Chong\lookapp\server\material_data_local.csv'
    try:
        print(f"Looking for file at: {file_path}")  # Debugging: Confirm path
        data = pd.read_csv(file_path)  # Use read_csv for CSV files
        print("File loaded successfully. Columns:", data.columns)  # Debugging: Print column names
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return pd.DataFrame()  # Return an empty DataFrame if the file is missing
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return pd.DataFrame()  # Handle other potential errors gracefully


@app.route('/item/<sku>')
def item_overview(sku):
    # Load material data
    data = load_material_data()

    # Check if the DataFrame is empty
    if data.empty:
        print("Error: Data is empty. Ensure the CSV file has data.")
        return "Error: No data available. Please check the CSV file.", 500

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
    app.run(debug=True)
