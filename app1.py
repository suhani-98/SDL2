import os
import logging
import shutil
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'output/'
LOG_FILE = 'file_upload.log'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

# Create output folders for CW, SW, and Uncategorized
def create_output_folders():
    try:
        for category in ['CW', 'SW', 'Uncategorized']:
            os.makedirs(os.path.join(OUTPUT_FOLDER, category), exist_ok=True)
        logging.info("Output folders created successfully.")
    except Exception as e:
        logging.error(f"Error creating output folders: {e}")

# Save files while preserving the original filename
def save_file_with_structure(file_path, category):
    try:
        # Get the original filename directly from the input file
        original_filename = os.path.basename(file_path)

        # Build the destination directory in the output folder based on category
        dest_dir = os.path.join(OUTPUT_FOLDER, category)

        # Create the destination directory
        os.makedirs(dest_dir, exist_ok=True)

        # Construct the full destination file path with the original filename
        dest_file_path = os.path.join(dest_dir, original_filename)

        # Move the file to the destination
        shutil.move(file_path, dest_file_path)

        logging.info(f"File {file_path} moved to {dest_file_path}")
        return dest_file_path

    except Exception as e:
        logging.error(f"Error saving file {file_path} to {dest_file_path}: {e}")
        return None

# Determine the category (CW or SW) based on file content (here, using file name as a placeholder)
def determine_category(filename):
    base_filename = os.path.basename(filename.lower())
    
    if 'cw' in base_filename:
        return 'CW'
    elif 'sw' in base_filename:
        return 'SW'
    return 'Uncategorized'

# Process the uploaded folder, preserving structure and sorting files into CW, SW, Uncategorized
def process_uploaded_folder(upload_folder_path):
    sorted_files = {'CW': [], 'SW': [], 'Uncategorized': []}

    # Walk through the uploaded folder and its subfolders
    for root, dirs, files in os.walk(upload_folder_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Determine the category of the file based on the filename
            category = determine_category(file)

            # Save the file while preserving its original name
            dest_file_path = save_file_with_structure(file_path, category)

            if dest_file_path:
                # Append the file paths to the sorted_files dictionary
                sorted_files[category].append(dest_file_path)
            else:
                logging.error(f"Failed to process file {file_path}")

    return sorted_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-folder', methods=['POST'])
def upload_folder():
    try:
        # Ensure at least one file was uploaded
        if not request.files:
            return 'No folder uploaded!'

        # Create output directories
        create_output_folders()

        # Process each uploaded file (assume folder input)
        for uploaded_file in request.files.getlist('folder'):
            filename = secure_filename(uploaded_file.filename)
            temp_file_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(temp_file_path)

        # Process the uploaded folder recursively, preserving structure
        sorted_files = process_uploaded_folder(UPLOAD_FOLDER)

        # Render the sorted files on the page
        return render_template('index.html', sorted_files=sorted_files)

    except Exception as e:
        logging.error(f"Error during folder upload: {e}")
        return 'Error occurred during folder upload.'

# Utility function to clear the uploads directory
def clear_upload_folder():
    try:
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER)
        logging.info("Upload folder cleared.")
    except Exception as e:
        logging.error(f"Error clearing upload folder: {e}")

# Utility function to clear the output directory
def clear_output_folder():
    try:
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)
        os.makedirs(OUTPUT_FOLDER)
        logging.info("Output folder cleared.")
    except Exception as e:
        logging.error(f"Error clearing output folder: {e}")

# Route to clear the directories
@app.route('/clear-folders', methods=['POST'])
def clear_folders():
    try:
        clear_upload_folder()
        clear_output_folder()
        return "Folders cleared successfully!"
    except Exception as e:
        logging.error(f"Error clearing folders: {e}")
        return "Error clearing folders."

if __name__ == '__main__':
    # Clear folders on startup to ensure no leftover files
    clear_upload_folder()
    clear_output_folder()
    app.run(debug=True)
