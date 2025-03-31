PDF Translator for Ubuntu
This project is a free and open source PDF translator for Ubuntu that leverages OCR, neural machine translation, and PDF generation to translate your documents. It supports extended language pairs (including Korean, German, Chinese, Spanish ↔ English), provides progress updates for large files, and features a resizable window with page navigation for both original and translated PDFs.

Features
OCR Support: Uses Tesseract OCR when PDF pages are scanned images.
Language Pairs: Automatically installs language packages for: Korean ↔ English, German ↔ English, Chinese ↔ English, Spanish ↔ English
Progress Updates: Displays a progress bar during extraction, translation, and PDF creation.
Page Navigation: Navigate through the pages of both the original and translated PDFs using Previous/Next buttons.
Resizable Window: The GUI window resizes and adapts to your screen.
Save Functionality: Save the translated PDF to a location of your choice.

Prerequisites
System Dependencies
Make sure to install the following system packages on Ubuntu:

sudo apt-get update
sudo apt-get install poppler-utils tesseract-ocr
poppler-utils: Required by pdf2image to convert PDF pages into images.
tesseract-ocr: Required for Optical Character Recognition (OCR).

Python Dependencies
All Python dependencies are listed in the requirements.txt file.

Setup Instructions
1. Clone or Download the Repository
Download the project files into your preferred directory.
2. Create a Virtual Environment

Open a terminal in the project directory and create a new virtual environment:

python3 -m venv venv

Activate the virtual environment:

source venv/bin/activate

3. Install Python Requirements
Install all required Python packages using pip:

pip install -r requirements.txt

4. Run the Application
Once the virtual environment is activated and the dependencies are installed, run the PDF translator:

python3 pdf_translator.py

Usage
Select Input PDF:
Click the "Select Input PDF" button to choose the PDF file you wish to translate.

Language Selection:
Use the drop-down menus to choose the source and target languages.

Translate PDF:
Click the "Translate PDF" button. The application will:

Extract text (using OCR if necessary).

Translate the extracted text.
Generate a new, formatted PDF with the translated text.
Update the progress bar during processing.

Page Navigation:
Use the Previous/Next buttons in the Original and Translated PDF Preview panels to navigate through the pages.

Save Translated PDF:
Click the "Save Translated PDF" button to save the output PDF to a desired location.

Troubleshooting
Tkinter Not Found:
If you encounter an error regarding tkinter, install it via:

sudo apt-get install python3-tk

Missing System Dependencies:
Ensure that poppler-utils and tesseract-ocr are properly installed as per the prerequisites.

License
This project is free and open source. Contributions are welcome!
