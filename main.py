from flask import Flask, jsonify, render_template, request
import random

app = Flask(__name__)
count=0 
   # List of Magic 8 Ball responses as Python code
RESPONSES = [
    "if question:\n  return True  # It is certain.",
    "result = True  # It is decidedly so.",
    "assert answer == True  # Without a doubt.",
    "return True  # Yes definitely.",
    "confidence = 1.0  # You may rely on it.",
    "if analyze(question):\n  print('Yes')  # As I see it, yes.",
    "probability = random.random()\nif probability > 0.2:\n  return True  # Most likely.",
    "forecast = 'positive'  # Outlook good.",
    "answer = True  # Yes.",
    "indicators = [True, True, False, True]\nif sum(indicators) > len(indicators)/2:\n  return True  # Signs point to yes.",
    "import random\nif random.random() < 0.5:\n  return 'Try again'  # Reply hazy, try again.",
    "# Error: Insufficient data\nraise TimeoutError('Ask again later.')",
    "# TODO: Implement this feature\npass  # Better not tell you now.",
    "try:\n  predict(question)\nexcept FutureUncertainError:\n  pass  # Cannot predict now.",
    "while not clear_thinking:\n  meditate()  # Concentrate and ask again.",
    "assert answer != True  # Don't count on it.",
    "return False  # My reply is no.",
    "survey_results = {'yes': 20, 'no': 80}\n# My sources say no.",
    "forecast = 'negative'  # Outlook not so good.",
    "confidence = 0.1  # Very doubtful."
]
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



    

