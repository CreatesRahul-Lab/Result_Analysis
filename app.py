import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO


def extract_data_from_pdf(pdf_file):
    """
    Extracts text data from the provided PDF file.
    """
    text_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_data.append(text)
    return "\n".join(text_data)


def parse_pdf_data(text):
    """
    Parses the extracted PDF text into a structured DataFrame.
    Extracts relevant columns like S.No, Registration No, Name, and Reappear Subjects.
    """
    rows = []
    for line in text.splitlines():
        # Adjust regex pattern based on the actual structure of the result PDF
        match = re.match(
            r"(\d+)\s+(\d+)\s+([A-Za-z\s]+)\s+(\d+)\s+([A-Za-z0-9\s,()/]+)\s+(\w+)", line
        )
        if match:
            s_no, reg_no, name, _, reappear_subjects, status = match.groups()
            rows.append(
                {
                    "S.No": s_no,
                    "Registration No": reg_no,
                    "Name": name.strip(),
                    "Re-appear in Subject Codes": reappear_subjects.strip(),
                    "Status": status.strip(),
                }
            )

    if not rows:
        raise ValueError("No valid data could be parsed. Check the PDF format.")
    return pd.DataFrame(rows)


def filter_students(df, subject_code, pass_or_fail):
    """
    Filters students based on the subject code and pass/reappear criteria.
    """
    filtered_rows = []
    
    # Debugging: Print out the DataFrame and subject_code
    st.write("DataFrame for filtering:", df)
    
    for _, row in df.iterrows():
        reappear_data = row["Re-appear in Subject Codes"]
        
        # Debugging: Print out reappear_data for each student
        st.write(f"Processing student: {row['Name']}, Reappear Data: {reappear_data}")
        
        # Extract marks for the subject code in the data
        subject_marks = re.findall(rf"({subject_code})\s*\((\w+)/(\d+)\)", reappear_data)
        
        # Debugging: Print out extracted subject marks
        st.write(f"Subject Marks Found: {subject_marks}")
        
        for code, mark_type, marks in subject_marks:
            marks = int(marks)
            if subject_code == code:
                if pass_or_fail.lower() == "pass" and marks >= 30:
                    filtered_rows.append(row)
                elif pass_or_fail.lower() == "reappear" and marks < 30:
                    filtered_rows.append(row)

    if not filtered_rows:
        raise ValueError(f"No students found for subject code '{subject_code}' with the selected criteria.")
    
    return pd.DataFrame(filtered_rows)


def convert_df_to_excel(df):
    """
    Converts a DataFrame to an Excel file and returns it as a binary object.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Filtered Results")
    return output.getvalue()


# Streamlit App
st.title("Semester Result Filtering Tool")

st.sidebar.header("Upload PDF")
uploaded_pdf = st.sidebar.file_uploader("Upload the result PDF", type=["pdf"])

if uploaded_pdf:
    try:
        st.write("Extracting data from the uploaded PDF...")
        extracted_text = extract_data_from_pdf(uploaded_pdf)

        # Parse the extracted text into a DataFrame
        df = parse_pdf_data(extracted_text)

        # Inputs for filtering
        subject_code = st.text_input("Enter the subject code to filter (e.g., 0095):")
        
        # Radio buttons for Pass or Reappear selection
        pass_or_fail = st.radio("Select filter type:", ["Pass", "Reappear"])

        if subject_code and st.button("Generate Filtered Excel File"):
            try:
                # Filter the data
                filtered_df = filter_students(df, subject_code, pass_or_fail)

                # Convert the filtered DataFrame to Excel
                excel_data = convert_df_to_excel(filtered_df)

                # Provide a download button
                st.success(
                    f"Filtered {pass_or_fail} list for subject code '{subject_code}' generated successfully!"
                )
                st.download_button(
                    label="Download Filtered Excel File",
                    data=excel_data,
                    file_name=f"{subject_code}_{pass_or_fail.lower()}_list.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except ValueError as ve:
                st.error(str(ve))
            except Exception as e:
                st.error(f"An error occurred: {e}")
    except Exception as e:
        st.error(f"Error processing the uploaded PDF: {e}")
else:
    st.info("Please upload a PDF to proceed.")