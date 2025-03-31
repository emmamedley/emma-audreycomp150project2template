from flask import Flask, jsonify, render_template, request
import random

app = Flask(__name__)

# Magic 8 Ball responses
responses = [
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

@app.route('/shake', methods=['POST'])
def shake():
    response = random.choice(responses)
    return jsonify({'answer': response})

if __name__ == '__main__':
    app.run(debug=True)
    