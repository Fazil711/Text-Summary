from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
import os

app = Flask(__name__)

api_key = ("")
if not api_key:
    raise ValueError("The GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=api_key)


GENERATE_CONTENT_CONFIG = types.GenerateContentConfig(
    temperature=0.9,  
    top_p=0.95,
    top_k=40,
    max_output_tokens=2048,  
    response_mime_type="text/plain",
    safety_settings=[  
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
)



def generate_response(user_input, chat_history=None):
    """Generates a response using the Gemini model.

    Args:
        user_input: The user's text input.
        chat_history:  A list of previous interactions (optional, for context).

    Returns:
        The generated text response, or an error message.
    """

    model = "gemini-2.0-flash"  

    if chat_history is None:
        chat_history = []

    contents = []
    for role, text in chat_history:
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))

    try:
        response_stream = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=GENERATE_CONTENT_CONFIG,
        )

        full_response = ""
        for chunk in response_stream:
            full_response += chunk.text

        return full_response

    except Exception as e:
        print(f"Error during generation: {e}")  
        return "Sorry, I encountered an error. Please try again."



@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html') 

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat requests."""
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request format'}), 400

    user_message = data['message']
    chat_history = data.get('history', []) 

    response = generate_response(user_message, chat_history)

    chat_history.append(("user", user_message))
    chat_history.append(("model", response))

    return jsonify({'response': response, 'history': chat_history})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))