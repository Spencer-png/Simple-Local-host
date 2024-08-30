import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
from tkinterdnd2 import TkinterDnD, DND_FILES
from http.server import HTTPServer, SimpleHTTPRequestHandler

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        file_path = self.translate_path(self.path)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
        else:
            self.send_error(404, "File not found")

class FileServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local File Server")
        self.root.geometry("700x500")
        self.root.configure(bg="#000000")  # Set a black background color (Black)

        # Server variables
        self.directory = ctk.StringVar(value=os.path.abspath("."))
        self.port = ctk.IntVar(value=8000)
        self.border_color = "#FFFFFF"  # Default border color (White)
        self.server_thread = None

        # UI Elements
        self.create_widgets()
        self.add_drag_and_drop_support()

    def create_widgets(self):
        # Directory selection
        ctk.CTkLabel(self.root, text="Directory to Serve:", text_color="#FFFFFF", bg_color="#000000").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.directory_entry = ctk.CTkEntry(self.root, textvariable=self.directory, width=400, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2)
        self.directory_entry.grid(row=0, column=1, padx=10, pady=10)
        self.browse_directory_button = ctk.CTkButton(self.root, text="Browse", command=self.browse_directory, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2, hover_color="#333333")
        self.browse_directory_button.grid(row=0, column=2, padx=10, pady=10)

        # Port selection
        ctk.CTkLabel(self.root, text="Port:", text_color="#FFFFFF", bg_color="#000000").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.port_entry = ctk.CTkEntry(self.root, textvariable=self.port, width=100, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2)
        self.port_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Start server button
        self.start_button = ctk.CTkButton(self.root, text="Start Server", command=self.start_server, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2, hover_color="#333333")
        self.start_button.grid(row=2, column=1, padx=10, pady=10)

        # File name input with browse button
        ctk.CTkLabel(self.root, text="File to Retrieve:", text_color="#FFFFFF", bg_color="#000000").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.file_name_entry = ctk.CTkEntry(self.root, width=400, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2)
        self.file_name_entry.grid(row=3, column=1, padx=10, pady=10)
        self.browse_file_button = ctk.CTkButton(self.root, text="Browse", command=self.browse_file, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2, hover_color="#333333")
        self.browse_file_button.grid(row=3, column=2, padx=10, pady=10)

        # Get file content button
        self.get_file_content_button = ctk.CTkButton(self.root, text="Get File Content", command=self.get_file_content, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2, hover_color="#333333")
        self.get_file_content_button.grid(row=4, column=2, padx=10, pady=10)

        # Copy URL button
        self.copy_url_button = ctk.CTkButton(self.root, text="Copy URL", command=self.copy_url, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2, hover_color="#333333")
        self.copy_url_button.grid(row=4, column=1, padx=10, pady=10)

        # Text area to display file content
        self.file_content_text = ctk.CTkTextbox(self.root, wrap="word", height=200, width=600, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2)
        self.file_content_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

        # Color picker button
        self.choose_color_button = ctk.CTkButton(self.root, text="Choose Border Color", command=self.choose_color, fg_color="#000000", text_color="#FFFFFF", border_color=self.border_color, corner_radius=10, border_width=2, hover_color="#333333")
        self.choose_color_button.grid(row=6, column=1, padx=10, pady=10)

    def add_drag_and_drop_support(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        file_path = event.data.strip('{}')
        if os.path.isfile(file_path):
            self.directory.set(os.path.dirname(file_path))
            self.file_name_entry.delete(0, ctk.END)
            self.file_name_entry.insert(0, os.path.basename(file_path))
            if self.server_thread is None:
                self.start_server()
            self.get_file_content()

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.directory.get())
        if directory:
            self.directory.set(directory)

    def browse_file(self):
        file_path = filedialog.askopenfilename(initialdir=self.directory.get(), title="Select File")
        if file_path:
            self.file_name_entry.delete(0, ctk.END)
            self.file_name_entry.insert(0, os.path.basename(file_path))
            self.directory.set(os.path.dirname(file_path))

    def start_server(self):
        if self.server_thread is None:
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            messagebox.showinfo("Server Started", f"Serving files at http://localhost:{self.port.get()}/")

    def run_server(self):
        os.chdir(self.directory.get())
        handler = lambda *args, **kwargs: CustomHandler(*args, directory=self.directory.get(), **kwargs)
        httpd = HTTPServer(('localhost', self.port.get()), handler)
        httpd.serve_forever()

    def get_file_content(self):
        file_path = os.path.join(self.directory.get(), self.file_name_entry.get())
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                self.file_content_text.delete(1.0, ctk.END)
                self.file_content_text.insert(ctk.END, content)
        else:
            messagebox.showerror("Error", f"File '{self.file_name_entry.get()}' not found.")

    def copy_url(self):
        file_name = self.file_name_entry.get()
        if file_name:
            url = f"http://localhost:{self.port.get()}/{file_name}"
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("URL Copied", f"URL copied to clipboard: {url}")
        else:
            messagebox.showerror("Error", "No file selected to generate a URL.")

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Choose Border Color")[1]  # Get the hex color code
        if color_code:
            self.border_color = color_code
            self.update_border_colors()

    def update_border_colors(self):
        # Update the border colors of all widgets
        self.directory_entry.configure(border_color=self.border_color) # Directory 
        self.port_entry.configure(border_color=self.border_color) # Port selection 
        self.file_name_entry.configure(border_color=self.border_color) # File name 
        self.file_content_text.configure(border_color=self.border_color) # display file content
        self.start_button.configure(border_color=self.border_color) # Start button 
        self.choose_color_button.configure(border_color=self.border_color) # Choose color button
        self.browse_directory_button.configure(border_color=self.border_color) # Browse directory button
        self.browse_file_button.configure(border_color=self.border_color) # Browse file button
        self.get_file_content_button.configure(border_color=self.border_color) # Get file content button
        self.copy_url_button.configure(border_color=self.border_color) # Copy url 
        self.root.update()

if __name__ == "__main__":
    root = TkinterDnD.Tk()  # TkinterDnD's Tk class 
    app = FileServerApp(root)
    root.mainloop()

