import streamlit as st
import pandas as pd
import re
import subprocess
import os
from datetime import datetime
from streamlit_ace import st_ace
from pymongo import MongoClient

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB URI
db = client['DSA_code_app_db']  # Database name
collection = db['submissions']  # Collection name

# Streamlit app setup
st.set_page_config(page_title="DSA Practice", page_icon="🧩", layout="wide")  # Using wide layout

from DSA_dbConnect import *  # Importing the database connection

# Load the questions from CSV (if necessary, otherwise this can be handled within the imported function)
questions_df = pd.read_csv('./question_details.csv')

# Add a new column for 'Status' if not already present and set the initial value to 'Pending'
if 'Status' not in questions_df.columns:
    questions_df['Status'] = 'Pending'

def clean_html(raw_html):
    """Remove HTML tags and decode HTML entities."""
    html_entities = {"&nbsp;": " ", "&quot;": '"', "&gt;": ">", "&lt;": "<", "&amp;": "&"}
    for entity, replacement in html_entities.items():
        raw_html = raw_html.replace(entity, replacement)
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def extract_test_cases(description):
    """Extract input/output test cases from the question description."""
    test_cases = []
    input_pattern = re.compile(r'Input:\s*(.+?)\n', re.IGNORECASE)
    output_pattern = re.compile(r'Output:\s*(.+?)\n', re.IGNORECASE)
    inputs = input_pattern.findall(description)
    outputs = output_pattern.findall(description)
    for i in range(min(len(inputs), len(outputs))):
        test_cases.append({"input": inputs[i].strip(), "output": outputs[i].strip()})
    return test_cases


def get_language_structure(language):
    """Return function template for the chosen language."""
    if language == "Python":
        return """def function_name(param1, param2):\n    # Your code here\n    return output\n"""
    elif language == "Java":
        return """public class Solution {\n    public static <return_type> function_name(<param_types> param1, param2) {\n        // Your code here\n        return <return_value>;\n    }\n    public static void main(String[] args) {\n        // Call your function here\n    }\n}"""
    elif language == "C":
        return """#include <stdio.h>\n\nvoid function_name(<param_types> param1, param2) {\n    // Your code here\n}\n\nint main() {\n    // Call your function here\n    return 0;\n}"""
    elif language == "C++":
        return """#include <iostream>\nusing namespace std;\n\nvoid function_name(<param_types> param1, param2) {\n    // Your code here\n}\n\nint main() {\n    // Call your function here\n    return 0;\n}"""
    return ""

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def execute_code(language, code, test_case):
    """Execute code in the chosen language with given test cases."""
    input_str = test_case['input']
    output_str = test_case['output']
    temp_file = None
    executable = None
    try:
        if language == "Python":
            temp_file = "temp_script.py"
            with open(temp_file, 'w') as f:
                f.write(f"{code}\n\nresult = function_name({input_str})\nprint(result)")
            result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=10)

        elif language == "Java":
            temp_file = "Solution.java"
            with open(temp_file, 'w') as f:
                f.write(code)
            compile_result = subprocess.run(['javac', temp_file], capture_output=True, text=True, timeout=10)
            if compile_result.returncode != 0:
                return compile_result.stderr.strip()
            result = subprocess.run(['java', 'Solution'], capture_output=True, text=True, timeout=10)

        elif language == "C":
            temp_file = "temp_script.c"
            executable = "temp_script.exe"  # Updated to Windows-style
            with open(temp_file, 'w') as f:
                f.write(code)
            compile_result = subprocess.run(['gcc', temp_file, '-o', executable], capture_output=True, text=True, timeout=10)
            if compile_result.returncode != 0:
                return compile_result.stderr.strip()
            result = subprocess.run([executable], input=input_str, capture_output=True, text=True, timeout=10)

        elif language == "C++":
            temp_file = "temp_script.cpp"
            executable = "temp_script.exe"  # Updated to Windows-style
            with open(temp_file, 'w') as f:
                f.write(code)
            compile_result = subprocess.run(['g++', temp_file, '-o', executable], capture_output=True, text=True, timeout=10)
            if compile_result.returncode != 0:
                return compile_result.stderr.strip()
            result = subprocess.run([executable], input=input_str, capture_output=True, text=True, timeout=10)
        
        # Check result
        actual_output = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        return actual_output
    finally:
        # Clean up files
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        if executable and os.path.exists(executable):
            os.remove(executable)

