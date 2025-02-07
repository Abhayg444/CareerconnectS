import streamlit as st
import openai
import time
import os
import json
import google.generativeai as genai
import numpy as np
import speech_recognition as sr
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

genai.configure(api_key=os.getenv('API_KEY'))

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["mock_interviews"]
feedback_collection = db["feedbacks"]

def get_gemini_questions(job_role, tech_stack, experience):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Generate five interview questions for a {job_role} role requiring experience in {tech_stack}. 
    The candidate has {experience} years of experience. Ensure the questions assess relevant skills and knowledge.
    """
    response = model.generate_content([prompt])
    # Split questions by lines, then filter out non-question lines, ensuring they start with a number and end with "?"
    questions = response.text.split("\n")
    filtered_questions = []

    for i, question in enumerate(questions):
        question = question.strip()
        # Check if the question starts with a number (like "1.", "2.") and ends with "?"
        if question and question[0].isdigit() and not question.endswith("?"):
            question += "?"
        if question and question[0].isdigit():  # Ensure it's a valid question
            filtered_questions.append(question)
    
    return filtered_questions

def process_answer(question, answer):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Evaluate the following candidate's answer to an interview question. 
    Provide a score out of 10 based on correctness, depth, and relevance, and give detailed feedback.
    
    Question: {question}
    Answer: {answer}
    """
    response = model.generate_content([prompt])
    return response.text

def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Recording... Speak now!")
        audio = recognizer.listen(source, timeout=5)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Could not request results"

if "interviews" not in st.session_state:
    st.session_state.interviews = []

st.title("AI Mock Interview")
st.subheader("Create and start your AI Mock Interview")

if st.button("+ Add New"):
    st.session_state.show_form = True

if "show_form" in st.session_state and st.session_state.show_form:
    with st.form("interview_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        job_role = st.text_input("Job Role/Job Position", placeholder="Ex. Full Stack Developer")
        tech_stack = st.text_input("Job Description/Tech Stack", placeholder="Ex. React, Angular, Node.js")
        experience = st.number_input("Years of Experience", min_value=0, step=1)
        start_btn = st.form_submit_button("Start Interview")
        cancel_btn = st.form_submit_button("Cancel")
        
        if cancel_btn:
            st.session_state.show_form = False
            st.rerun()
        
        if start_btn:
            questions = get_gemini_questions(job_role, tech_stack, experience)
            interview_data = {
                "username": username,
                "role": job_role,
                "stack": tech_stack,
                "experience": experience,
                "questions": questions,
                "responses": []
            }
            st.session_state.current_interview = interview_data
            st.session_state.interviews.append(interview_data)
            st.session_state.show_form = False
            st.session_state.question_index = 0
            st.rerun()

if "current_interview" in st.session_state:
    interview = st.session_state.current_interview
    st.subheader(f"Job Role: {interview['role']}")
    st.text(f"Tech Stack: {interview['stack']}")
    st.text(f"Years of Experience: {interview['experience']}")
    
    index = st.session_state.question_index
    if index < len(interview["questions"]):
        st.subheader(f"Question #{index + 1}")
        st.write(interview["questions"][index])

        # Show processed answer in the text area for editing
        if "answer_text" in st.session_state:
            answer = st.session_state.answer_text
        else:
            answer = ""  # Initialize answer as empty if it's not yet recorded

        answer = st.text_area("Your Answer", key=f"answer_{index}", value=answer)  # User can edit answer
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Record Answer"):
                st.session_state.answer_text = record_audio()
                st.rerun()
        
        with col2:
            if st.button("Next Question"):
                # Ensure answer is saved properly
                answer = st.session_state.answer_text if "answer_text" in st.session_state else ""
                st.session_state.answer_text = ""  # Clear the answer text after moving to next question
                
                # Submit the answer and get feedback
                feedback = process_answer(interview["questions"][index], answer)
                response_data = {
                    "username": interview["username"],
                    "question": interview["questions"][index],
                    "answer": answer,
                    "feedback": feedback
                }
                feedback_collection.insert_one(response_data)
                interview["responses"].append(response_data)
                st.session_state.question_index += 1
                st.rerun()
    else:
        st.success("Interview Completed! Generating Feedback...")
        for response in interview["responses"]:
            st.write(f"**Q:** {response['question']}")
            st.write(f"**Your Answer:** {response['answer']}")
            st.write(f"**Feedback:** {response['feedback']}")
        
        if st.button("Close Interview"):
            del st.session_state["current_interview"]
            del st.session_state["question_index"]
            st.rerun()

if st.session_state.interviews:
    st.subheader("Previous Mock Interviews")
    for i, interview in enumerate(st.session_state.interviews):
        with st.expander(f"{interview['role']} - {interview['experience']} Years (Created At: {datetime.now().strftime('%Y-%m-%d')})"):
            st.write(f"Tech Stack: {interview['stack']}")
            for response in interview["responses"]:
                st.write(f"**Q:** {response['question']}")
                st.write(f"**Your Answer:** {response['answer']}")
                st.write(f"**Feedback:** {response['feedback']}")
