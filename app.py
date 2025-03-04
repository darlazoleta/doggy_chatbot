from flask import Flask, request, jsonify
from flask_cors import CORS
from cohere import Client
import threading
import time
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Cohere Client
co = Client('IMkbSoANcmONhqF7zhDhqr2LUlCdDxBnkLZbznyz')  # Replace with actual API key

# Cohere Model ID
MODEL_ID = '126d7bb8-059e-449b-a041-e8c4877fd9bd-ft'

# Store conversation context
user_context = {}

# API URL to send "hi" message to
HI_API_URL = "https://doggy-chatbot.onrender.com/chat"  # Replace with your API URL

def classify_text(question):
    try:
        response = co.classify(model=MODEL_ID, inputs=[question])
        return response.classifications[0].prediction
    except Exception as e:
        print(f"Classification Error: {e}")
        return None

def is_irrelevant(question):
    irrelevant_animals = ["cat", "rabbit", "bird", "hamster", "fish", "turtle", "parrot", "guinea pig", "ferret", "lizard", "snake", "mouse", "rat", "chinchilla", "horse", "goat", "sheep", "pig", "cow", "duck", "chicken", "frog", "gecko", "hedgehog", "alpaca"]
    return any(animal in question.lower() for animal in irrelevant_animals)

def ask_chatbot(user_id, question):
    if is_irrelevant(question):
        return "I can only assist with dog issues/concerns."
    
    category = classify_text(question)
    
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    polite_responses = ["thank you", "thanks", "alright"]
    
    if any(word in question.lower() for word in greetings):
        return "Hello! How can I assist you with your dog's concerns?"
    elif any(word in question.lower() for word in polite_responses):
        return "You're welcome! Let me know if you need any help with your dog."
    
    if category != "dog topic" and user_id not in user_context:
        return "I can only assist with dog issues/concerns."
    
    if user_id not in user_context:
        user_context[user_id] = []
    
    chat_history = user_context[user_id][-5:]
    formatted_chat_history = [{"role": "USER" if entry["role"].upper() == "USER" else "CHATBOT", "message": entry["message"]} for entry in chat_history]
    formatted_chat_history.append({"role": "USER", "message": question})
    
    try:
        response = co.chat(
            model="command",
            message=question,
            chat_history=formatted_chat_history,
            temperature=0.7
        )
        
        bot_reply = response.text.strip().replace("**", "")
        formatted_chat_history.append({"role": "CHATBOT", "message": bot_reply})
        user_context[user_id] = formatted_chat_history
        
        return bot_reply
    except Exception as e:
        print(f"Chatbot API Error: {e}")
        return "I'm sorry, but I couldn't process your request right now."

def send_hi_message():
    while True:
        try:
            response = requests.post(HI_API_URL, data={"message": "hi"})
            print(f"Sent 'hi' message to API, status: {response.status_code}")
        except Exception as e:
            print(f"Error sending 'hi' message: {e}")
        
        time.sleep(30)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    user_id = data.get("user_id", "default")
    
    if not user_message:
        return jsonify({"response": "Please enter a valid message."})
    
    chatbot_response = ask_chatbot(user_id, user_message)
    return jsonify({"response": chatbot_response})

if __name__ == "__main__":
    # Start the "hi" message thread when the app runs
    threading.Thread(target=send_hi_message, daemon=True).start()
    
    app.run(debug=True)
