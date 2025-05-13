from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
import os

app = Flask(__name__)

api_key = ("GEMINI_API_KEY")
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

def generate_summary(text):
    """Generates a summary of the given text using Gemini."""
    model = "gemini-2.0-flash"  
    prompt = f"Summarize the following text:\n\n{text}" 
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    try:
        response_stream = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=GENERATE_CONTENT_CONFIG,  
        )
        full_summary = ""
        for chunk in response_stream:
            full_summary += chunk.text
        return full_summary

    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Sorry, I couldn't summarize that text."


def generate_rephrase(text):
    """Rephrases the given text using Gemini."""
    model = "gemini-2.0-flash"
    prompt = f"Rephrase the following text:\n\n{text}" 
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    try:
        response_stream = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=GENERATE_CONTENT_CONFIG,  
        )
        full_rephrased = ""
        for chunk in response_stream:
            full_rephrased += chunk.text
        return full_rephrased

    except Exception as e:
        print(f"Error during rephrasing: {e}")
        return "Sorry, I couldn't rephrase that text."


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    user_message = data['message']
    chat_history = data.get('history', [])
    response = generate_response(user_message, chat_history)
    chat_history.append(("user", user_message))
    chat_history.append(("model", response))
    return jsonify({'response': response, 'history': chat_history})

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    text_to_summarize = data['text']
    summary = generate_summary(text_to_summarize)
    return jsonify({'summary': summary})

@app.route('/rephrase', methods=['POST'])
def rephrase():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    text_to_rephrase = data['text']
    rephrased_text = generate_rephrase(text_to_rephrase)
    return jsonify({'rephrased': rephrased_text})

if __name__ == '__main__':
    #app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    app.run(host='0.0.0.0', port=5000, debug=True)
