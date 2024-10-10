import os
import logging
import shutil
import re
import PyPDF2
from flask import Flask, render_template, request

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'output/'
LOG_FILE = 'file_upload.log'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)  # Set the file handler level
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add the file handler to the root logger
logging.getLogger().addHandler(file_handler)

# Create a console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set the console handler level
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add the console handler to the root logger
logging.getLogger().addHandler(console_handler)

# Create output folders for CW, SW, and Uncategorized
def create_output_folders():
    try:
        for category in ['CW', 'SW']:
            for year in ['1st', '2nd', '3rd', '4th']:
                os.makedirs(os.path.join(OUTPUT_FOLDER, category, year), exist_ok=True)
        logging.info("Output folders created successfully.")
    except Exception as e:
        logging.error(f"Error creating output folders: {e}")

# Extract the semester from the PDF file
def extract_semester(pdf_path):
    try:
        logging.debug(f"Extracting semester from: {pdf_path}")
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    logging.debug(f"Checking line: {line}")
                    if "Semester" in line:
                        # Assuming the format is like "Semester: X" or "Semester X"
                        matches = re.findall(r'Semester\s*[:\s]*([1-8])', line)
                        if matches:
                            logging.debug(f"Found semester: {matches[0]}")
                            return int(matches[0])  # Return the semester number as an integer
    except Exception as e:
        logging.error(f"Error reading PDF {pdf_path}: {e}")
    return None

# Determine the year based on the semester number
def determine_year_from_semester(semester):
    if semester in [1, 2]:
        return '1st'
    elif semester in [3, 4]:
        return '2nd'
    elif semester in [5, 6]:
        return '3rd'
    elif semester in [7, 8]:
        return '4th'
    return None

# Save files while preserving the original filename and categorizing by year based on the semester
def save_file_with_structure(file_path, category):
    try:
        original_filename = os.path.basename(file_path)
        semester = extract_semester(file_path)
        year = determine_year_from_semester(semester)

        logging.debug(f"Semester: {semester}, Year: {year}")

        if year:
            dest_dir = os.path.join(OUTPUT_FOLDER, category, year)
        else:
            dest_dir = os.path.join(OUTPUT_FOLDER, category, 'Uncategorized')

        os.makedirs(dest_dir, exist_ok=True)

        dest_file_path = os.path.join(dest_dir, original_filename)
        shutil.move(file_path, dest_file_path)

        logging.info(f"File {file_path} moved to {dest_file_path}")
        return dest_file_path

    except Exception as e:
        logging.error(f"Error saving file {file_path}: {e}")
        return None

# Determine the category (CW or SW) based on file content
def determine_category(filename):
    base_filename = os.path.basename(filename.lower())
    
    logging.debug(f"Base filename: {base_filename}")
    if 'cw' in base_filename:
        return 'CW'
    return 'SW'

# Process the uploaded folder, preserving structure and sorting files into CW and SW year-wise based on semester
def process_uploaded_folder(upload_folder_path):
    sorted_files = {'CW': {'1st': [], '2nd': [], '3rd': [], '4th': []},
                    'SW': {'1st': [], '2nd': [], '3rd': [], '4th': []}}

    for root, dirs, files in os.walk(upload_folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            filename = os.path.basename(file)

            category = determine_category(filename)
            logging.debug(f"Category determined: {category} for file: {filename}")

            dest_file_path = save_file_with_structure(file_path, category)

            if dest_file_path:
                semester = extract_semester(dest_file_path)
                year = determine_year_from_semester(semester)
                if year:
                    sorted_files[category][year].append(dest_file_path)
                else:
                    logging.error(f"Failed to determine year for file {file_path}")
            else:
                logging.error(f"Failed to process file {file_path}")

    return sorted_files

# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-folder', methods=['POST'])
def upload_folder():
    logging.debug("Received request to upload folder")
    try:
        if not request.files:
            logging.error("No files uploaded!")
            return 'No folder uploaded!'
        
        create_output_folders()

        for uploaded_file in request.files.getlist('folder'):
            filename = os.path.basename(uploaded_file.filename)
            temp_file_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(temp_file_path)
            logging.debug(f"Uploaded file saved at: {temp_file_path}")

        sorted_files = process_uploaded_folder(UPLOAD_FOLDER)

        return render_template('index.html', sorted_files=sorted_files)

    except Exception as e:
        logging.error(f"Error during folder upload: {e}")
        return 'Error occurred during folder upload.'

@app.route('/clear-folders', methods=['POST'])
def clear_folders():
    try:
        clear_upload_folder()
        clear_output_folder()
        return "Folders cleared successfully!"
    except Exception as e:
        logging.error(f"Error clearing folders: {e}")
        return "Error clearing folders."

# Utility functions to clear directories
def clear_upload_folder():
    try:
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER)
        logging.info("Upload folder cleared.")
    except Exception as e:
        logging.error(f"Error clearing upload folder: {e}")

def clear_output_folder():
    try:
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)
        os.makedirs(OUTPUT_FOLDER)
        logging.info("Output folder cleared.")
    except Exception as e:
        logging.error(f"Error clearing output folder: {e}")

if __name__ == '__main__':
    clear_upload_folder()
    clear_output_folder()
    app.run(debug=True)
