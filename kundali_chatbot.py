import openai
import json

def initialize_chatbot(
    kundali_json,
    openai_api_key,
    user_dob,
    model_id="ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"
):
    """
    Initializes the chatbot with the provided Kundali data, system prompt, and user's DOB
    for thorough Vedic astrology analysis.
    """
    # Set your OpenAI API key
    openai.api_key = openai_api_key

    # Convert JSON data to a formatted string
    kundali_summary = json.dumps(kundali_json, indent=2)

    # System prompt for detailed, personalized astrology analysis
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
        "1. Take the user's Date of Birth (DOB) into account for personalized analysis.\n"
        "2. Provide a deep, personalized analysis of planetary positions and aspects.\n"
        "3. Analyze the user's Mahadasha and Antardasha, focusing on how they influence the specific question.\n"
        "4. Dive into the meanings of key planetary positions and their impact on the user's life.\n"
        "5. Use Vedic astrology principles to explain the timing of events and their potential outcomes.\n"
        "6. Answer concisely, with detailed explanations of key factors involved in the analysis.\n\n"
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
    try:
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
    except Exception as e:
        return f"Error during OpenAI API call: {str(e)}"

def handle_chatbot_interaction(kundali_json, user_question, user_dob):
    """
    Handles the conversation by initializing and updating the conversation history
    with the user's question, then fetching a response from the model.
    """
    # Set your OpenAI API key here
    openai_api_key = "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"
    
    if not openai_api_key:
        return "OpenAI API key not found."

    # Initialize chatbot with system prompt and Kundali data, including the DOB
    conversation_history, model_id = initialize_chatbot(
        kundali_json,
        openai_api_key,
        user_dob,
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
