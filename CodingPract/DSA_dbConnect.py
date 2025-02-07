import streamlit as st
import pandas as pd
from pymongo import MongoClient

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB URI
db = client['DSA_code_app_db']  # Database name
collection = db['submissions']  # Collection name

# Path for the CSV files where the question data is stored
QUESTIONS_FILE = "question_details.csv"

# Read question details from the CSV file
questions_df = pd.read_csv(QUESTIONS_FILE)

# Ensure the topics column is properly formatted
questions_df["topics"] = questions_df["topics"].fillna("[]")  # Handle null values
questions_df["topics"] = questions_df["topics"].apply(
    lambda x: x.strip("[]").replace("'", "").replace('"', "").split(",")
)

# Function to get QID
def get_qid(row):
    return row.QID  # Access the QID using dot notation

# Function to fetch user submission data from MongoDB
def fetch_user_submissions(username):
    submissions = collection.find({"username": username})
    submission_data = {entry["qid"]: {"status": entry["status"], "time_taken": entry["time_taken"]}
                       for entry in submissions}
    return submission_data

# Display the header
st.header("📋 Question List")

# Ask for username first
username = st.text_input("Enter your username")

st.session_state['username'] = username
st.session_state['submissions'] = fetch_user_submissions(username)

    # Add filters for difficulty and topics
difficulty_level = st.selectbox("Filter by Difficulty", options=[""] + questions_df["difficulty"].unique().tolist())
selected_topic = st.selectbox(
        "Filter by Topic",
        options=[""] + pd.Series(
            [topic.strip() for topics in questions_df["topics"] for topic in topics]
        ).unique().tolist(),
    )

    # Progressive filtering: Apply both filters
filtered_questions = questions_df.copy()

if difficulty_level:  # Filter by difficulty
        filtered_questions = filtered_questions[filtered_questions["difficulty"] == difficulty_level]

if selected_topic:  # Filter by topic
        filtered_questions = filtered_questions[filtered_questions["topics"].apply(lambda topics: selected_topic in [topic.strip() for topic in topics])]

    # Check if any rows match the filters
if filtered_questions.empty:
        st.warning("No questions match the selected criteria. Please adjust your filters.")
else:
        # Display the table headers
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 3, 1, 2, 1, 1, 1])

        with col1:
            st.markdown("<b style='color: #1f77b4;'>Index</b>", unsafe_allow_html=True)
        with col2:
            st.markdown("<b style='color: #1f77b4;'>QID</b>", unsafe_allow_html=True)
        with col3:
            st.markdown("<b style='color: #1f77b4;'>Title</b>", unsafe_allow_html=True)
        with col4:
            st.markdown("<b style='color: #1f77b4;'>Difficulty</b>", unsafe_allow_html=True)
        with col5:
            st.markdown("<b style='color: #1f77b4;'>Topics</b>", unsafe_allow_html=True)
        with col6:
            st.markdown("<b style='color: #1f77b4;'>Status</b>", unsafe_allow_html=True)
        with col7:
            st.markdown("<b style='color: #1f77b4;'>Time Taken</b>", unsafe_allow_html=True)

        # Display filtered results row by row
        for idx, row in enumerate(filtered_questions.itertuples(), 1):  # Start from index 1
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 3, 1, 2, 1, 1, 1])
            
            qid = row.QID
            submission_info = st.session_state['submissions'].get(qid, {"status": "Pending", "time_taken": "N/A"})

            with col1:
                st.write(f"**{idx}**")  # Use the continuous index
            with col2:
                st.write(f"**{qid}**")  # QID
            with col3:
                st.write(row.title)  # Title
            with col4:
                st.write(row.difficulty)  # Difficulty
            with col5:
                st.write(", ".join([topic.strip() for topic in row.topics]))  # Display topics
            with col6:
                st.write(submission_info["status"])  # Submitted or Pending
            with col7:
                st.write(submission_info["time_taken"])  # Time taken for submission
            with col8:
                # Directly display the clickable URL for the next question
                next_url = f"http://localhost:8501/?qid={qid}"
                st.markdown(f"[Next Question (QID {qid})]({next_url})")
