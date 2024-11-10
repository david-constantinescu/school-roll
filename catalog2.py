import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import sqlite3
import os
from datetime import datetime
from statistics import median
import webbrowser
import subprocess
import shutil
import platform

# Database setup
conn = sqlite3.connect('school_roll.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                grade REAL,
                date TEXT,
                pdf_path TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )''')
conn.commit()

# GUI class
class SchoolRollApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Roll")
        self.root.geometry("600x400")

        # Frames
        self.frame_top = tk.Frame(root)
        self.frame_top.pack(pady=10)

        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.pack(pady=10)

        # Student List
        self.student_listbox = tk.Listbox(self.frame_top, width=30, height=10)
        self.student_listbox.grid(row=0, column=0, rowspan=4, padx=10)

        self.load_students()

        # Entry and buttons
        tk.Label(self.frame_top, text="Student Name:").grid(row=0, column=1, sticky="w")
        self.entry_name = tk.Entry(self.frame_top)
        self.entry_name.grid(row=0, column=2)

        self.btn_add_student = tk.Button(self.frame_top, text="Add Student", command=self.add_student)
        self.btn_add_student.grid(row=1, column=2)

        self.btn_add_grade = tk.Button(self.frame_top, text="Add Grade", command=self.add_grade)
        self.btn_add_grade.grid(row=2, column=2)

        self.btn_view_grades = tk.Button(self.frame_top, text="View Grades", command=self.view_grades)
        self.btn_view_grades.grid(row=3, column=2)

        # Student Grades
        self.grades_text = tk.Text(self.frame_bottom, width=60, height=10)
        self.grades_text.pack()

    def load_students(self):
        self.student_listbox.delete(0, tk.END)
        c.execute("SELECT * FROM students")
        for student in c.fetchall():
            self.student_listbox.insert(tk.END, f"{student[0]}: {student[1]}")

    def add_student(self):
        name = self.entry_name.get().strip()
        if name:
            c.execute("INSERT INTO students (name) VALUES (?)", (name,))
            conn.commit()
            self.load_students()
            self.entry_name.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Student name cannot be empty.")

    def add_grade(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Error", "Please select a student.")
            return

        grade = tk.simpledialog.askfloat("Grade", "Enter grade:")
        if grade is None:
            return  # User canceled

        date = datetime.now().strftime("%Y-%m-%d")
        pdf_path = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF Files", "*.pdf")])
        if not pdf_path:
            messagebox.showerror("Error", "You must select a PDF file.")
            return

        # Insert grade into database
        c.execute("INSERT INTO grades (student_id, grade, date, pdf_path) VALUES (?, ?, ?, ?)",
                  (student_id, grade, date, pdf_path))
        conn.commit()
        messagebox.showinfo("Success", "Grade added successfully.")

    def view_grades(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Error", "Please select a student.")
            return

        c.execute("SELECT id, grade, date, pdf_path FROM grades WHERE student_id = ?", (student_id,))
        grades = c.fetchall()

        if not grades:
            messagebox.showinfo("No Grades", "No grades available for this student.")
            return

        # Clear any existing tags and text
        self.grades_text.delete(1.0, tk.END)

        grades_list = [grade[1] for grade in grades]
        median_grade = median(grades_list)

        # Display grades with clickable PDF filenames
        self.grades_text.insert(tk.END, f"Grades for Student ID {student_id}:\n\n")
        for i, (grade_id, grade, date, pdf_path) in enumerate(grades):
            pdf_name = os.path.basename(pdf_path)
            self.grades_text.insert(tk.END, f"Grade: {grade}, Date: {date}, PDF: ")

            # Insert PDF filename with a unique tag for each file
            tag_name = f"pdf_{i}"
            self.grades_text.insert(tk.END, pdf_name + "\n", tag_name)

            # Add event binding for double-click on this PDF tag
            self.grades_text.tag_bind(tag_name, "<Double-1>", lambda e, path=pdf_path: self.open_pdf(path))

            # Add a Download button next to each grade
            download_button = tk.Button(self.frame_bottom, text="Download", command=lambda path=pdf_path: self.download_pdf(path))
            self.grades_text.window_create(tk.END, window=download_button)

        self.grades_text.insert(tk.END, f"\nMedian Grade: {median_grade:.2f}")

    def open_pdf(self, pdf_path):
        """Open the specified PDF file with the default viewer."""
        if os.path.exists(pdf_path):
            if platform.system() == "Darwin":  # macOS
                subprocess.call(["open", pdf_path])  # Use the macOS 'open' command
            else:
                webbrowser.open(pdf_path)  # Use default webbrowser for other OS
        else:
            messagebox.showerror("Error", "The PDF file could not be found.")

    def download_pdf(self, pdf_path):
        """Download the specified PDF file to the user's Downloads folder."""
        if os.path.exists(pdf_path):
            downloads_folder = os.path.expanduser("~/Downloads")
            destination_path = os.path.join(downloads_folder, os.path.basename(pdf_path))
            shutil.copy(pdf_path, destination_path)
            messagebox.showinfo("Download Complete", f"File downloaded to {destination_path}")
        else:
            messagebox.showerror("Error", "The PDF file could not be found.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolRollApp(root)
    root.mainloop()