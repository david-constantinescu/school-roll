import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import sqlite3
import os
from datetime import datetime
from statistics import median
import webbrowser
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
        self.root.geometry("600x550")

        # Frames
        self.frame_top = tk.Frame(root)
        self.frame_top.pack(pady=10)

        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.pack(pady=10)

        # Student List
        self.student_listbox = tk.Listbox(self.frame_top, width=30, height=10)
        self.student_listbox.grid(row=0, column=0, rowspan=5, padx=10)

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

        # Download PDF button above Edit/Delete Grades
        self.btn_download_pdf = tk.Button(self.frame_top, text="Download PDF", command=self.download_pdf)
        self.btn_download_pdf.grid(row=4, column=2)

        self.btn_edit_delete_grade = tk.Button(self.frame_top, text="Edit/Delete Grades", command=self.edit_or_delete_grades)
        self.btn_edit_delete_grade.grid(row=5, column=2)

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

        self.grades_text.delete(1.0, tk.END)
        grades_list = [grade[1] for grade in grades]
        median_grade = median(grades_list)

        # Display grades
        self.grades_text.insert(tk.END, f"Grades for Student ID {student_id}:\n\n")
        for grade_id, grade, date, pdf_path in grades:
            pdf_name = os.path.basename(pdf_path)
            self.grades_text.insert(tk.END, f"Grade ID: {grade_id}, Grade: {grade}, Date: {date}, PDF: {pdf_name}\n")
        self.grades_text.insert(tk.END, f"\nMedian Grade: {median_grade:.2f}")

    def edit_or_delete_grades(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Error", "Please select a student.")
            return

        grade_id = simpledialog.askinteger("Edit/Delete Grade", "Enter the Grade ID:")
        if grade_id is None:
            return

        c.execute("SELECT grade, pdf_path FROM grades WHERE id = ? AND student_id = ?", (grade_id, student_id))
        record = c.fetchone()
        if record is None:
            messagebox.showerror("Error", "Grade ID not found for this student.")
            return

        action = messagebox.askquestion("Edit/Delete Grade", "Do you want to edit this grade?")
        if action == "yes":
            self.edit_grade(grade_id)
        else:
            self.delete_grade(grade_id)

    def edit_grade(self, grade_id):
        new_grade = simpledialog.askfloat("Edit Grade", "Enter the new grade:")
        if new_grade is None:
            return

        new_pdf_path = filedialog.askopenfilename(title="Select new PDF File (or cancel to keep existing)", filetypes=[("PDF Files", "*.pdf")])
        if not new_pdf_path:
            c.execute("UPDATE grades SET grade = ? WHERE id = ?", (new_grade, grade_id))
        else:
            c.execute("UPDATE grades SET grade = ?, pdf_path = ? WHERE id = ?", (new_grade, new_pdf_path, grade_id))
        conn.commit()
        messagebox.showinfo("Success", "Grade updated successfully.")

    def delete_grade(self, grade_id):
        confirm = messagebox.askyesno("Delete Grade", "Are you sure you want to delete this grade?")
        if confirm:
            c.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
            conn.commit()
            messagebox.showinfo("Deleted", "Grade deleted successfully.")

    def download_pdf(self):
        try:
            grade_id = simpledialog.askinteger("Download PDF", "Enter the Grade ID:")
            if grade_id is None:
                return

            c.execute("SELECT pdf_path FROM grades WHERE id = ?", (grade_id,))
            record = c.fetchone()
            if record is None:
                messagebox.showerror("Error", "Grade ID not found.")
                return

            pdf_path = record[0]
            if not os.path.exists(pdf_path):
                messagebox.showerror("Error", "PDF file not found.")
                return

            download_path = os.path.expanduser("~/Downloads")
            shutil.copy(pdf_path, download_path)
            messagebox.showinfo("Success", f"PDF downloaded to {download_path}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolRollApp(root)
    root.mainloop()