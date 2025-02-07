from DSA_questions import get_qid

import streamlit as st
import pandas as pd
import re
import subprocess
import os
from streamlit_ace import st_ace

# Load the questions from CSV (if necessary, otherwise this can be handled within the imported function)
questions_df = pd.read_csv('./question_details.csv')

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

# Streamlit app setup
st.set_page_config(page_title="DSA Practice", page_icon="🧩", layout="wide")  # Using wide layout

# Get the QID from the query parameters in the URL
query_params = st.query_params  # Replace experimental method
selected_qid = query_params.get("qid", None)
if isinstance(selected_qid, list):
    selected_qid = selected_qid[0]  # If it's a list, get the first element
if selected_qid is not None:
    selected_qid = int(selected_qid)  # Convert to integer if it's not None
else:
    selected_qid = None  # Handle the case where qid is missing or invalid

if selected_qid:
    # Ensure QID is an integer
    selected_qid = int(selected_qid)
        
    # Fetch the question using the imported function
    question_data = questions_df[questions_df['QID'] == selected_qid]
  
    if question_data is not None:
        description = clean_html(question_data.iloc[0]['Body'])
        test_cases = extract_test_cases(description)
        
        # Use the entire screen width by setting full width for columns
        col1, col2 = st.columns([1, 1])  # Use 50% width for both columns
        with col1:
            st.subheader("Description")
            st.write("---")
            st.write(description.split("Example")[0].strip())
            with st.expander("Test Cases"):
                for idx, test_case in enumerate(test_cases):
                    st.write("**Test Case {idx}**")
                    st.write(f"*Input:* {test_case['input']}")
                    st.write(f"*Output:* {test_case['output']}")

            st.write("---")

            # Display hints in collapsible section
            hints = question_data.iloc[0]['Hints']
            if hints != '[]':  # Only display if hints are not null or empty
                hints = hints.strip('[]').replace('"', '').replace("'", "").split(",")
                with st.expander("Hints"):
                    st.markdown("---")
                    for hint in hints:
                        st.write(f"{hint.strip()}")
            else:
                st.write("No hints available.")

        with col2:
            st.subheader("Code")

            language = st.selectbox("Select Language", ["Python", "Java", "C", "C++"])
            st.markdown(f"### Function Structure for {language}")
            function_structure = get_language_structure(language)

            # Set the correct mode for syntax highlighting based on the selected language
            if language in ["C", "C++"]:
                ace_mode = "c_cpp"
            else:
                ace_mode = language.lower()

            # Dynamic size calculation based on the content of col1
            description_height = len(description.split("\n")) * 20  # Approximate height based on the number of lines
            test_cases_height = len(test_cases) * 40  # Approximate height based on the number of test cases
            total_height = description_height + test_cases_height

            # Set dynamic height for the code editor
            editor_height = min(400, total_height)  # Set a minimum height for the editor to prevent it from being too small

            # Create the code editor with dynamic height
            code = st_ace(language=ace_mode, theme='monokai', height=editor_height, value=function_structure)
            
            # Check if the code is modified
            if st.session_state.get("previous_code", "") != code:
                st.session_state["code_modified"] = True
                st.session_state["previous_code"] = code
            else:
                st.session_state["code_modified"] = False

            # Button to apply the changes and save the code
            apply_button = st.button("Apply Changes")
            if apply_button and st.session_state["code_modified"]:
                # Save the modified code to the existing file
                temp_file = "temp_script.py" if language == "Python" else f"Solution.{language.lower()}"
                with open(temp_file, 'w') as f:
                    f.write(code)
                st.success("Changes applied successfully!")

            # Button to execute the code for each test case separately
            for idx, test_case in enumerate(test_cases):
                case_button = st.button(f"Case Test {idx + 1}")
                if case_button:
                    st.subheader(f"Executing Test Case {idx + 1}")
                    st.write(f"**Input:** {test_case['input']}")
                    # Execute the code with the current test case
                    actual_output = execute_code(language, code, test_case)
                    st.write(f"**Execution Output:** {actual_output}")

                    # Check if the output matches the expected result
                    if actual_output.strip() == test_case['output'].strip():
                        st.success(f"Test Case {idx + 1} Passed")
                    else:
                        st.error(f"Test Case {idx + 1} Failed")

