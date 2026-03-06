import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os

# Try importing pyperclip for clipboard support
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

class JsonRefinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Refiner - Advanced Edition")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # Main Container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Toolbar ---
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # File Operations
        ttk.Label(toolbar, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Load JSON", command=self.load_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save JSON", command=self.save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Refine Operations
        ttk.Label(toolbar, text="Refine:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Pretty Print (Format)", command=self.pretty_print).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Minify (Compact)", command=self.minify_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Validate", command=self.validate_json).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Tools
        ttk.Button(toolbar, text="Clear", command=self.clear_text).pack(side=tk.LEFT, padx=2)
        if CLIPBOARD_AVAILABLE:
            ttk.Button(toolbar, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=2)

        # Search Bar
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="Search Key/Value:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(search_frame, text="Find Next", command=self.find_text).pack(side=tk.LEFT)

        # --- Editor Area ---
        editor_frame = ttk.Frame(main_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        # Line Numbers (Canvas)
        self.line_numbers = tk.Text(editor_frame, width=4, padx=4, takefocus=0, border=0,
                                    background="#f0f0f0", state='disabled', wrap='none')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Main Text Editor
        self.text_area = tk.Text(editor_frame, wrap="none", undo=True, font=("Consolas", 11))
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        v_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.sync_scroll_y)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(main_frame, orient="horizontal", command=self.text_area.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_area.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.line_numbers.config(yscrollcommand=v_scroll.set)

        # Bind events for line numbers
        self.text_area.bind('<KeyRelease>', self.update_line_numbers)
        self.text_area.bind('<MouseWheel>', self.sync_scroll_y_mouse)
        self.text_area.bind('<Button-1>', self.update_line_numbers)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def configure_styles(self):
        self.style.configure("TButton", font=("Segoe UI", 9))
        self.style.configure("TLabel", font=("Segoe UI", 9))

    def sync_scroll_y(self, *args):
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)

    def sync_scroll_y_mouse(self, *args):
        self.line_numbers.yview_moveto(self.text_area.yview()[0])
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        line_count = int(self.text_area.index('end-1c').split('.')[0])
        line_num_string = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', line_num_string)
        self.line_numbers.config(state='disabled')

    def get_json_content(self):
        return self.text_area.get("1.0", tk.END).strip()

    def set_json_content(self, content):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", content)
        self.update_line_numbers()

    def validate_json(self):
        content = self.get_json_content()
        if not content:
            self.status_var.set("Status: Empty content")
            return
        try:
            json.loads(content)
            messagebox.showinfo("Success", "Valid JSON Format!")
            self.status_var.set("Status: Valid JSON")
            return True
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Error at line {e.lineno}, column {e.colno}:\n{e.msg}")
            self.text_area.mark_set("insert", f"{e.lineno}.{e.colno}")
            self.text_area.see(f"{e.lineno}.{e.colno}")
            self.text_area.focus()
            self.status_var.set(f"Status: Error at line {e.lineno}")
            return False

    def pretty_print(self):
        content = self.get_json_content()
        if not content: return
        try:
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=4)
            self.set_json_content(formatted)
            self.status_var.set("Status: Formatted (Pretty Print)")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Cannot format invalid JSON:\n{e.msg}")

    def minify_json(self):
        content = self.get_json_content()
        if not content: return
        try:
            parsed = json.loads(content)
            minified = json.dumps(parsed, separators=(',', ':'))
            self.set_json_content(minified)
            self.status_var.set("Status: Minified")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Cannot minify invalid JSON:\n{e.msg}")

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.set_json_content(f.read())
                self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Load Error", str(e))

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.get_json_content())
                self.status_var.set(f"Saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.update_line_numbers()
        self.status_var.set("Cleared")

    def copy_to_clipboard(self):
        content = self.get_json_content()
        pyperclip.copy(content)
        self.status_var.set("Copied to clipboard")

    def find_text(self):
        self.text_area.tag_remove('found', '1.0', tk.END)
        target = self.search_var.get()
        if target:
            idx = '1.0'
            while True:
                idx = self.text_area.search(target, idx, nocase=1, stopindex=tk.END)
                if not idx: break
                lastidx = f'{idx}+{len(target)}c'
                self.text_area.tag_add('found', idx, lastidx)
                idx = lastidx
            self.text_area.tag_config('found', foreground='white', background='blue')
            self.status_var.set(f"Search complete for '{target}'")

if __name__ == "__main__":
    root = tk.Tk()
    # Set icon if available, otherwise ignore
    # root.iconbitmap('icon.ico') 
    app = JsonRefinerApp(root)
    root.mainloop()
