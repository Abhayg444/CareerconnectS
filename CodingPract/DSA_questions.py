import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="DSA Practice Questions", page_icon="🧩", layout="wide")

# Read question details from the CSV file
questions_file = "question_details.csv"
questions_df = pd.read_csv(questions_file)

# Ensure the topics column is properly formatted
questions_df["topics"] = questions_df["topics"].fillna("[]")  # Handle null values
questions_df["topics"] = questions_df["topics"].apply(
    lambda x: x.strip("[]").replace("'", "").replace('"', "").split(",")
)

# Function to get QID
def get_qid(row):
    return row.QID  # Access the QID using dot notation

# Display the header
st.header("📋 Question List")

# Display the table description
st.write("Here is the list of available questions:")

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
    filtered_questions = filtered_questions[
        filtered_questions["topics"].apply(lambda topics: selected_topic in [topic.strip() for topic in topics])
    ]

# Check if any rows match the filters
if filtered_questions.empty:
    st.warning("No questions match the selected criteria. Please adjust your filters.")
else:
    # Display the table headers
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 1, 2, 1])  # Define column layout

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

    # Display filtered results row by row
    for idx, row in enumerate(filtered_questions.itertuples(), 1):  # Start from index 1
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 1, 2, 1])
        with col1:
            st.write(f"**{idx}**")  # Use the continuous index
        with col2:
            st.write(f"**{row.QID}**")  # QID
        with col3:
            st.write(row.title)  # Title
        with col4:
            st.write(row.difficulty)  # Difficulty
        with col5:
            st.write(", ".join([topic.strip() for topic in row.topics]))  # Display topics
        with col6:
            # Directly display the clickable URL
            next_url = f"http://localhost:8501/?qid={get_qid(row)}"
            st.markdown(f"[Next Question (QID {get_qid(row)})]({next_url})")
