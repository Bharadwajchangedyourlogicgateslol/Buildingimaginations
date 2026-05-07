import os
import shutil
from PIL import Image
from PyPDF2 import PdfReader
from ebooklib import epub
from tkinter import (Tk, Label, Button, Spinbox,
                     filedialog, messagebox, StringVar,
                     IntVar, Frame)
from tkinter.ttk import Progressbar, Style
import threading

# You'll need: pip install pymupdf
import fitz  # PyMuPDF

TEMP_IMG_DIR = 'temp_pages'

class PDF2EPUBApp:
    def __init__(self, master):
        self.master = master
        master.title("Universal PDF to EPUB Converter")
        master.geometry("480x320")
        master.configure(bg="#ffffff")
        self.selected_files = []

        # UI Style
        style = Style()
        style.theme_use('default')
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TProgressbar", thickness=12)

        self.label = Label(master, text="Select PDF files to convert", bg="#ffffff", fg="#333333")
        self.label.pack(pady=(15, 5))

        self.browse_button = Button(master, text="Browse PDFs", command=self.browse_files)
        self.browse_button.pack(pady=8)

        # DPI
        dpi_frame = Frame(master, bg="#ffffff")
        dpi_frame.pack(pady=5)
        Label(dpi_frame, text="DPI:", bg="#ffffff").pack(side="left")
        self.dpi_var = IntVar(value=300)
        self.dpi_spinbox = Spinbox(dpi_frame, from_=72, to=600, increment=50,
                                   textvariable=self.dpi_var, width=6)
        self.dpi_spinbox.pack(side="left", padx=(5, 0))

        self.convert_button = Button(master, text="Convert to EPUB", state="disabled",
                                     command=self.run_conversion_thread)
        self.convert_button.pack(pady=15)

        self.progress = Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=(10, 5))

        self.status_var = StringVar(value="")
        self.status_label = Label(master, textvariable=self.status_var,
                                  bg="#ffffff", fg="#444444")
        self.status_label.pack()

    def browse_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if files:
            self.selected_files = list(files)
            self.label.config(text=f"{len(files)} PDF(s) selected")
            self.convert_button.config(state="normal")

    def run_conversion_thread(self):
        thread = threading.Thread(target=self.start_conversion)
        thread.start()

    def start_conversion(self):
        dpi = self.dpi_var.get()
        self.convert_button.config(state="disabled")
        
        for file in self.selected_files:
            try:
                self.status_var.set(f"Converting: {os.path.basename(file)}")
                self.convert_file(file, dpi)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to convert {os.path.basename(file)}:\n{str(e)}")
            finally:
                self.progress['value'] = 0
                self.status_var.set("")

        messagebox.showinfo("Success", "All files converted successfully!")
        self.convert_button.config(state="normal")

    def convert_file(self, pdf_path, dpi):
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_path = os.path.join(os.path.dirname(pdf_path), base + ".epub")

        if not os.path.exists(TEMP_IMG_DIR):
            os.makedirs(TEMP_IMG_DIR)

        # === FIXED: Real PDF to Image rendering using PyMuPDF ===
        doc = fitz.open(pdf_path)
        total = len(doc)
        self.progress['maximum'] = total
        images = []

        for idx, page in enumerate(doc):
            self.status_var.set(f"{base}: page {idx+1}/{total}")
            self.master.update_idletasks()

            # Render page to image
            pix = page.get_pixmap(dpi=dpi)
            img_path = os.path.join(TEMP_IMG_DIR, f"page_{idx+1:03d}.jpg")
            pix.save(img_path)
            
            images.append(img_path)
            self.progress['value'] = idx + 1

        doc.close()

        # === Create EPUB ===
        book = epub.EpubBook()
        book.set_identifier(base)
        book.set_title(base)
        book.set_language('en')

        spine = ['nav']

        for idx, img_path in enumerate(images):
            with open(img_path, 'rb') as f:
                content = f.read()

            item = epub.EpubItem(uid=f"img_{idx}",
                                 file_name=f"images/page_{idx+1:03d}.jpg",
                                 media_type='image/jpeg',
                                 content=content)
            book.add_item(item)

            html = f'''<html><body style="margin:0;padding:0;">
                        <img src="images/page_{idx+1:03d}.jpg" style="width:100%;height:auto;"/>
                       </body></html>'''

            page = epub.EpubHtml(title=f'Page {idx+1}',
                                 file_name=f'page_{idx+1:03d}.xhtml',
                                 lang='en')
            page.content = html
            book.add_item(page)
            spine.append(page)

        book.spine = spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(out_path, book)

        # Cleanup
        shutil.rmtree(TEMP_IMG_DIR, ignore_errors=True)
        self.status_var.set(f"Finished: {base}.epub")


if __name__ == "__main__":
    root = Tk()
    app = PDF2EPUBApp(root)
    root.mainloop()
