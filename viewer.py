import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # Hide pygame support prompt

import sys  # Add this import if not already present
if not sys.stdout:
    sys.stdout = open(os.devnull, 'w')
if not sys.stderr:
    sys.stderr = open(os.devnull, 'w')

try:
    import fitz  # PyMuPDF
except AssertionError:
    # Handle PyMuPDF initialization error during bundling
    import pymupdf
    fitz = pymupdf

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pygame
import zipfile
from mutagen.mp3 import MP3  # Add this import for MP3 files
import sys  # Add this import at the top with other imports

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Viewer with Music Player")
        self.root.configure(bg='#2e2e2e')  # Dark gray background
        
        # Initialize variables
        self.pdf_document = None
        self.cbz_images = []
        self.current_page = 0
        self.photo = None
        self.zoom_level = 1.0  # Default zoom level for both PDF and images
        self.music_files = []  # List of music files
        self.current_music_index = -1
        self.music_playing = False
        self.music_length = 0  # Length of the current music file in seconds
        self.comic_mode = False  # Comic viewing mode toggle
        self.dragging = False  # Initialize dragging flag

        # Initialize pygame mixer
        pygame.mixer.init()

        # Create a frame for the main layout
        self.main_frame = tk.Frame(self.root, bg='#2e2e2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the canvas and scrollbars
        self.canvas_scroll_frame = tk.Frame(self.main_frame, bg='#2e2e2e')
        self.canvas_scroll_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Canvas for displaying the PDF pages or images
        self.canvas = tk.Canvas(self.canvas_scroll_frame, bg='#1e1e1e', bd=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind mouse wheel events for scrolling
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)

        # Vertical Scrollbar
        self.v_scroll = tk.Scrollbar(self.canvas_scroll_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.v_scroll.set)

        # Horizontal Scrollbar Frame
        self.h_scroll_frame = tk.Frame(self.main_frame, bg='#2e2e2e')
        self.h_scroll_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Horizontal Scrollbar
        self.h_scroll = tk.Scrollbar(self.h_scroll_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.config(xscrollcommand=self.h_scroll.set)

        # Create top section frame
        self.top_section = tk.Frame(self.root, bg='#2e2e2e')  # Match the root background color
        self.top_section.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Create logo frame
        self.logo_frame = tk.Frame(self.top_section, bg='#2e2e2e')  # Match the root background color
        self.logo_frame.pack(side=tk.LEFT, padx=10)

        # Add logo image
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
            logo_path = os.path.join(script_dir, "math.ico")  # Use a relative path to the logo file
            self.logo_image = Image.open(logo_path)  # Ensure the path is correct
            self.logo_image = self.logo_image.resize((50, 50), Image.LANCZOS)  # Resize the image to a smaller size
            self.logo_photo = ImageTk.PhotoImage(self.logo_image)
            self.logo_label = tk.Label(self.logo_frame, image=self.logo_photo, bg='#2e2e2e')  # Match the root background color
            self.logo_label.pack(side=tk.LEFT)
        except Exception as e:
            print(f"Error loading logo image: {e}")
            self.logo_label = tk.Label(self.logo_frame, text="Logo", font=('Arial', 14, 'bold'), fg='white', bg='#2e2e2e')  # Match the root background color
            self.logo_label.pack(side=tk.LEFT)

        # Button Frame for navigation and zoom (modify existing button frame code)
        self.button_frame = tk.Frame(self.top_section, bg='#2e2e2e')  # Match the root background color
        self.button_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)

        # Button styling
        button_style = {'bg': '#4e4e4e', 'fg': 'white', 'font': ('Arial', 10, 'bold'), 'relief': tk.FLAT}

        # Create buttons with proper alignment
        buttons = [
            ("◄", self.prev_page),
            ("Open PDF/CBZ", self.open_file),
            ("►", self.next_page),
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out),
            ("Fit Width", self.fit_width),
            ("Fit Height", self.fit_height),
        ]

        for text, command in buttons:
            tk.Button(self.button_frame, text=text, command=command, **button_style).pack(side=tk.LEFT, padx=5, pady=5)

        # Add Jump to Page button and entry
        self.page_entry = tk.Entry(self.button_frame, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.button_frame, text="Go", command=self.jump_to_page, **button_style).pack(side=tk.LEFT, padx=5, pady=5)

        # Center align the buttons
        self.button_frame.pack(side=tk.TOP, fill=tk.X, padx=10)

        # Add toggle for Comic Mode
        self.comic_mode_button = tk.Checkbutton(self.button_frame, text="Quiet Mode", bg='#4e4e4e', fg='white', font=('Arial', 10, 'bold'), command=self.toggle_comic_mode)
        self.comic_mode_button.pack(side=tk.RIGHT, padx=10)

        # Music Player Frame
        self.music_frame = tk.Frame(self.root, bg='#2e2e2e')
        self.music_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # Music Player Controls
        tk.Button(self.music_frame, text="📂", command=self.open_music, **button_style).pack(side=tk.LEFT, padx=10)
        tk.Button(self.music_frame, text="▶", command=self.play_music, **button_style).pack(side=tk.LEFT, padx=10)
        tk.Button(self.music_frame, text="❚❚", command=self.pause_music, **button_style).pack(side=tk.LEFT, padx=10)
        tk.Button(self.music_frame, text="⏭", command=self.next_music, **button_style).pack(side=tk.LEFT, padx=10)
        tk.Button(self.music_frame, text="🔀", command=self.shuffle_music, **button_style).pack(side=tk.LEFT, padx=10)

        # Current Song Label
        self.song_label = tk.Label(self.music_frame, text="No song playing", bg='#2e2e2e', fg='white', font=('Arial', 10))
        self.song_label.pack(side=tk.LEFT, padx=10)

        # Current Time Label
        self.current_time_label = tk.Label(self.music_frame, text="00:00", bg='#2e2e2e', fg='white', font=('Arial', 10))
        self.current_time_label.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress_bar = tk.Scale(self.music_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, sliderrelief=tk.FLAT, bg='#4e4e4e', troughcolor='#1e1e1e', fg='white', showvalue=0)
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        self.progress_bar.bind("<ButtonPress-1>", self.start_drag)  # Bind event to start dragging
        self.progress_bar.bind("<ButtonRelease-1>", self.stop_drag)  # Bind event to stop dragging

        # Total Time Label
        self.total_time_label = tk.Label(self.music_frame, text="00:00", bg='#2e2e2e', fg='white', font=('Arial', 10))
        self.total_time_label.pack(side=tk.LEFT, padx=5)

        # Bind keyboard events
        self.root.bind("<Right>", self.next_page_key)
        self.root.bind("<Left>", self.prev_page_key)
        self.root.bind("<space>", self.toggle_play_pause_music)
        self.root.bind("<Control-Right>", self.next_music_key)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Up>", self.scroll_up)
        self.root.bind("<Down>", self.scroll_down)
        self.fullscreen = False

        # Check command line arguments for file to open
        if hasattr(sys, 'frozen'):
            # Running as a bundled executable
            if len(sys.argv) > 1:
                file_path = sys.argv[1]
                if file_path.lower().endswith('.pdf'):
                    self.open_pdf(file_path)
                elif file_path.lower().endswith('.cbz'):
                    self.open_cbz(file_path)
        else:
            # Running as a script
            if len(sys.argv) > 1:
                file_path = sys.argv[1]
                if file_path.lower().endswith('.pdf'):
                    self.open_pdf(file_path)
                elif file_path.lower().endswith('.cbz'):
                    self.open_cbz(file_path)

    def scroll_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def scroll_down(self, event):
        self.canvas.yview_scroll(1, "units")

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        self.resize_elements()
        return "break"

    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes("-fullscreen", False)
            self.resize_elements()
        return "break"

    def resize_elements(self):
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas_scroll_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.h_scroll_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.top_section.pack(side=tk.TOP, fill=tk.X, pady=5)
        self.music_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def toggle_comic_mode(self):
        self.comic_mode = not self.comic_mode
        if self.comic_mode:
            # Hide music player controls and show comic viewer settings
            self.music_frame.pack_forget()
        else:
            # Restore music player controls
            self.music_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("Comic Book Zip files", "*.cbz")])
        if file_path:
            if file_path.lower().endswith('.pdf'):
                self.open_pdf(file_path)
            elif file_path.lower().endswith('.cbz'):
                self.open_cbz(file_path)

    def resize_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        new_width = min(width, screen_width)
        new_height = min(height, screen_height)
        self.root.geometry(f"{new_width}x{new_height}")

    def open_pdf(self, file_path):
        try:
            self.pdf_document = fitz.open(file_path)
            self.current_page = 0
            self.zoom_level = 1.0
            self.show_page(self.current_page)
            # Resize window based on the first page size
            page = self.pdf_document[0]
            pix = page.get_pixmap()
            self.resize_window(pix.width, pix.height)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")
            self.pdf_document = None

    def open_cbz(self, file_path):
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                image_files = [f for f in zip_ref.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                image_files.sort()  # Sort files to display in order
                self.cbz_images = [Image.open(zip_ref.open(f)) for f in image_files]
                self.current_page = 0
                self.zoom_level = 1.0
                self.show_image(self.current_page)
                # Resize window based on the first image size
                img = self.cbz_images[0]
                self.resize_window(img.width, img.height)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open CBZ file: {e}")
            self.cbz_images = []

    def show_page(self, page_number):
        if self.pdf_document and 0 <= page_number < len(self.pdf_document):
            try:
                page = self.pdf_document[page_number]
                matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
                pix = page.get_pixmap(matrix=matrix, alpha=False)  # Ensure alpha is set to False
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                self.photo = ImageTk.PhotoImage(img)
                self.canvas.delete("all")

                # Calculate centered coordinates
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                img_width, img_height = img.size

                x = max((canvas_width - img_width) // 2, 0)
                y = max((canvas_height - img_height) // 2, 0)

                self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)

                # Update scroll region and reset view to top
                self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
                self.canvas.yview_moveto(0)
                self.root.title(f"PDF Viewer - Page {page_number + 1}/{len(self.pdf_document)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to render page: {e}")

    def show_image(self, page_number):
        if self.cbz_images and 0 <= page_number < len(self.cbz_images):
            try:
                img = self.cbz_images[page_number]
                img = img.resize((int(img.width * self.zoom_level), int(img.height * self.zoom_level)), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.canvas.delete("all")

                # Calculate centered coordinates
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                img_width, img_height = img.size

                x = max((canvas_width - img_width) // 2, 0)
                y = max((canvas_height - img_height) // 2, 0)

                self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)

                # Update scroll region and reset view to top
                self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
                self.canvas.yview_moveto(0)
                self.root.title(f"Comic Viewer - Page {page_number + 1}/{len(self.cbz_images)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to render image: {e}")

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def on_shift_mouse_wheel(self, event):
        self.canvas.xview_scroll(-1 * int(event.delta / 120), "units")

    def prev_page(self):
        if (self.pdf_document and self.current_page > 0) or (self.cbz_images and self.current_page > 0):
            self.current_page -= 1
            if self.pdf_document:
                self.show_page(self.current_page)
            elif self.cbz_images:
                self.show_image(self.current_page)

    def next_page(self):
        if (self.pdf_document and self.current_page < len(self.pdf_document) - 1) or (self.cbz_images and self.current_page < len(self.cbz_images) - 1):
            self.current_page += 1
            if self.pdf_document:
                self.show_page(self.current_page)
            elif self.cbz_images:
                self.show_image(self.current_page)

    def zoom_in(self):
        self.zoom_level *= 1.2
        if self.pdf_document:
            self.show_page(self.current_page)
        elif self.cbz_images:
            self.show_image(self.current_page)

    def zoom_out(self):
        self.zoom_level /= 1.2
        if self.pdf_document:
            self.show_page(self.current_page)
        elif self.cbz_images:
            self.show_image(self.current_page)

    def fit_width(self):
        if self.pdf_document:
            page = self.pdf_document[self.current_page]
            page_width = page.rect.width
            canvas_width = self.canvas.winfo_width()
            self.zoom_level = canvas_width / page_width
            self.show_page(self.current_page)
        elif self.cbz_images:
            img = self.cbz_images[self.current_page]
            img_width, _ = img.size
            canvas_width = self.canvas.winfo_width()
            self.zoom_level = canvas_width / img_width
            self.show_image(self.current_page)

    def fit_height(self):
        if self.pdf_document:
            page = self.pdf_document[self.current_page]
            page_height = page.rect.height
            canvas_height = self.canvas.winfo_height()
            self.zoom_level = canvas_height / page_height
            self.show_page(self.current_page)
        elif self.cbz_images:
            img = self.cbz_images[self.current_page]
            _, img_height = img.size
            canvas_height = self.canvas.winfo_height()
            self.zoom_level = canvas_height / img_height
            self.show_image(self.current_page)

    def open_music(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Audio files", "*.mp3;*.wav")])
        if file_paths:
            self.music_files = list(file_paths)
            self.current_music_index = 0
            if self.music_files:
                pygame.mixer.music.load(self.music_files[self.current_music_index])
                self.song_label.config(text=os.path.basename(self.music_files[self.current_music_index]))

    def play_music(self):
        if self.music_files:
            pygame.mixer.music.load(self.music_files[self.current_music_index])
            pygame.mixer.music.play()
            self.music_playing = True
            self.music_length = self.get_music_length(self.music_files[self.current_music_index])
            self.total_time_label.config(text=self.format_time(self.music_length))  # Update total time label
            self.update_music_progress()

    def get_music_length(self, file_path):
        if file_path.lower().endswith('.mp3'):
            audio = MP3(file_path)
            return audio.info.length
        else:
            audio = pygame.mixer.Sound(file_path)
            return audio.get_length()

    def pause_music(self):
        if self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False

    def next_music(self):
        if self.music_files:
            pygame.mixer.music.stop()
            self.current_music_index = (self.current_music_index + 1) % len(self.music_files)
            pygame.mixer.music.load(self.music_files[self.current_music_index])
            pygame.mixer.music.play()
            self.music_playing = True
            self.song_label.config(text=os.path.basename(self.music_files[self.current_music_index]))

    def shuffle_music(self):
        if self.music_files:
            import random
            random.shuffle(self.music_files)
            self.current_music_index = 0
            pygame.mixer.music.load(self.music_files[self.current_music_index])
            self.song_label.config(text=os.path.basename(self.music_files[self.current_music_index]))

    def update_music_progress(self):
        if self.music_playing and not self.dragging:
            current_pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
            progress = (current_pos / self.music_length) * 100 if self.music_length > 0 else 0
            self.progress_bar.set(progress)
            self.current_time_label.config(text=self.format_time(current_pos))  # Update current time label
            if current_pos < self.music_length:
                self.root.after(100, self.update_music_progress)  # Check every 100 milliseconds
            else:
                self.music_playing = False
                self.progress_bar.set(0)  # Reset progress bar when music ends
                self.current_time_label.config(text="00:00")  # Reset current time label

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}"

    def start_drag(self, event):
        self.dragging = True

    def stop_drag(self, event):
        self.dragging = False
        self.set_music_position(event)

    def set_music_position(self, event):
        if self.music_length > 0:
            new_position = self.progress_bar.get() / 100 * self.music_length  # Calculate new position in seconds
            pygame.mixer.music.set_pos(new_position)  # Set new position
            self.current_time_label.config(text=self.format_time(new_position))  # Update current time label

    def jump_to_page(self):
        try:
            page_number = int(self.page_entry.get()) - 1
            if self.pdf_document and 0 <= page_number < len(self.pdf_document):
                self.current_page = page_number
                self.show_page(self.current_page)
            elif self.cbz_images and 0 <= page_number < len(self.cbz_images):
                self.current_page = page_number
                self.show_image(self.current_page)
        except ValueError:
            messagebox.showerror("Error", "Invalid page number")

    # Keyboard input methods
    def next_page_key(self, event):
        self.next_page()

    def prev_page_key(self, event):
        self.prev_page()

    def toggle_play_pause_music(self, event):
        if self.music_playing:
            self.pause_music()
        else:
            self.play_music()

    def next_music_key(self, event):
        self.next_music()

if __name__ == "__main__":
    root = tk.Tk()
    viewer = PDFViewer(root)
    root.state('zoomed')  # Open the window maximized
    root.mainloop()
