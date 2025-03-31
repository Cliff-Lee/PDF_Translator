#!/usr/bin/env python3
"""
PDF Translator for Ubuntu with Extended Language Pairs, OCR, Progress Updates, Save & Navigation
----------------------------------------------------------------------------------------------
This script creates a GUI application that:
  - Automatically installs language packages (if available) for:
      • Korean ↔ English
      • German ↔ English
      • Chinese ↔ English
      • Spanish ↔ English
  - Extracts text from a selected PDF.
    - If text extraction fails (e.g. scanned pages), it uses OCR via pytesseract.
  - Translates the text using Argos Translate.
  - Generates a new, formatted PDF with the translated text.
  - Provides a progress bar for large files.
  - Allows navigation of pages (both original and translated PDFs) via Previous/Next buttons.
  - Displays side‑by‑side previews and supports window resizing.
  - Allows the user to save the translated PDF to a chosen location.

Ubuntu Setup:
1. Install system dependencies (for pdf2image and OCR):
     sudo apt-get install poppler-utils tesseract-ocr
2. Create and activate a virtual environment, then install required Python packages:
     pip install PyPDF2 argostranslate reportlab pdf2image pillow pytesseract
3. Ensure you are connected to the internet to download language packages.
"""

import os
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import PyPDF2
from argostranslate import package, translate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import pytesseract  # For OCR

# Modified function: now accepts a page number.
def get_pdf_preview_image(pdf_path, page_number=1):
    try:
        images = convert_from_path(pdf_path, dpi=100, first_page=page_number, last_page=page_number)
        if images:
            return images[0]
        else:
            raise Exception("No pages found in PDF.")
    except Exception as e:
        raise Exception("Error generating preview image: " + str(e))

# Automatically install required language pairs.
def install_required_language_pairs():
    print("Updating package index...")
    package.update_package_index()
    available_packages = package.get_available_packages()
    # Required language pairs: (source, target)
    required_pairs = [
        ('ko','en'), ('en','ko'),
        ('de','en'), ('en','de'),
        ('zh','en'), ('en','zh'),
        ('es','en'), ('en','es')
    ]
    installed_langs = translate.get_installed_languages()

    def is_pair_installed(src, tgt, installed_langs):
        for lang in installed_langs:
            if lang.code == src:
                for trans in lang.translations_to:
                    if trans.to_lang.code == tgt:
                        return True
        return False

    for src, tgt in required_pairs:
        if not is_pair_installed(src, tgt, installed_langs):
            found_package = None
            for pkg in available_packages:
                if pkg.from_code == src and pkg.to_code == tgt:
                    found_package = pkg
                    break
            if found_package:
                print(f"Installing language package for {src} -> {tgt}...")
                pkg_path = found_package.download()
                package.install_from_path(pkg_path)
                installed_langs = translate.get_installed_languages()
            else:
                print(f"No available package found for {src} -> {tgt}.")

# Extract text from PDF with OCR fallback. Updates progress (50% total).
def extract_text_from_pdf(pdf_path, progress_callback=None):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for i, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                else:
                    try:
                        images = convert_from_path(pdf_path, dpi=200, first_page=i, last_page=i)
                        if images:
                            ocr_text = pytesseract.image_to_string(images[0])
                            text += ocr_text + "\n"
                    except Exception as ocr_e:
                        raise Exception(f"Error during OCR on page {i}: " + str(ocr_e))
                if progress_callback:
                    progress_callback((i / num_pages) * 50)
    except Exception as e:
        raise Exception("Error extracting text from PDF: " + str(e))
    if not text.strip():
        raise Exception("No text could be extracted from the PDF.")
    return text

# Translate text using Argos Translate.
def translate_text(text, from_lang_code, to_lang_code):
    try:
        installed_languages = translate.get_installed_languages()
        from_lang_obj = None
        to_lang_obj = None
        for lang in installed_languages:
            if lang.code == from_lang_code:
                from_lang_obj = lang
            if lang.code == to_lang_code:
                to_lang_obj = lang
        if not from_lang_obj or not to_lang_obj:
            raise Exception("Translation packages for the selected language pair are not installed.")
        translation = from_lang_obj.get_translation(to_lang_obj)
        return translation.translate(text)
    except Exception as e:
        raise Exception("Error during translation: " + str(e))

# Create a formatted PDF using ReportLab.
def create_translated_pdf(text, output_pdf_path):
    try:
        doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            para = para.replace('\n', ' ')
            if para.strip():
                story.append(Paragraph(para.strip(), styles["Normal"]))
                story.append(Spacer(1, 12))
        doc.build(story)
    except Exception as e:
        raise Exception("Error creating translated PDF: " + str(e))

