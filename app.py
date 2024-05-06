from flask import Flask, request, render_template, redirect
import os
import pandas as pd
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
import openai
from flask import Flask, render_template, request
import openai
from openai import OpenAI
import pandas as pd
import json
import os
import pandas as pd
from PyPDF2 import PdfReader
import openai
from collections import defaultdict
from io import StringIO
from pdfminer.high_level import extract_text  
import json
from openai import OpenAI
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# Create Flask app
app = Flask(__name__)

# Set the directory for storing PDFs
UPLOAD_FOLDER = 'pdf'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to extract text from specific pages
def extract_text_from_pdf(pdf_path, start_page, end_page):
    with open(pdf_path, 'rb') as file:
        text = extract_text(file, page_numbers=range(start_page, end_page + 1))
    return text



# Template for OpenAI summarization
template = """
#   Anda adalah seorang hakim agung di Mahkamah Agung di Indonesia. Dari hasil putusan dibawah ini berikan aku kesimpulannya:
{}
variabel yang harus ada adalah sebagai berikut: presiding judge, member judge, clerk, ruling, other rulings, note of ruling, date of deliberation, date read out, type of judicial institution, date of register, judicial institution, case_number, court, defendants.name, defendants.place_of_birth, defendants.date_of_birth, defendants.age, defendants.gender, defendants.nationality, defendants.religion, defendants.occupation, charges.article, charges.offense, verdict.sentence, verdict.assets_confiscated.description, verdict.assets_confiscated.weight, fine dan conclusion
# """

# Single route for displaying, uploading, and extracting text from PDFs
@app.route('/', methods=['GET', 'POST'])
def manage_pdfs():
    #initialize default variables 
    extracted_text= None
    summary_result= None
    if request.method == 'POST':
        # Handle PDF upload
        if 'file' not in request.files:
            return redirect('/')
        
        file = request.files['file']
        if file.filename == '':
            return redirect('/')
        
        if file and file.filename.lower().endswith('.pdf'):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        
        return redirect('/')

    # Retrieve PDF details for displaying
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith('.pdf')]
    pdf_list = [{"Filename": f} for f in pdf_files]
    
    # Handle PDF selection and text extraction
    search_query = request.args.get('search_query', '')
    filtered_pdfs = [pdf for pdf in pdf_files if search_query.lower() in pdf.lower()]
    extracted_text = None

    if filtered_pdfs:
        selected_pdf = request.args.get('selected_pdf', '')
        if selected_pdf in filtered_pdfs:
            pdf_path = os.path.join(UPLOAD_FOLDER, selected_pdf)
            pdf_reader = PdfReader(pdf_path)

            # Extract and display the first 3 pages
            extracted_text_first = extract_text_from_pdf(pdf_path, 0, 2)

            # Determine total number of pages
            total_pages = len(pdf_reader.pages)

            # Extract and display the last 3 pages, if possible
            if total_pages > 3:
                extracted_text_last = extract_text_from_pdf(pdf_path, total_pages - 3, total_pages - 1)
                extracted_text = extracted_text_first + "\n" + extracted_text_last
            else:
                extracted_text = extracted_text_first

# --------------OPENAI---------------
            # Summarization and NER with OpenAI
            if extracted_text:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    response_format={ "type": "json_object" },
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                        {"role": "user", "content": template.format(extracted_text)}
                    ]
                    )
                data= json.loads(response.choices[0].message.content)
                df = pd.json_normalize(data)
                df = df.T
                df.columns = ["Hasil Putusan"]
                summary_result= df.to_html(classes= "dataframe", header=True, index=True)

    pdf_df = pd.DataFrame(pdf_list)
    pdf_html_table = pdf_df.to_html(index=False)

    return render_template(
        'pdf_extract.html',
        pdf_table=pdf_html_table,
        search_query=search_query,
        extracted_text=extracted_text,
        filtered_pdfs=filtered_pdfs,
        summary_result=summary_result
    )

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
