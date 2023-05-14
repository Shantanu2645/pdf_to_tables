import os
import time
import threading
from flask import Flask, render_template, request, send_file
import pandas as pd
import tabula

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'pdf_file' not in request.files:
        return render_template('index.html', error_message='No PDF file selected.')

    pdf_file = request.files['pdf_file']
    output_format = request.form['output_format']

    if pdf_file.filename == '':
        return render_template('index.html', error_message='No PDF file selected.')

    try:
        start_time = time.time()

        output_name = os.path.splitext(pdf_file.filename)[0]  # Get the uploaded file name without extension
        output_path = os.path.join(app.root_path, 'output', f"{output_name}.{output_format.lower()}")  # Construct the output file path

        file_path = os.path.join(app.root_path, 'uploads', pdf_file.filename)
        pdf_file.save(file_path)

        df = tabula.read_pdf(file_path, pages="all", multiple_tables=True, stream=True, guess=True, lattice=True)
        final_df = pd.concat(df)

        if output_format == 'Excel':
            output_path = os.path.join(app.root_path, 'output', f"{output_name}.xlsx")
            final_df.to_excel(output_path, index=False)
        elif output_format == 'CSV':
            output_path = os.path.join(app.root_path, 'output', f"{output_name}.csv")
            final_df.to_csv(output_path, index=False)
        elif output_format == 'JSON':
            output_path = os.path.join(app.root_path, 'output', f"{output_name}.json")
            final_df.to_json(output_path, orient="records")

        elapsed_time = round(time.time() - start_time, 2)

        # Delete the uploaded file
        os.remove(file_path)

        return update_template(output_path, elapsed_time)
    except Exception as e:
        return render_template('index.html', error_message=str(e))

def update_template(output_path, elapsed_time):
    with app.app_context():
        status_message = f"File exported successfully. Elapsed Time: {elapsed_time} seconds."
        return render_template('index.html', status_message=status_message, output_path=output_path)

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join(app.root_path, 'output', filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    # Create the 'uploads' and 'output' directories if they don't exist
    os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'output'), exist_ok=True)
    
    app.run(debug=True)
