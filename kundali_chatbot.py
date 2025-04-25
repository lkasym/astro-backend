import openai
import json

def initialize_chatbot(kundali_json, openai_api_key, model_id="ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"):
    """
    Initializes the chatbot with Kundali JSON data, including divisional charts, Mahadasha, and planetary aspects.
    """
    openai.api_key = openai_api_key  

    # Convert JSON data to a formatted string
    kundali_summary = json.dumps(kundali_json, indent=2)

    conversation_history = [
        {
            "role": "system",
            "content": (
                "You are an expert Vedic astrologer providing highly detailed Kundali-based predictions using all available planetary charts, Mahadasha, Antardasha, and planetary aspects (Drishti)."
                " Consider planetary rulers, house relationships, yogas, and doshas in your analysis."
                " Your responses should be structured in proper bullet points instead of paragraphs."
                "\n\n"
                "Important Charts to Consider:\n"
                "- D1 (Lagna Chart): Core personality, life events, overall outlook.\n"
                "- D9 (Navamsa Chart): Marriage, partnerships, destiny refinement.\n"
                "- D10 (Dasamsa Chart): Career, business success, professional standing.\n"
                "- D7 (Saptamsa Chart): Children, family relationships.\n"
                "- D6 (Shashtamsa Chart): Health, immunity, disease susceptibility.\n\n"
                "Key Analysis Factors:\n"
                "- Ruling Planets & House Relationships: Identify dominant planetary rulers and their impact.\n"
                "- Mahadasha & Antardasha: Current & upcoming planetary periods shaping life events.\n"
                "- Drishti (Planetary Aspects): How planets influence each other across different houses.\n"
                "- Yogas & Doshas: Identify beneficial and challenging planetary combinations.\n\n"
                "Here is the complete Kundali data including all relevant charts and planetary positions:\n\n"
                f"{kundali_summary}"
            ),
        }
    ]

    return conversation_history, model_id


def get_chatbot_response(conversation_history, model_id="ft:gpt-4o-2024-08-06:personal:kundali-analysis-2:ASW1lwhF"):
    """
    Sends the conversation history to OpenAI's API and returns the chatbot's response.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model_id,
            messages=conversation_history,
            temperature=0.7,
            max_tokens=4000,
            top_p=1.0,
            frequency_penalty=0.3,
            presence_penalty=0.4
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error communicating with the chatbot: {e}"


def handle_chatbot_interaction(kundali_json, user_question):
    """
    Handles the chatbot interaction using Kundali data, analyzing house rulers, Mahadasha, Antardasha, and planetary aspects.
    """
    try:
        openai_api_key = "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"
        if not openai_api_key:
            return "OpenAI API key not found in code."

        conversation_history, model_id = initialize_chatbot(kundali_json, openai_api_key)

        conversation_history.append({
            "role": "user",
            "content": (
                f"User's question: {user_question}\n\n"
                "Please provide a structured, in-depth analysis using bullet points instead of paragraphs:\n\n"
                "Personality and Life Overview:\n"
                "- Influence of planetary rulers on character and destiny.\n"
                "- Strengths and weaknesses based on planetary positions.\n\n"
                "Career and Financial Growth:\n"
                "- Ideal career paths and business success opportunities (D10 chart).\n"
                "- Financial stability and long-term wealth prospects.\n"
                "- Influence of Mahadasha and Antardasha on career growth.\n\n"
                "Love and Marriage:\n"
                "- Marriage prospects and ideal partner traits (D9 chart).\n"
                "- Relationship challenges and suggested remedies.\n\n"
                "Health and Well-being:\n"
                "- Major health risks (D1 and D6 charts).\n"
                "- Recommended lifestyle changes and preventive measures.\n\n"
                "Mahadasha and Antardasha Insights:\n"
                "- Current and upcoming planetary periods shaping life events.\n"
                "- Remedies to balance challenging planetary influences.\n\n"
                "Spiritual Growth and Remedies:\n"
                "- Key karmic lessons derived from planetary placements.\n"
                "- Mantras, pujas, fasting practices, and gemstones for planetary pacification."
            )
        })

        chatbot_response = get_chatbot_response(conversation_history, model_id)

        return chatbot_response

    except Exception as e:
        return f"Error in chatbot interaction: {e}"
