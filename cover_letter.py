import streamlit as st 
import PyPDF2
from docx import Document

# Function to Extract Text from PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    reader = PyPDF2.PdfReader(uploaded_file)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to Extract Text from DOCX
def extract_text_from_docx(uploaded_file):
    text = ""
    doc = Document(uploaded_file)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Streamlit UI
st.title("Cover Letter Generator")

# Allow multiple document types for resume upload
uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "doc"])
job_desc = st.text_area("Enter Job Description", height=250)

download_format = st.selectbox("Choose download format for cover letter", ["TXT"])

if uploaded_file and job_desc:
    file_type = uploaded_file.name.split('.')[-1].lower()
    resume_text = ""

    if file_type == "pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_type in ["docx", "doc"]:
        resume_text = extract_text_from_docx(uploaded_file)

    # Display extracted resume content (optional)
    # st.subheader("Extracted Resume Content:")
    # st.markdown(f'<p style="color:white;">{resume_text}</p>', unsafe_allow_html=True)

    puter_js_code = f"""
    <script src="https://js.puter.com/v2/"></script>
    <script>
        let generatedText = ""; // Declare generatedText in global scope

        function generateCoverLetter() {{
            let resumeText = `{resume_text}`;
            let jobDescription = `{job_desc}`;
            let prompt = `Generate a professional cover letter based on the following resume details: {resume_text}. The job description is: {job_desc}.`;

            puter.ai.chat(prompt)
                .then(response => {{
                    generatedText = response;  // Store generated text in global variable
                    document.getElementById("coverLetter").innerText = generatedText;
                    // Show the download button after cover letter is generated
                    document.getElementById("downloadButton").style.display = "block";
                    document.getElementById("coverLetter").style.display = "block";
                }});
        }}
    </script>
    <button onclick="generateCoverLetter()">Generate Cover Letter</button>
    <p id="coverLetter" style="color:white; display:none;"></p>
    <div id="downloadButton" style="display:none;">
        <button onclick="downloadCoverLetter()">Download Cover Letter</button>
    </div>
    
    <script>
        function downloadCoverLetter() {{
            if (generatedText === "") {{
                alert("No cover letter generated yet!");
                return;
            }}
            // Create a Blob for the TXT file
            let blob = new Blob([generatedText], {{ type: 'text/plain' }});
            let link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'cover_letter.txt';  // Name the file .txt
            link.click();
        }}
    </script>
    """

    # Render JavaScript inside Streamlit
    st.components.v1.html(puter_js_code, height=1000)
