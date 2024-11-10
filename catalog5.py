import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import sqlite3
import os
from datetime import datetime
from statistics import median
import shutil

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
        self.root.geometry("800x600")

        # Top frame for search bar and student list (left) and buttons (right)
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left frame for search and student list
        self.left_frame = tk.Frame(self.top_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(self.left_frame, text="Search Student:").pack(anchor="w")
        self.search_entry = tk.Entry(self.left_frame)
        self.search_entry.pack(fill=tk.X, padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self.search_student)

        self.student_listbox = tk.Listbox(self.left_frame)
        self.student_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.load_students()

        # Right frame for function buttons
        self.right_frame = tk.Frame(self.top_frame)
        self.right_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=5, pady=5)

        self.entry_name = tk.Entry(self.right_frame)
        self.entry_name.pack(fill=tk.X, padx=5, pady=5)
        self.btn_add_student = tk.Button(self.right_frame, text="Add Student", command=self.add_student)
        self.btn_add_student.pack(fill=tk.X, padx=5, pady=5)

        self.btn_add_grade = tk.Button(self.right_frame, text="Add Grade", command=self.add_grade)
        self.btn_add_grade.pack(fill=tk.X, padx=5, pady=5)

        self.btn_view_grades = tk.Button(self.right_frame, text="View Grades", command=self.view_grades)
        self.btn_view_grades.pack(fill=tk.X, padx=5, pady=5)

        self.btn_download_pdf = tk.Button(self.right_frame, text="Download PDF", command=self.download_pdf)
        self.btn_download_pdf.pack(fill=tk.X, padx=5, pady=5)

        self.btn_edit_delete_grade = tk.Button(self.right_frame, text="Edit/Delete Grades", command=self.edit_or_delete_grades)
        self.btn_edit_delete_grade.pack(fill=tk.X, padx=5, pady=5)

        self.btn_grades_test = tk.Button(self.right_frame, text="Grades/Test", command=self.grades_test)
        self.btn_grades_test.pack(fill=tk.X, padx=5, pady=5)

        # Bottom frame for grades display
        self.grades_text = tk.Text(root)
        self.grades_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def load_students(self):
        self.student_listbox.delete(0, tk.END)
        c.execute("SELECT * FROM students")
        for student in c.fetchall():
            self.student_listbox.insert(tk.END, f"{student[0]}: {student[1]}")

    def search_student(self, event):
        query = self.search_entry.get().strip().lower()
        self.student_listbox.delete(0, tk.END)
        c.execute("SELECT * FROM students WHERE LOWER(name) LIKE ?", (f"%{query}%",))
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
        median_grade = round(median(grades_list))

        # Display grades
        self.grades_text.insert(tk.END, f"Grades for Student ID {student_id}:\n\n")
        for grade_id, grade, date, pdf_path in grades:
            pdf_name = os.path.basename(pdf_path)
            self.grades_text.insert(tk.END, f"Grade ID: {grade_id}, Grade: {grade}, Date: {date}, PDF: {pdf_name}\n")
        self.grades_text.insert(tk.END, f"\nMedian Grade: {median_grade}")

    def download_pdf(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Error", "Please select a student.")
            return

        c.execute("SELECT pdf_path FROM grades WHERE student_id = ?", (student_id,))
        record = c.fetchone()

        if record:
            pdf_path = record[0]
            if os.path.exists(pdf_path):
                downloads_dir = os.path.expanduser('~/Downloads')
                destination = os.path.join(downloads_dir, os.path.basename(pdf_path))
                shutil.copy(pdf_path, destination)  # Copy the PDF to Downloads
                messagebox.showinfo("Success", f"PDF downloaded to {destination}")
            else:
                messagebox.showerror("Error", "PDF file not found.")
        else:
            messagebox.showinfo("Error", "No PDF associated with this student.")

    def grades_test(self):
        pdf_path = filedialog.askopenfilename(title="Select Test PDF", filetypes=[("PDF Files", "*.pdf")])
        if not pdf_path:
            messagebox.showerror("Error", "You must select a PDF file.")
            return

        choice = messagebox.askquestion("Grades/Test", "Do you want to see a specific student's grade for this test?")
        if choice == "yes":
            student_id = simpledialog.askinteger("Student ID", "Enter the Student ID:")
            if student_id is None:
                return

            c.execute("SELECT grade FROM grades WHERE student_id = ? AND pdf_path = ?", (student_id, pdf_path))
            record = c.fetchone()
            if record:
                grade = record[0]
                messagebox.showinfo("Grade", f"Student ID {student_id} received a grade of {grade} on this test.")
            else:
                messagebox.showinfo("Not Found", f"No grade found for Student ID {student_id} on this test.")

        else:
            c.execute("SELECT grade FROM grades WHERE pdf_path = ?", (pdf_path,))
            grades = [record[0] for record in c.fetchall()]
            if grades:
                median_grade = round(median(grades))
                messagebox.showinfo("Median Grade", f"The median grade for this test is {median_grade}.")
            else:
                messagebox.showinfo("No Grades", "No grades found for this test.")

    def edit_or_delete_grades(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Error", "Please select a student.")
            return

        c.execute("SELECT id, grade, pdf_path FROM grades WHERE student_id = ?", (student_id,))
        grades = c.fetchall()
        if not grades:
            messagebox.showinfo("No Grades", "This student has no grades.")
            return

        grade_choices = [f"ID: {grade[0]}, Grade: {grade[1]}, PDF: {os.path.basename(grade[2])}" for grade in grades]
        grade_choice = simpledialog.askstring("Edit/Delete Grade", "Select a grade to edit or delete:\n" + "\n".join(grade_choices))

        if not grade_choice:
            return

        selected_grade_id = int(grade_choice.split(",")[0].split(":")[1].strip())

        action = messagebox.askquestion("Edit or Delete", "Would you like to edit this grade?", icon="question")

        if action == "yes":
            new_grade = simpledialog.askfloat("New Grade", "Enter the new grade:")
            if new_grade is not None:
                c.execute("UPDATE grades SET grade = ? WHERE id = ?", (new_grade, selected_grade_id))
                conn.commit()
                messagebox.showinfo("Success", "Grade updated.")
                self.view_grades()  # Refresh the grades display
        else:
            c.execute("DELETE FROM grades WHERE id = ?", (selected_grade_id,))
            conn.commit()
            messagebox.showinfo("Success", "Grade deleted.")
            self.view_grades()  # Refresh the grades display

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolRollApp(root)
    root.mainloop()