from flask import Flask, jsonify, render_template, request
import random

app = Flask(__name__)

# List of Magic 8 Ball responses
RESPONSES = [
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful."
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():
    # Get a random response
    answer = random.choice(RESPONSES)
    return jsonify({'answer': answer})

# Keep the existing routes for backwards compatibility
@app.route('/increment', methods=['POST'])
def increment():
    global count
    count += 1
    return jsonify({'count': count})

@app.route('/flip_case', methods=['POST'])
def flip_case():
    text = request.json['text']
    flipped_text = ''.join(c.lower() if c.isupper() else c.upper() for c in text)
    return jsonify({'flipped_text': flipped_text})

if __name__ == '__main__':
    app.run(debug=True)
    
