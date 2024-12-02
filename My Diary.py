import sqlite3
from tkinter import *
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from fpdf import FPDF

class DiaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("My Diary")
        self.root.geometry("800x600")
        
        # Connect to SQLite database
        self.conn = sqlite3.connect("diary.db")
        self.cursor = self.conn.cursor()
        self.setup_database()

        # Main GUI components
        self.create_widgets()

    def setup_database(self):
        # Create tables for diary entries and tags
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            title TEXT,
            content TEXT,
            tags TEXT,
            mood TEXT,
            image_path TEXT
        )
        """)
        self.conn.commit()

    def create_widgets(self):
        # Add a logo at the top
        top_logo_frame = Frame(self.root)
        top_logo_frame.pack(side=TOP, fill=X)

        # Load the logo image
        try:
            logo_image = PhotoImage(file="logo.png")  # Replace 'logo.png' with your logo file
            logo_label = Label(top_logo_frame, image=logo_image)
            logo_label.image = logo_image  # Keep a reference to avoid garbage collection
            logo_label.pack(pady=10)
        except TclError:
            logo_label = Label(top_logo_frame, text="My Diary", font=("Arial", 24, "bold"))
            logo_label.pack(pady=10)

        # Top Frame for Entry Actions
        top_frame = Frame(self.root)
        top_frame.pack(side=TOP, fill=X, padx=10, pady=5)

        Button(top_frame, text="New Entry", command=self.new_entry, width=15).pack(side=LEFT, padx=5)
        Button(top_frame, text="View Entries", command=self.view_entries, width=15).pack(side=LEFT, padx=5)
        Button(top_frame, text="Delete Entry", command=self.delete_entry, width=15).pack(side=LEFT, padx=5)
        Button(top_frame, text="Export to PDF", command=self.export_to_pdf, width=15).pack(side=LEFT, padx=5)

        # Main Frame for Calendar and Diary Entry Display
        self.calendar = Calendar(self.root, selectmode="day")
        self.calendar.pack(side=LEFT, fill=Y, padx=10, pady=10)

        self.display_frame = Frame(self.root)
        self.display_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

        # Display Area
        self.display_text = Text(self.display_frame, wrap=WORD)
        self.display_text.pack(fill=BOTH, expand=True)

    def new_entry(self):
        # Create a new diary entry
        entry_window = Toplevel(self.root)
        entry_window.title("New Diary Entry")
        entry_window.geometry("400x500")

        Label(entry_window, text="Title:").pack(anchor=W, padx=10, pady=5)
        title_entry = Entry(entry_window, width=50)
        title_entry.pack(padx=10, pady=5)

        Label(entry_window, text="Tags (comma-separated):").pack(anchor=W, padx=10, pady=5)
        tags_entry = Entry(entry_window, width=50)
        tags_entry.pack(padx=10, pady=5)

        Label(entry_window, text="Mood:").pack(anchor=W, padx=10, pady=5)
        mood_entry = Entry(entry_window, width=50)
        mood_entry.pack(padx=10, pady=5)

        Label(entry_window, text="Content:").pack(anchor=W, padx=10, pady=5)
        content_text = Text(entry_window, wrap=WORD, height=10)
        content_text.pack(padx=10, pady=5)

        Button(entry_window, text="Save", command=lambda: self.save_entry(entry_window, title_entry.get(), 
                                                                          tags_entry.get(), mood_entry.get(), 
                                                                          content_text.get("1.0", END))).pack(pady=10)

    def save_entry(self, window, title, tags, mood, content):
        date = self.calendar.get_date()
        self.cursor.execute("""
        INSERT INTO entries (date, title, content, tags, mood, image_path)
        VALUES (?, ?, ?, ?, ?, NULL)
        """, (date, title, content, tags, mood))
        self.conn.commit()
        messagebox.showinfo("Success", "Entry saved!")
        window.destroy()

    def view_entries(self):
        # Display diary entries for the selected date
        selected_date = self.calendar.get_date()
        self.cursor.execute("SELECT title, content, tags, mood FROM entries WHERE date=?", (selected_date,))
        entries = self.cursor.fetchall()

        self.display_text.delete("1.0", END)
        if entries:
            for entry in entries:
                self.display_text.insert(END, f"Title: {entry[0]}\n")
                self.display_text.insert(END, f"Mood: {entry[3]}\n")
                self.display_text.insert(END, f"Tags: {entry[2]}\n")
                self.display_text.insert(END, f"Content:\n{entry[1]}\n")
                self.display_text.insert(END, "-"*50 + "\n")
        else:
            self.display_text.insert(END, "No entries found for this date.")

    def delete_entry(self):
        # Delete a diary entry for the selected date and title
        delete_window = Toplevel(self.root)
        delete_window.title("Delete Entry")
        delete_window.geometry("400x200")

        Label(delete_window, text="Select Date:").pack(anchor=W, padx=10, pady=5)
        selected_date = self.calendar.get_date()

        # Retrieve entries for the selected date
        self.cursor.execute("SELECT title FROM entries WHERE date=?", (selected_date,))
        titles = self.cursor.fetchall()

        if not titles:
            messagebox.showinfo("No Entries", "No entries found for the selected date.")
            delete_window.destroy()
            return

        Label(delete_window, text=f"Entries on {selected_date}:").pack(anchor=W, padx=10, pady=5)
        title_var = StringVar(delete_window)
        title_var.set(titles[0][0])  # Default to the first title

        # Dropdown to select the title
        OptionMenu(delete_window, title_var, *[title[0] for title in titles]).pack(padx=10, pady=10)

        def confirm_delete():
            selected_title = title_var.get()
            self.cursor.execute("DELETE FROM entries WHERE date=? AND title=?", (selected_date, selected_title))
            self.conn.commit()
            messagebox.showinfo("Deleted", f"Entry '{selected_title}' deleted successfully!")
            delete_window.destroy()

        Button(delete_window, text="Delete", command=confirm_delete).pack(pady=10)

    def export_to_pdf(self):
        # Export diary entries to a PDF
        selected_date = self.calendar.get_date()
        self.cursor.execute("SELECT title, content, tags, mood FROM entries WHERE date=?", (selected_date,))
        entries = self.cursor.fetchall()

        if not entries:
            messagebox.showwarning("No Entries", "No entries to export for the selected date.")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for entry in entries:
            pdf.cell(0, 10, f"Title: {entry[0]}", ln=True)
            pdf.cell(0, 10, f"Mood: {entry[3]}", ln=True)
            pdf.cell(0, 10, f"Tags: {entry[2]}", ln=True)
            pdf.multi_cell(0, 10, f"Content:\n{entry[1]}\n")
            pdf.cell(0, 10, "-"*50, ln=True)

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if save_path:
            pdf.output(save_path)
            messagebox.showinfo("Success", "PDF exported successfully!")

# Run the application
root = Tk()
app = DiaryApp(root)
root.mainloop()
