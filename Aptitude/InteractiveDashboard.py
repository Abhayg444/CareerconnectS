import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import time
import numpy as np


# Connect to the MongoDB database
def db_connect():
    client = MongoClient("mongodb://localhost:27017/")
    return client['quiz_system']


# Fetch test data for a given username and category from the "apti_test" collection
def get_test_data(username, category):
    db = db_connect()
    collection = db['apti_test']
    tests_cursor = collection.find({"student_id": username, "category": category})
    tests = list(tests_cursor)
    if tests:
        df = pd.DataFrame(tests)
        # Calculate accuracy if not already present
        if 'accuracy' not in df.columns:
            df['accuracy'] = df['marks_achieved'] / df['no_of_questions'] * 100
        return df
    else:
        return pd.DataFrame()


# Categorize performance based on accuracy
def assign_performance_category(row):
    if row['accuracy'] < 50:
        return "Poor"
    elif row['accuracy'] < 70:
        return "Average"
    elif row['accuracy'] < 90:
        return "Good"
    else:
        return "Excellent"


# Provide detailed improvement tips using multiple data dimensions
def improvement_tips(df):
    if df.empty or 'accuracy' not in df.columns:
        return "Insufficient data to provide improvement tips."

    avg_accuracy = df['accuracy'].mean()
    tips = []

    # Overall performance tip based on average accuracy
    if avg_accuracy < 50:
        tips.append(
            "Your overall accuracy is below 50%. It might be a good idea to revisit fundamental concepts and work on a range of basic problems.")
    elif avg_accuracy < 70:
        tips.append(
            "Your average accuracy suggests there’s room for improvement. Focus on reviewing topics where you tend to lose marks.")
    elif avg_accuracy < 90:
        tips.append(
            "You’re doing well with an average accuracy in the 70-90% range. Identify the few questions that challenge you and target similar problems.")
    else:
        tips.append(
            "Excellent performance overall! Consider challenging yourself with more complex problems and perhaps mentor your peers.")

    # Time taken analysis if available
    if 'time_taken' in df.columns:
        avg_time = df['time_taken'].mean()
        median_time = df['time_taken'].median()
        if avg_time > median_time * 1.2:
            tips.append(
                "Your test durations vary significantly. Consider practicing with timed quizzes to improve consistency.")
        elif avg_time < median_time * 0.8:
            tips.append("While you're quick on tests, make sure that speed isn’t compromising your accuracy.")

    # Trend analysis: Compare the latest test with overall average
    if 'test_no' in df.columns and len(df) > 1:
        df_sorted = df.sort_values('test_no')
        last_accuracy = df_sorted['accuracy'].iloc[-1]
        if last_accuracy < avg_accuracy * 0.95:
            tips.append(
                "Your most recent test shows a slight dip compared to your average. It might help to review the topics covered in that test.")
        elif last_accuracy > avg_accuracy * 1.05:
            tips.append(
                "Great job on your latest test! Try to identify what contributed to this improvement and apply it consistently.")

    return " ".join(tips)


# --- Streamlit UI Setup ---
st.set_page_config(page_title="Quiz Performance Dashboard", layout="wide")
st.title("Interactive Quiz Performance Dashboard")
st.write("Visualize your quiz performance and get insights on how to improve.")

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    username = st.text_input("Enter Username:")
    category = st.radio("Select Category:", options=["General", "Technical"])
    submit_button = st.button("Submit")

# Main content area
if submit_button:
    df = get_test_data(username, category)
    if df.empty:
        st.error("No test data found for the given username and category.")
    else:
        st.subheader("Data Overview")
        st.dataframe(df)

        # Accuracy Trend: Line Chart
        st.subheader("Accuracy Trend")
        if 'test_no' in df.columns:
            fig_line = px.line(
                df,
                x='test_no',
                y='accuracy',
                markers=True,
                title='Accuracy Trend Across Tests',
                labels={'test_no': 'Test Number', 'accuracy': 'Accuracy (%)'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Test number data not available for trend analysis.")

        # Score Distribution: Histogram
        st.subheader("Score Distribution")
        if 'marks_achieved' in df.columns:
            fig_hist = px.histogram(
                df,
                x='marks_achieved',
                nbins=10,
                title='Distribution of Marks Achieved',
                labels={'marks_achieved': 'Marks Achieved'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Marks achieved data not available for distribution analysis.")

        # Time Taken Analysis
        st.subheader("Time Taken Analysis")
        if 'time_taken' in df.columns:
            fig_time = px.line(
                df,
                x='test_no',
                y='time_taken',
                markers=True,
                title='Time Taken per Test',
                labels={'test_no': 'Test Number', 'time_taken': 'Time Taken (seconds)'}
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Time taken data is not available in the dataset.")

        # Performance Breakdown: Pie Chart
        st.subheader("Performance Breakdown")
        if 'accuracy' in df.columns:
            df['performance_category'] = df.apply(assign_performance_category, axis=1)
            breakdown = df['performance_category'].value_counts().reset_index()
            breakdown.columns = ['Performance', 'Count']
            fig_pie = px.pie(
                breakdown,
                names='Performance',
                values='Count',
                title='Performance Breakdown'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Accuracy data is not available to compute performance breakdown.")

        # Improvement Tips Section
        st.subheader("Tips to Improve")
        tips = improvement_tips(df)
        avg_accuracy = df['accuracy'].mean() if 'accuracy' in df.columns else 0
        st.markdown(f"**Average Accuracy:** {avg_accuracy:.2f}%")
        st.markdown(tips)
else:
    st.info("Please use the sidebar to input a username and select a category, then click Submit.")
