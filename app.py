import json
import time
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Configure Google Generative AI
genai.configure(api_key="AIzaSyC6lwqVLbRfiKAcI-vhTKvt7X0femJbW6c")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Path to JSON files
ANSWERS_FILE = "answers.json"
QUESTIONS_FILE = "questions.json"

# Store answers in a JSON file
def save_answers(answers):
    try:
        with open(ANSWERS_FILE, "w") as file:
            json.dump(answers, file, indent=4)
    except Exception as e:
        print(f"Error saving answers: {e}")

# Load answers from the JSON file
def load_answers():
    try:
        with open(ANSWERS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"answers": {}}

# Load questions from an external JSON file
def load_questions():
    try:
        with open(QUESTIONS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Suggest career based on the user's data
def suggest_career_from_answers(answers, model, max_attempts=3, sleep_time=2):
    prompt = f"""
You are a career counselor guiding a 10th-grade student. Based on the following information provided by the student, suggest potential career paths, academic streams, and job roles that could be suitable for them after completing their 10th grade. Consider their academic progress, interests, and any other relevant details shared.

Student Information:
{json.dumps(answers, indent=4)}

Provide suggestions for the following:
1. Academic Stream Suggestions: Suggest whether the student should pursue Science, Commerce, or Arts after 10th grade based on their interests and aptitude.
2. Potential Career Paths: Recommend a few career options that might suit the student's interests and abilities. These could include roles in technology, medicine, business, arts, or other fields.
3. Actionable Advice: Offer guidance on what subjects or skills the student should focus on for their chosen career path.
4. Motivation: Provide encouragement and advice to help the student stay focused on their studies and career aspirations.

Make sure the suggestions are realistic, clear, and age-appropriate, considering that the student is currently in the 10th standard.
"""

    attempt = 0
    last_output = None

    while attempt < max_attempts:
        response = model.generate_content([prompt])

        if response and response.text:
            current_output = response.text.strip()

            # Stop if the output hasn't changed
            if current_output == last_output:
                break

            last_output = current_output

        time.sleep(sleep_time)
        attempt += 1

    return last_output

# Routes for each stage
@app.route('/12th', methods=['GET', 'POST'])
def twelfth():
    questions = load_questions()
    answers = load_answers()
    current_question_index = len(answers['answers'])

    if current_question_index < len(questions):
        if request.method == 'POST':
            user_answer = request.form.get('answer')

            if 'answers' not in answers:
                answers['answers'] = {}

            question_text = questions[current_question_index]['question']
            answers['answers'][question_text] = user_answer

            save_answers(answers)

            return redirect(url_for('twelfth'))

        current_question = questions[current_question_index]
        return render_template('questions.html',
                               question=current_question['question'],
                               purpose=current_question['purpose'],
                               question_index=current_question_index + 1)

    return redirect(url_for('final_page'))

@app.route('/10th', methods=['GET', 'POST'])
def tenth():
    questions = load_questions()
    answers = load_answers()
    current_question_index = len(answers.get('answers', {}))

    print(f"Loaded questions: {questions}")
    print(f"Loaded answers: {answers}")
    print(f"Current question index: {current_question_index}")

    if current_question_index < len(questions):
        if request.method == 'POST':
            user_answer = request.form.get('answer')

            if 'answers' not in answers:
                answers['answers'] = {}

            question_text = questions[current_question_index]['question']
            answers['answers'][question_text] = user_answer

            save_answers(answers)

            print(f"Saved answer for question: {question_text}")

            return redirect(url_for('tenth'))

        current_question = questions[current_question_index]
        return render_template('questions.html',
                               question=current_question['question'],
                               purpose=current_question.get('purpose', ''),
                               question_index=current_question_index + 1)

    print("Redirecting to final page")
    return redirect(url_for('final_page'))

@app.route('/final')
def final_page():
    return render_template('final_page.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    answers = load_answers()

    if request.method == 'POST':
        # Send the answers to the model to get career suggestions
        career_suggestions = suggest_career_from_answers(answers['answers'], model)
        return render_template('results.html', answers=answers['answers'], career_suggestions=career_suggestions)

    return render_template('results.html', answers=answers['answers'])

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
