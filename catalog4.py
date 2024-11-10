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
        self.root.geometry("600x600")

        # Frames
        self.frame_top = tk.Frame(root)
        self.frame_top.pack(pady=10)

        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.pack(pady=10)

        # Student List
        self.student_listbox = tk.Listbox(self.frame_top, width=30, height=10)
        self.student_listbox.grid(row=0, column=0, rowspan=6, padx=10)

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

        self.btn_download_pdf = tk.Button(self.frame_top, text="Download PDF", command=self.download_pdf)
        self.btn_download_pdf.grid(row=4, column=2)

        self.btn_edit_delete_grade = tk.Button(self.frame_top, text="Edit/Delete Grades", command=self.edit_or_delete_grades)
        self.btn_edit_delete_grade.grid(row=5, column=2)

        # New Grades/Test button
        self.btn_grades_test = tk.Button(self.frame_top, text="Grades/Test", command=self.grades_test)
        self.btn_grades_test.grid(row=6, column=2)

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
                # Choose the Downloads directory as the destination
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

        c.execute("SELECT id, grade, date, pdf_path FROM grades WHERE student_id = ?", (student_id,))
        grades = c.fetchall()

        if not grades:
            messagebox.showinfo("No Grades", "No grades available for this student.")
            return

        grade_choices = [f"Grade ID: {grade[0]}, Grade: {grade[1]}, Date: {grade[2]}, PDF: {os.path.basename(grade[3])}" for grade in grades]
        grade_choice = simpledialog.askstring("Select Grade", "Choose a grade to edit/delete:\n" + "\n".join(grade_choices))

        if not grade_choice:
            return

        # Edit or delete
        action = messagebox.askquestion("Edit/Delete", "Do you want to edit or delete this grade?")
        if action == "yes":
            new_grade = simpledialog.askfloat("Edit Grade", "Enter new grade:")
            if new_grade is not None:
                c.execute("UPDATE grades SET grade = ? WHERE id = ?", (new_grade, grades[grade_choices.index(grade_choice)][0]))
                conn.commit()
                messagebox.showinfo("Success", "Grade updated.")
        else:
            c.execute("DELETE FROM grades WHERE id = ?", (grades[grade_choices.index(grade_choice)][0],))
            conn.commit()
            messagebox.showinfo("Success", "Grade deleted.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolRollApp(root)
    root.mainloop()