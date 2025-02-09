import streamlit as st
from pymongo import MongoClient
import pandas as pd
import dash
from dash import dcc, html
import plotly.express as px

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['DSA_code_app_db']
collection = db['submissions']

# Function to fetch data based on username
def fetch_data(username):
    query = {"username": username}
    cursor = collection.find(query)
    data = list(cursor)
    return pd.DataFrame(data)

st.header("DSA Submission Overview")

# Streamlit input for username
username = st.text_input("Enter Username")

if username:
    # Fetch data based on the input username
    df = fetch_data(username)

    # Display the dataframe (optional for testing)
    # st.write(df)

    # Calculate submission counts
    submission_count = len(df)
    st.write(f"Total Submissions: {submission_count}")

    # Date-wise submission counts
    df['timestamp'] = pd.to_datetime(df['timestamp'])  # Convert timestamp to datetime
    df['date'] = df['timestamp'].dt.date  # Extract the date (ignoring time)

    # Count submissions per date
    date_counts = df['date'].value_counts().sort_index().reset_index()
    date_counts.columns = ['Date', 'Submission Count']

    st.write("Submissions Date-wise:")
    # Use line chart instead of bar chart for date-wise submissions
    submission_date_chart = px.line(date_counts, x="Date", y="Submission Count", 
                                    title="Submissions Date-wise", markers=True)
    submission_date_chart.update_layout(xaxis_tickangle=45)  # Horizontal x-axis labels
    st.plotly_chart(submission_date_chart)

    # Difficulty-wise submissions (pie chart)
    difficulty_counts = df['difficulty'].value_counts().reset_index()
    difficulty_counts.columns = ['Difficulty', 'Count']
    st.write("Difficulty-wise Submissions:")
    st.plotly_chart(px.pie(difficulty_counts, names='Difficulty', values='Count', title='Difficulty-wise Submissions'))

    # Topic-wise submissions (bar chart)
    topic_counts = df.explode('topics')['topics'].value_counts().reset_index()
    topic_counts.columns = ['Topic', 'Count']
    st.write("Topic-wise Submissions:")
    topic_bar_chart = px.bar(topic_counts, x="Topic", y="Count", title="Topic-wise Submissions")
    topic_bar_chart.update_layout(xaxis_tickangle=0)  # Horizontal x-axis labels
    st.plotly_chart(topic_bar_chart)

    # Coding language used (pie chart)
    coding_lang_counts = df['coding_lang'].value_counts().reset_index()
    coding_lang_counts.columns = ['Coding Language', 'Count']
    st.write("Coding Language Used:")
    st.plotly_chart(px.pie(coding_lang_counts, names='Coding Language', values='Count', title='Coding Language Used'))

    # Create a Dash app instance
    app = dash.Dash(__name__)

    # Build the layout for the Dash dashboard
    app.layout = html.Div([
        html.H1(f"Dashboard for {username}"),
        dcc.Graph(
            id="submission_date_graph",
            figure=submission_date_chart  # Include the date-wise submission graph
        ),
        dcc.Graph(
            id="difficulty_pie_chart",
            figure=px.pie(difficulty_counts, names='Difficulty', values='Count', title='Difficulty-wise Submissions')
        ),
        dcc.Graph(
            id="topic_bar_chart",
            figure=px.bar(topic_counts, x="Topic", y="Count", title="Topic-wise Submissions")
        ),
        dcc.Graph(
            id="coding_lang_pie_chart",
            figure=px.pie(coding_lang_counts, names='Coding Language', values='Count', title='Coding Language Used')
        )
    ])

    # Run the Dash app inside Streamlit
    app.run_server(debug=False, use_reloader=False, port=8051)
