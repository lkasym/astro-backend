# app.py

import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

# ─────────────────────────────────────────────────────────────────────────────
# 1) Your OpenAI key (hard-coded per your request)
# ─────────────────────────────────────────────────────────────────────────────
openai.api_key = "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"

# ─────────────────────────────────────────────────────────────────────────────
# 2) Request & response schemas
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    kundali_json: dict
    user_dob: str
    user_question: str

class ChatResponse(BaseModel):
    analysis_id: str | None
    message: str

# ─────────────────────────────────────────────────────────────────────────────
# 3) Build the system prompt + history
# ─────────────────────────────────────────────────────────────────────────────
def initialize_chatbot(kundali_json: dict, user_dob: str,
                       model_id: str = "ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"):
    kundali_summary = json.dumps(kundali_json, indent=2)
    system_prompt = (
        f"You are a highly knowledgeable and precise Vedic astrologer. "
        f"Use the following Kundali data, including the user's Date of Birth (DOB): {user_dob}\n"
        "• Divisional Charts (D1, D9, D10, D7, D6, etc.)\n"
        "• Planetary Aspects (Drishti)\n"
        "• Planetary Periods (Mahadasha, Antardasha)\n"
        "• Yogas and Doshas\n"
        "• Planetary Conjunctions and House Relationships\n"
        "• Rahu/Ketu Axis and Other Relevant Factors\n\n"
        "When answering user questions, please:\n"
        "1. Take the user's DOB into account.\n"
        "2. Provide deep, personalized analysis.\n"
        "3. Explain Mahadasha/Antardasha influences.\n"
        "4. Dive into key planetary meanings.\n"
        "5. Use Vedic timing principles.\n"
        "6. Answer concisely with detailed rationale.\n\n"
        f"Here is the Kundali data:\n\n{kundali_summary}\n"
    )
    return [{"role": "system", "content": system_prompt}], model_id

# ─────────────────────────────────────────────────────────────────────────────
# 4) Call OpenAI and return both the completion ID + assistant message
# ─────────────────────────────────────────────────────────────────────────────
def chat_with_kundali(kundali_json: dict, user_dob: str, user_question: str):
    history, model_id = initialize_chatbot(kundali_json, user_dob)
    history.append({"role": "user", "content": user_question})

    try:
        resp = openai.ChatCompletion.create(
            model=model_id,
            messages=history,
            temperature=0.8,
            max_tokens=3000,
            top_p=1.0,
            frequency_penalty=0.1,
            presence_penalty=0.2,
        )
    except Exception as e:
        # signal FastAPI to return HTTP 500 with message
        return {"analysis_id": None, "message": f"OpenAI API error: {e}"}

    return {
        "analysis_id": resp.id,
        "message": resp.choices[0].message.content.strip(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# 5) FastAPI app + endpoint
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI()

@app.post("/chatbot", response_model=ChatResponse)
async def chatbot_endpoint(req: ChatRequest):
    result = chat_with_kundali(req.kundali_json, req.user_dob, req.user_question)
    if result["analysis_id"] is None:
        # will become an HTTP 500 with your error message
        raise HTTPException(status_code=500, detail=result["message"])
    return result