# Main GUI Application Class.
class PDFTranslatorApp:
    def __init__(self, master):
        self.master = master
        master.title("PDF Translator for Ubuntu")
        # Allow window resizing.
        master.resizable(True, True)
        self.input_pdf_path = None
        self.output_pdf_path = "translated.pdf"
        self.original_current_page = 1
        self.original_total_pages = 0
        self.translated_current_page = 1
        self.translated_total_pages = 0

        # Top control frame.
        control_frame = tk.Frame(master)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Preview frame.
        preview_frame = tk.Frame(master)
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # File selection.
        self.select_button = tk.Button(control_frame, text="Select Input PDF", command=self.select_pdf)
        self.select_button.grid(row=0, column=0, padx=5, pady=5)
        self.pdf_label = tk.Label(control_frame, text="No file selected")
        self.pdf_label.grid(row=0, column=1, padx=5, pady=5)

        # Language selection.
        self.source_lang_label = tk.Label(control_frame, text="Source Language:")
        self.source_lang_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.target_lang_label = tk.Label(control_frame, text="Target Language:")
        self.target_lang_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")

        self.installed_languages = translate.get_installed_languages()
        self.language_options = {}
        for lang in self.installed_languages:
            name = getattr(lang, "name", lang.code)
            display = f"{name} ({lang.code})"
            self.language_options[display] = lang.code

        if not self.language_options:
            messagebox.showerror("Error", "No languages installed in Argos Translate.\nPlease install language packages.")
            master.quit()

        language_list = list(self.language_options.keys())
        self.source_lang_combo = ttk.Combobox(control_frame, values=language_list, state="readonly")
        self.source_lang_combo.grid(row=1, column=1, padx=5, pady=5)
        self.source_lang_combo.current(0)
        self.target_lang_combo = ttk.Combobox(control_frame, values=language_list, state="readonly")
        self.target_lang_combo.grid(row=2, column=1, padx=5, pady=5)
        if len(language_list) > 1:
            self.target_lang_combo.current(1)
        else:
            self.target_lang_combo.current(0)

        # Translate button.
        self.translate_button = tk.Button(control_frame, text="Translate PDF", command=self.translate_pdf)
        self.translate_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Progress bar.
        self.progress_bar = ttk.Progressbar(control_frame, orient="horizontal", length=300, mode="determinate", maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # Save button.
        self.save_button = tk.Button(control_frame, text="Save Translated PDF", command=self.save_translated_pdf, state=tk.DISABLED)
        self.save_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        # ORIGINAL PDF PREVIEW PANEL.
        self.original_preview_frame = tk.LabelFrame(preview_frame, text="Original PDF Preview")
        self.original_preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.original_canvas = tk.Canvas(self.original_preview_frame, bg="gray")
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        # Navigation controls for original PDF.
        self.original_nav_frame = tk.Frame(self.original_preview_frame)
        self.original_nav_frame.pack(fill=tk.X)
        self.prev_orig_button = tk.Button(self.original_nav_frame, text="Previous", command=self.prev_original_page, state=tk.DISABLED)
        self.prev_orig_button.pack(side=tk.LEFT, padx=5, pady=2)
        self.orig_page_label = tk.Label(self.original_nav_frame, text="Page 0 of 0")
        self.orig_page_label.pack(side=tk.LEFT, padx=5)
        self.next_orig_button = tk.Button(self.original_nav_frame, text="Next", command=self.next_original_page, state=tk.DISABLED)
        self.next_orig_button.pack(side=tk.LEFT, padx=5, pady=2)

        # TRANSLATED PDF PREVIEW PANEL.
        self.translated_preview_frame = tk.LabelFrame(preview_frame, text="Translated PDF Preview")
        self.translated_preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.translated_canvas = tk.Canvas(self.translated_preview_frame, bg="gray")
        self.translated_canvas.pack(fill=tk.BOTH, expand=True)
        # Navigation controls for translated PDF.
        self.translated_nav_frame = tk.Frame(self.translated_preview_frame)
        self.translated_nav_frame.pack(fill=tk.X)
        self.prev_trans_button = tk.Button(self.translated_nav_frame, text="Previous", command=self.prev_translated_page, state=tk.DISABLED)
        self.prev_trans_button.pack(side=tk.LEFT, padx=5, pady=2)
        self.trans_page_label = tk.Label(self.translated_nav_frame, text="Page 0 of 0")
        self.trans_page_label.pack(side=tk.LEFT, padx=5)
        self.next_trans_button = tk.Button(self.translated_nav_frame, text="Next", command=self.next_translated_page, state=tk.DISABLED)
        self.next_trans_button.pack(side=tk.LEFT, padx=5, pady=2)

        # Image references.
        self.original_image_tk = None
        self.translated_image_tk = None

    def update_progress(self, value):
        self.master.after(0, lambda: self.progress_bar.config(value=value))

    def select_pdf(self):
        file_path = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.input_pdf_path = file_path
            self.pdf_label.config(text=os.path.basename(file_path))
            # Get total pages of the original PDF.
            try:
                with open(self.input_pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    self.original_total_pages = len(reader.pages)
            except Exception as e:
                messagebox.showerror("Error", "Failed to read PDF: " + str(e))
                return

            # Enable navigation if more than one page.
            if self.original_total_pages > 1:
                self.prev_orig_button.config(state=tk.NORMAL)
                self.next_orig_button.config(state=tk.NORMAL)
            else:
                self.prev_orig_button.config(state=tk.DISABLED)
                self.next_orig_button.config(state=tk.DISABLED)
            self.original_current_page = 1
            self.display_original_preview(self.original_current_page)

    def display_original_preview(self, page):
        try:
            img = get_pdf_preview_image(self.input_pdf_path, page_number=page)
            self.original_image_tk = ImageTk.PhotoImage(img)
            self.original_canvas.delete("all")
            self.original_canvas.create_image(0, 0, anchor="nw", image=self.original_image_tk)
            self.orig_page_label.config(text=f"Page {page} of {self.original_total_pages}")
        except Exception as e:
            messagebox.showerror("Error", "Original preview: " + str(e))

    def display_translated_preview(self, page):
        try:
            img = get_pdf_preview_image(self.output_pdf_path, page_number=page)
            self.translated_image_tk = ImageTk.PhotoImage(img)
            self.translated_canvas.delete("all")
            self.translated_canvas.create_image(0, 0, anchor="nw", image=self.translated_image_tk)
            self.trans_page_label.config(text=f"Page {page} of {self.translated_total_pages}")
        except Exception as e:
            messagebox.showerror("Error", "Translated preview: " + str(e))

    def prev_original_page(self):
        if self.original_current_page > 1:
            self.original_current_page -= 1
            self.display_original_preview(self.original_current_page)

    def next_original_page(self):
        if self.original_current_page < self.original_total_pages:
            self.original_current_page += 1
            self.display_original_preview(self.original_current_page)

    def prev_translated_page(self):
        if self.translated_current_page > 1:
            self.translated_current_page -= 1
            self.display_translated_preview(self.translated_current_page)

    def next_translated_page(self):
        if self.translated_current_page < self.translated_total_pages:
            self.translated_current_page += 1
            self.display_translated_preview(self.translated_current_page)

    def save_translated_pdf(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if save_path:
            try:
                shutil.copy(self.output_pdf_path, save_path)
                messagebox.showinfo("Saved", f"Translated PDF saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")

    def translate_pdf(self):
        if not self.input_pdf_path:
            messagebox.showerror("Error", "Please select an input PDF file.")
            return

        source_lang_display = self.source_lang_combo.get()
        target_lang_display = self.target_lang_combo.get()
        source_lang = self.language_options.get(source_lang_display)
        target_lang = self.language_options.get(target_lang_display)

        self.translate_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.update_progress(0)

        def process_translation():
            try:
                # Extract text with OCR (50% progress).
                extracted_text = extract_text_from_pdf(self.input_pdf_path, progress_callback=self.update_progress)
                self.update_progress(50)
                # Translate text (progress to 75%).
                translated_text = translate_text(extracted_text, source_lang, target_lang)
                self.update_progress(75)
                # Create the translated PDF.
                create_translated_pdf(translated_text, self.output_pdf_path)
                self.update_progress(100)
                self.master.after(0, lambda: messagebox.showinfo("Success", f"Translated PDF saved as {self.output_pdf_path}"))
                # After creation, get total pages of translated PDF.
                try:
                    with open(self.output_pdf_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        self.translated_total_pages = len(reader.pages)
                except Exception as e:
                    self.translated_total_pages = 1
                self.translated_current_page = 1
                self.master.after(0, self.display_translated_preview, self.translated_current_page)
                # Enable navigation for translated PDF if applicable.
                if self.translated_total_pages > 1:
                    self.master.after(0, lambda: self.prev_trans_button.config(state=tk.NORMAL))
                    self.master.after(0, lambda: self.next_trans_button.config(state=tk.NORMAL))
                else:
                    self.master.after(0, lambda: self.prev_trans_button.config(state=tk.DISABLED))
                    self.master.after(0, lambda: self.next_trans_button.config(state=tk.DISABLED))
                self.master.after(0, lambda: self.save_button.config(state=tk.NORMAL))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.update_progress(0)
            finally:
                self.master.after(0, lambda: self.translate_button.config(state=tk.NORMAL))

        threading.Thread(target=process_translation).start()

def main():
    install_required_language_pairs()
    root = tk.Tk()
    app = PDFTranslatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
