import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify, render_template


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

def authenticate_google_sheets():
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Load credentials from the environment variable instead of a file
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise Exception("Google Sheets credentials not found in environment variables.")

    creds_dict = json.loads(creds_json)  # Convert the string back to a dictionary
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    return client

def add_band_request(band_name, user_name="Anonymous"):
    client = authenticate_google_sheets()
    sheet = client.open("Band Requests").sheet1  # Open the first sheet in the document
    sheet.append_row([band_name, user_name])
    
    return f"Added request for: {band_name}"

def get_most_requested_bands():
    client = authenticate_google_sheets()
    sheet = client.open("Band Requests").sheet1
    records = sheet.get_all_records()
    band_count = {}

    for record in records:
        band = record['Band Name']
        band_count[band] = band_count.get(band, 0) + 1

    sorted_bands = sorted(band_count.items(), key=lambda x: x[1], reverse=True)
    
    result = "Most requested bands:\n"
    for band, count in sorted_bands[:10]:  # Limit to top 10
        result += f"{band}: {count} requests\n"
    
    return result

@app.route('/add_band', methods=['POST'])
def handle_band_request():
    data = request.json
    band_name = data.get("band_name")
    user_name = data.get("user_name", "Anonymous")
    
    if not band_name:
        return jsonify({"error": "Band name is required"}), 400
    
    response = add_band_request(band_name, user_name)
    return jsonify({"message": response})

@app.route('/top_bands', methods=['GET'])
def show_top_bands():
    response = get_most_requested_bands()
    return jsonify({"top_bands": response})

if __name__ == "__main__":
    app.run(debug=True)

