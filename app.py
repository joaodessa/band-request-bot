import gspread
import os
import json
import requests  # 🔥 NEW: For Spotify API requests
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify, render_template

# ✅ Spotify API Credentials (REPLACE with your keys)
SPOTIFY_CLIENT_ID = "be64ee4853c8489fb18fc950196c58c4"
SPOTIFY_CLIENT_SECRET = "03788c1bf8134d9c81003f74a4441d5b"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
SPOTIFY_RECOMMEND_URL = "https://api.spotify.com/v1/artists/{id}/related-artists"

# ✅ Flask App Initialization
app = Flask(__name__)

# ✅ Authenticate with Spotify API
def get_spotify_token():
    response = requests.post(SPOTIFY_TOKEN_URL, {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    })
    return response.json().get("access_token")

# ✅ Fetch Similar Artists from Spotify
def get_similar_artists(band_name):
    token = get_spotify_token()
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Search for the artist
    search_params = {"q": band_name, "type": "artist", "limit": 1}
    search_response = requests.get(SPOTIFY_SEARCH_URL, headers=headers, params=search_params)
    search_data = search_response.json()

    if not search_data.get("artists") or not search_data["artists"]["items"]:
        return []

    artist_id = search_data["artists"]["items"][0]["id"]

    # Step 2: Fetch related artists
    related_response = requests.get(SPOTIFY_RECOMMEND_URL.format(id=artist_id), headers=headers)
    related_data = related_response.json()

    similar_artists = [artist["name"] for artist in related_data.get("artists", [])][:5]  # Limit to 5
    return similar_artists

# ✅ Function to Authenticate Google Sheets
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise Exception("Google Sheets credentials not found in environment variables.")

    creds_dict = json.loads(creds_json)  # Convert string to dictionary
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# ✅ Function to Add Band Request
def add_band_request(band_name, city, user_name="Anonymous"):
    client = authenticate_google_sheets()
    sheet = client.open("Band Requests").sheet1  
    sheet.append_row([band_name, city, user_name])
    return f"Added request for: {band_name} in {city}"

# ✅ Fetch Most Requested Bands
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

# ✅ Handle Band Requests (NOW WITH AI SUGGESTIONS)
@app.route('/add_band', methods=['POST'])
def handle_band_request():
    data = request.json
    band_name = data.get("band_name")
    city = data.get("city")
    user_name = data.get("user_name", "Anonymous")

    if not band_name or not city:
        return jsonify({"error": "Band name and city are required"}), 400

    # 🔥 Fetch AI-based recommendations from Spotify
    similar_artists = get_similar_artists(band_name)

    # ✅ Save the band request in Google Sheets
    response_message = add_band_request(band_name, city, user_name)

    # 🎶 Append recommendations to response
    if similar_artists:
        response_message += f" 🎧 You may also like: {', '.join(similar_artists)}"

    return jsonify({"message": response_message})

# ✅ Fetch Top Bands
@app.route('/top_bands', methods=['GET'])
def show_top_bands():
    response = get_most_requested_bands()
    return jsonify({"top_bands": response})

# ✅ Serve the Homepage
@app.route('/')
def home():
    return render_template("index.html")

# ✅ Run the Flask App
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))  
    app.run(host="0.0.0.0", port=port)