def store_submission_data(username, qid, difficulty, cleaned_topics, code_lang, time_taken):
    """Store user submission data in MongoDB."""
    submission_data = {
        "username": username,
        "qid": qid,
        "difficulty": difficulty,
        "topics": cleaned_topics,
        "coding_lang": code_lang,
        "time_taken": time_taken,
        "status": "submitted",  # Mark as submitted
        "timestamp": datetime.now()  # Store timestamp of submission
    }
    collection.insert_one(submission_data)
    st.success("Data stored successfully!")

# Streamlit interface setup
query_params = st.query_params  # Replace experimental method
selected_qid = query_params.get("qid", None)
if isinstance(selected_qid, list):
    selected_qid = selected_qid[0]  # If it's a list, get the first element
if selected_qid is not None:
    selected_qid = int(selected_qid)  # Convert to integer if it's not None
else:
    selected_qid = None  # Handle the case where qid is missing or invalid

if selected_qid:
    selected_qid = int(selected_qid)
    # Fetch the question using the imported function
    question_data = questions_df[questions_df['QID'] == selected_qid]
  
    if question_data is not None:
        description = clean_html(question_data.iloc[0]['Body'])
        test_cases = extract_test_cases(description)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Description")
            st.write("---")
            st.write(description.split("Example")[0].strip())
            with st.expander("Test Cases"):
                for idx, test_case in enumerate(test_cases):
                    st.write(f"*Input:* {test_case['input']}")
                    st.write(f"*Output:* {test_case['output']}")

            st.write("---")

            hints = question_data.iloc[0]['Hints']
            if hints != '[]':  
                hints = hints.strip('[]').replace('"', '').replace("'", "").split(",")
                with st.expander("Hints"):
                    st.markdown("---")
                    for hint in hints:
                        st.write(f"{hint.strip()}")

        with col2:
            st.subheader("Code")

            language = st.selectbox("Select Language", ["Python", "Java", "C", "C++"])
            st.markdown(f"### Function Structure for {language}")
            function_structure = get_language_structure(language)

            if language in ["C", "C++"]:
                ace_mode = "c_cpp"
            else:
                ace_mode = language.lower()

            description_height = len(description.split("\n")) * 20
            test_cases_height = len(test_cases) * 40
            total_height = description_height + test_cases_height
            editor_height = min(400, total_height)

            code = st_ace(language=ace_mode, theme='monokai', height=editor_height, value=function_structure)

            if 'start_time' not in st.session_state:
                st.session_state['start_time'] = datetime.now()

            if 'test_case_status' not in st.session_state:
                st.session_state['test_case_status'] = {}

            for idx, test_case in enumerate(test_cases):
                if f"case_{idx}" not in st.session_state['test_case_status']:
                    st.session_state['test_case_status'][f"case_{idx}"] = None

                case_button = st.button(f"Test Case {idx + 1}", key=f"case_{idx}", disabled=st.session_state['test_case_status'][f"case_{idx}"] == "passed")
                
                if case_button:
                    st.subheader(f"Executing Test Case {idx + 1}")
                    st.write(f"**Input:** {test_case['input']}")
                    actual_output = execute_code(language, code, test_case)
                    st.write(f"**Execution Output:** {actual_output}")

                    if actual_output.strip() == test_case['output'].strip():
                        st.session_state['test_case_status'][f"case_{idx}"] = "passed"
                        st.success(f"Test Case {idx + 1} Passed", icon="✅")
                    else:
                        st.session_state['test_case_status'][f"case_{idx}"] = "failed"
                        st.error(f"Test Case {idx + 1} Failed", icon="❌")
                        st.session_state['test_case_status'][f"case_{idx}"] = None
                        break

            if all(status == "passed" for status in st.session_state['test_case_status'].values()):
                end_time = datetime.now()
                time_taken_seconds = (end_time - st.session_state['start_time']).total_seconds()
                
                formatted_time_taken = format_time(time_taken_seconds)
                st.success(f"All test cases passed in {formatted_time_taken}.")
                
                username = username
                difficulty = question_data.iloc[0]['difficulty']
                topics = question_data.iloc[0]['topics']
                cleaned_topics = topics.strip("[]").replace("'", "").split(",")  # This will result in a list of topics
                code_lang = language

                store_submission_data(username, selected_qid, difficulty, cleaned_topics, code_lang, formatted_time_taken)

            if 'start_time' in st.session_state:
                elapsed_time_seconds = (datetime.now() - st.session_state['start_time']).total_seconds()
                formatted_elapsed_time = format_time(elapsed_time_seconds)
                st.sidebar.write(f"Time Elapsed: {formatted_elapsed_time}")