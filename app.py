import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

# Configure Google Generative AI
genai.configure(api_key="AIzaSyBLu0Frwa5vKVhXl2FkFyyqvAVkwm5IKPU")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Global variables for user conversations
user_conversations = {}

ANSWERS_FILE = {
    "10th": "answers10.json",
    "12th": "answers12.json",
    "ug": "answersUG.json"}
QUESTIONS_FILE = {
    "10th": "questions.json",
    "12th": "12questions.json",
    "ug": "ugquestions.json"
}


# Load questions from an external JSON file
def load_questions(level):
    try:
        with open(QUESTIONS_FILE[level], "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Helper functions
def reset_answers(level):
    """Clears the answers12.json file by resetting its contents."""
    empty_answers = {"answers": {}}
    with open(ANSWERS_FILE[level], "w") as file:
        json.dump(empty_answers, file, indent=4)


reset_answers(level="10th")
reset_answers(level="12th")
reset_answers(level="ug")


def load_answers(level):
    """Loads saved answers from a JSON file."""
    try:
        with open(ANSWERS_FILE[level], "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        reset_answers(level)
        return {"answers": {}}


def save_answers(answers, level):
    """Saves answers to a JSON file."""
    try:
        with open(ANSWERS_FILE[level], "w") as file:
            json.dump(answers, file, indent=4)
    except Exception as e:
        print(f"Error saving answers: {e}")


def talk_to_natalie(user_input, conversation_history):
    """Generates a response from the chatbot."""
    conversation_history.append(f"User: {user_input}")
    prompt = (
        "You are a professional mental health and career guidance chatbot specializing in empathetic, clear, and actionable advice. "
        "Respond to users' emotional and career-related queries with understanding and structure."
        "\n\n### User Input:\n" + user_input +
        "\n\n### Example Responses:\n"
        "- Validate emotions and acknowledge challenges.\n"
        "- Provide suggestions tailored to user needs.\n"
        "- Encourage exploration and autonomy."
    )
    response = model.generate_content([prompt])
    if response and response.text:
        chatbot_reply = response.text.strip()
    else:
        chatbot_reply = "I’m here to help. Could you share more about what’s on your mind?"

    conversation_history.append(f"Natalie: {chatbot_reply}")
    return chatbot_reply, conversation_history


def suggest_career_from_answers(answers, level):
    """Generates career guidance based on user's answers."""
    prompts = {
        '10th': "Provide structured career advice for a 10th-grade student based on the provided information. Suggest academic streams, future job roles, and actionable advice.",
        '12th': "Analyze the student's 12th-grade profile and suggest higher education pathways, career domains, and preparation strategies.",
        'ug': "Offer career advice for an undergraduate student focusing on career paths, further education, internships, and skill development."
    }
    prompt = prompts.get(level, "") + f"\n\nStudent Information:\n{json.dumps(answers, indent=4)}"
    print(prompt)
    response = model.generate_content([prompt])
    return response.text.strip() if response and response.text else "No suggestions available at the moment."


# Routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    return render_template("chat.html")


@app.route("/get_response", methods=["POST"])
def get_response():
    user_message = request.json.get("message")
    user_id = request.json.get("user_id", "default_user")

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    conversation_history = user_conversations[user_id]
    natalie_response, updated_history = talk_to_natalie(user_message, conversation_history)
    user_conversations[user_id] = updated_history

    return jsonify({"response": natalie_response})


@app.route("/question/<string:level>", methods=["GET", "POST"])
def question(level):
    questions = load_questions(level)
    answers = load_answers(level)
    current_question_index = len(answers['answers'])

    if current_question_index < len(questions):
        if request.method == 'POST':
            user_answer = request.form.get('answer')

            if 'answers' not in answers:
                answers['answers'] = {}

            question_text = questions[current_question_index]['question']
            answers['answers'][question_text] = user_answer

            save_answers(answers, level)

            return redirect(url_for('question', level=level))

        current_question = questions[current_question_index]
        return render_template("questions.html",
                               question=current_question['question'],
                               purpose=current_question['purpose'],
                               question_index=current_question_index + 1)
    return redirect(url_for('final_page', level=level))


@app.route('/final/<string:level>', methods=["GET", "POST"])
def final_page(level):
    return render_template('final_page.html', level=level)


@app.route('/results/<string:level>', methods=['GET', 'POST'])
def results(level):
    answers = load_answers(level)
    if request.method == 'POST':
        # Send the answers to the model to get career suggestions
        career_suggestions = suggest_career_from_answers(answers['answers'], level)
        return render_template('results.html', answers=answers['answers'], career_suggestions=career_suggestions)
    return render_template('results.html', answers=answers['answers'])


# Main function
if __name__ == "__main__":
    app.run(debug=True)
