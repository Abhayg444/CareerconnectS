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
from deepface import DeepFace
import cv2
from PIL import Image
import threading

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
    questions = response.text.split("\n")
    filtered_questions = []

    for i, question in enumerate(questions):
        question = question.strip()
        if question and question[0].isdigit() and not question.endswith("?"):
            question += "?"
        if question and question[0].isdigit():
            filtered_questions.append(question)
    
    return filtered_questions

def process_answer(question, answer, avg_emotion):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Evaluate the following candidate's answer to an interview question. 
    Provide a score out of 10 based on correctness, depth, and relevance, and give detailed feedback.
    
    Question: {question}
    Answer: {answer}
    Average Emotion: {avg_emotion}
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

# Track emotions in the background
emotion_list = []
emotion_lock = threading.Lock()

def track_emotions_from_webcam():
    global emotion_list
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Could not access the webcam")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to grab frame from webcam")
            break

        try:
            # Analyze emotion using DeepFace
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            dominant_emotion = result[0]['dominant_emotion']
            
            # Use a lock to safely update the shared emotion list
            with emotion_lock:
                emotion_list.append(dominant_emotion)

        except Exception as e:
            st.write("Error in emotion detection:", e)
        
        # Display webcam feed in Streamlit (just to show webcam)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        st.image(img, caption="Live Webcam Feed", use_column_width=True)

        # Stop button to end emotion tracking
        if st.button("Stop Emotion Tracking"):
            break

    cap.release()

# Get the dominant emotion from the list of detected emotions
def get_avg_emotion():
    with emotion_lock:
        if emotion_list:
            avg_emotion = max(set(emotion_list), key=emotion_list.count)  # Mode of the emotions
            return avg_emotion
        else:
            return "No emotions detected"

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
            # Start background emotion tracking
            threading.Thread(target=track_emotions_from_webcam, daemon=True).start()
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
                
                # Get the current dominant emotion (average) after the answer is submitted
                avg_emotion = get_avg_emotion()

                # Submit the answer and get feedback along with the average emotion
                feedback = process_answer(interview["questions"][index], answer, avg_emotion)
                response_data = {
                    "username": interview["username"],
                    "question": interview["questions"][index],
                    "answer": answer,
                    "feedback": feedback,
                    "emotion": avg_emotion
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
            st.write(f"**Emotion:** {response['emotion']}")

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
                st.write(f"**Emotion:** {response['emotion']}")
