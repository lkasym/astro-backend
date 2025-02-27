from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from datetime import datetime
from kundali_calculations import calculate_kundali
from kundali_chatbot import handle_chatbot_interaction

app = FastAPI()

# ✅ Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# ✅ Google Maps API Key
GOOGLE_MAPS_API_KEY = "AIzaSyD2-vOLkjencAqLJJ8fHDdVONnV12AT4EI"

# ✅ TimeZoneDB API Key
TIMEZONE_API_KEY = "41XNPVX0HOMY"

# ✅ Define request schema for Kundali Generation
class KundaliRequest(BaseModel):
    name: str
    date_of_birth: str  # Format: YYYY-MM-DD
    time_of_birth: str  # Format: HH:MM AM/PM
    place: str

# ✅ Define request schema for Chatbot
class ChatbotRequest(BaseModel):
    kundali_json: dict  # ✅ Pass the **entire Kundali JSON**
    user_question: str  # ✅ User’s query about Kundali

# ✅ Function to Convert Time Format
def convert_to_24_hour(time_str):
    try:
        return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        try:
            return datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM (24-hour) or HH:MM AM/PM")

# ✅ Root Endpoint
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI Kundali API is running!"}

# ✅ Fetch Place Suggestions
@app.get("/place-suggestions")
async def get_place_suggestions(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={query}&types=(cities)&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url, timeout=10).json()

    if "predictions" not in response or not response["predictions"]:
        raise HTTPException(status_code=404, detail="No location suggestions found.")

    return {"suggestions": [p["description"] for p in response["predictions"]]}

# ✅ Generate Kundali (No more recalculations in chatbot!)
@app.post("/generate-kundali")
async def generate_kundali(data: KundaliRequest):
    try:
        time_24_hour = convert_to_24_hour(data.time_of_birth)

        # 🔹 Get Latitude & Longitude from Google Maps API
        location_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={data.place}&key={GOOGLE_MAPS_API_KEY}"
        location_response = requests.get(location_url, timeout=10).json()

        if not location_response["results"]:
            raise HTTPException(status_code=404, detail=f"Location not found: {data.place}")

        latitude = location_response["results"][0]["geometry"]["location"]["lat"]
        longitude = location_response["results"][0]["geometry"]["location"]["lng"]

        # 🔹 Get Timezone from Coordinates
        timezone_url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONE_API_KEY}&format=json&by=position&lat={latitude}&lng={longitude}"
        timezone_response = requests.get(timezone_url, timeout=10).json()

        if "zoneName" not in timezone_response:
            raise HTTPException(status_code=500, detail="Timezone lookup failed")

        timezone = timezone_response["zoneName"]

        # 🔹 Perform Kundali Calculations
        kundali_data = calculate_kundali(
            name=data.name,
            date_of_birth=data.date_of_birth,
            time_of_birth=time_24_hour,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )

        return {"kundali": kundali_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kundali generation error: {str(e)}")

# ✅ Chatbot Endpoint (Now Passes JSON Directly!)
@app.post("/chatbot")
async def chatbot_interaction(data: ChatbotRequest):
    try:
        if not data.kundali_json or not isinstance(data.kundali_json, dict):
            raise HTTPException(status_code=400, detail="Invalid Kundali JSON provided.")

        # ✅ Pass the JSON directly to chatbot (No recalculations!)
        response = handle_chatbot_interaction(
            kundali_json=data.kundali_json,
            user_question=data.user_question
        )

        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")
