import openai
import json

def initialize_chatbot(
    kundali_json,
    openai_api_key,
    model_id="ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"
):
    """
    Initializes the chatbot with the provided Kundali data and system prompt
    for thorough Vedic astrology analysis.
    """
    # Set your OpenAI API key
    openai.api_key = openai_api_key
    
    # Convert JSON data to a formatted string
    kundali_summary = json.dumps(kundali_json, indent=2)

    # System prompt ensuring analysis of all relevant charts, aspects, dashas, etc.
    system_prompt = (
        "You are a highly knowledgeable and precise Vedic astrologer. "
        "Use the following Kundali data, including:\n"
        "• Divisional Charts (D1, D9, D10, D7, D6, etc.)\n"
        "• Planetary Aspects (Drishti)\n"
        "• Planetary Periods (Mahadasha, Antardasha)\n"
        "• Yogas and Doshas\n"
        "• Planetary Conjunctions and House Relationships\n"
        "• Rahu/Ketu Axis and Other Relevant Factors\n\n"
        "When answering user questions:\n"
        "1. Analyze each relevant chart and factor in detail.\n"
        "2. Explain which planetary aspects and dasha periods are most relevant.\n"
        "3. Identify any Yogas, Doshas, strengths, or weaknesses in planetary positions.\n"
        "4. Focus on the user’s key concerns—do not provide unnecessary information.\n"
        "5. Structure your responses in clear bullet points.\n\n"
        "Here is the Kundali data:\n\n"
        f"{kundali_summary}\n"
    )

    conversation_history = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    return conversation_history, model_id

def get_chatbot_response(
    conversation_history,
    model_id="ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"
):
    """
    Sends the conversation history to the specified OpenAI model and returns the response.
    """
    response = openai.ChatCompletion.create(
        model=model_id,
        messages=conversation_history,
        temperature=0.8,
        max_tokens=3000,
        top_p=1.0,
        frequency_penalty=0.1,
        presence_penalty=0.2
    )
    return response["choices"][0]["message"]["content"].strip()

def handle_chatbot_interaction(kundali_json, user_question):
    """
    Handles the conversation by initializing and updating the conversation history
    with the user's question, then fetching a response from the model.
    """
    # Use your provided OpenAI API key (replace with your own if different)
    openai_api_key = "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"
    if not openai_api_key:
        return "OpenAI API key not found in code."

    # Initialize chatbot with system prompt and Kundali data
    conversation_history, model_id = initialize_chatbot(
        kundali_json,
        openai_api_key,
        model_id="ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"
    )
    
    # Append user's question to conversation history
    conversation_history.append({
        "role": "user",
        "content": user_question
    })

    # Get model response
    chatbot_response = get_chatbot_response(conversation_history, model_id)
    return chatbot_response
