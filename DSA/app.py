from flask import Flask, render_template, request, jsonify
import subprocess
import json
import re
import os

app = Flask(__name__)

# Load DSA questions from a JSON file
with open('DSA_Data.json', 'r') as f:
    questions = json.load(f)

# Route for home page (problem list)
@app.route('/')
def index():
    return render_template('index.html', questions=questions)

# Route for a specific question
@app.route('/question')
def question():
    id = request.args.get('id')  # Get the question ID from the URL parameters
    lang = request.args.get('language')  # Get the language from the URL parameters
    problem = questions.get(id)  # Retrieve the question from the questions dictionary

    if not problem:
        return "Question not found!", 404
    
    return render_template('question.html', problem=problem, language=lang)

# Route to run/compile and evaluate code
@app.route('/run', methods=['POST'])
def run_code():
    code = request.form['code']  # Function definition
    lang = request.form['language']
    input_data = request.form['input']  # Parameters and their values as input

    filename = None
    command = None

    if lang == 'python':
        filename = 'user_code.py'
        with open(filename, 'w') as f:
            f.write(code)
        command = ['python', filename]
    
    elif lang == 'java':
        # Use regex to extract the class name
        class_name_match = re.search(r'class\s+(\w+)', code)
        if class_name_match:
            class_name = class_name_match.group(1)
            filename = f'{class_name}.java'
        else:
            return jsonify({'output': 'Could not find a valid class name in Java code.'}), 400

        with open(filename, 'w') as f:
            f.write(code)

        # Compile the Java code
        compile_result = subprocess.run(['javac', filename], capture_output=True, text=True)

        if compile_result.returncode != 0:
            return jsonify({'output': compile_result.stderr}), 400

        # Run the Java program
        command = ['java', '-cp', '.', class_name]

    else:
        return jsonify({'output': 'Unsupported language!'}), 400

    # Execute the code and capture output
    try:
        # Execute the compiled code for languages that require compilation
        if lang in ['java']:
            result = subprocess.run(command, input=input_data, text=True, capture_output=True)
            output = result.stdout
            error = result.stderr
            if error:
                return jsonify({'output': error}), 400
            return jsonify({'output': output.strip()})
        
        # For Python, we can execute the code directly
        elif lang == 'python':
            exec_globals = {}
            exec(code, exec_globals)  # Execute the provided code
            
            # Assuming the function name is the first callable defined in the code
            function_name = next((name for name in exec_globals if callable(exec_globals[name])), None)
            
            if function_name:
                # Extract function parameters from input_data
                input_lines = input_data.split('\n')
                params = {line.split('=')[0].strip(): eval(line.split('=')[1].strip()) for line in input_lines if '=' in line}
                
                # Call the function with the provided parameters
                output = exec_globals[function_name](**params)
                return jsonify({'output': str(output)})  # Ensure output is a string
            else:
                return jsonify({'output': 'No callable function found in the code!'}), 400

    except Exception as e:
        return jsonify({'output': str(e)})  # Convert any exceptions to string

    finally:
        # Clean up temporary files
        if filename and os.path.exists(filename):
            os.remove(filename)
        if lang == 'java' and 'class_name' in locals():
            if os.path.exists(class_name + '.class'):
                os.remove(class_name + '.class')

if __name__ == '__main__':
    app.run(debug=True, port=5555) 
