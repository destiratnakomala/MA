from flask import Flask, request, render_template, redirect
import os
import pandas as pd
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import openai


# Create Flask app
app = Flask(__name__)

# Set the directory for storing PDFs
UPLOAD_FOLDER = 'pdf'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)




# Single route for displaying and uploading PDFs
@app.route('/', methods=['GET', 'POST'])
def manage_pdfs():
    if request.method == 'POST':
        # Handling PDF upload
        if 'file' not in request.files:
            return redirect('/')
        
        file = request.files['file']
        if file.filename == '':
            return redirect('/')
        
        if file and file.filename.lower().endswith('.pdf'):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        
        return redirect('/')

    # Retrieve PDF details for displaying
    pdf_list = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                with open(pdf_path, "rb") as file:
                    pdf_reader = PdfReader(file)
                    page_count = len(pdf_reader.pages)
                    pdf_list.append({"Filename": filename, "Page Count": page_count})
            except Exception as e:
                print(f"Could not read {filename}: {str(e)}")

    pdf_df = pd.DataFrame(pdf_list)
    pdf_html_table= pdf_df.to_html(index=False)
    return render_template('pdf.html', pdf_table=pdf_html_table)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
