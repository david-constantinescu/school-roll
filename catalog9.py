import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from statistics import median
from datetime import datetime
import sqlite3
import os
import shutil
from ttkbootstrap import Style
from ttkbootstrap import ttk

# Database setup
conn = sqlite3.connect('school_roll.db')
c = conn.cursor()

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
        self.root.title("Catalog Școlar")
        self.root.geometry("600x600")

        # Apply ttkbootstrap style
        style = Style(theme="flatly")  # Choose "flatly" for a light Apple-like theme
        rounded_button = "success.TButton"

        # Frames
        self.frame_top = tk.Frame(root)
        self.frame_top.pack(pady=10)

        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.pack(pady=10)

        # Elev List
        self.student_listbox = tk.Listbox(self.frame_top, width=30, height=10)
        self.student_listbox.grid(row=0, column=0, rowspan=5, padx=10)

        self.load_students()

        # Entry and buttons
        tk.Label(self.frame_top, text="Nume Elev:").grid(row=0, column=1, sticky="w")
        self.entry_name = tk.Entry(self.frame_top)
        self.entry_name.grid(row=0, column=2)

        self.btn_add_student = ttk.Button(self.frame_top, text="Adaugă Elev", command=self.add_student, style=rounded_button)
        self.btn_add_student.grid(row=1, column=2)

        self.btn_add_grade = ttk.Button(self.frame_top, text="Adaugă Notă", command=self.add_grade, style=rounded_button)
        self.btn_add_grade.grid(row=2, column=2)

        self.btn_view_grades = ttk.Button(self.frame_top, text="Vizualizează Note", command=self.view_grades, style=rounded_button)
        self.btn_view_grades.grid(row=3, column=2)

        self.btn_download_pdf = ttk.Button(self.frame_top, text="Descarcă PDF", command=self.download_pdf, style=rounded_button)
        self.btn_download_pdf.grid(row=4, column=2)

        self.btn_edit_delete_grade = ttk.Button(self.frame_top, text="Editează/Șterge Note", command=self.edit_or_delete_grades, style=rounded_button)
        self.btn_edit_delete_grade.grid(row=5, column=2)

        # New Grades/Test Button
        self.btn_grades_test = ttk.Button(self.frame_top, text="Note/Test", command=self.view_test_results, style=rounded_button)
        self.btn_grades_test.grid(row=6, column=2)

        # Elev Grades
        self.grades_text = tk.Text(self.frame_bottom, width=60, height=10)
        self.grades_text.pack()

    def load_students(self):
        """Load students from the database and display them in alphabetical order."""
        self.student_listbox.delete(0, tk.END)
        c.execute("SELECT * FROM students ORDER BY name ASC")  # Sorting by name in ascending order
        for student in c.fetchall():
            self.student_listbox.insert(tk.END, f"{student[0]}: {student[1]}")

    def add_student(self):
        name = self.entry_name.get().strip()
        if name:
            c.execute("INSERT INTO students (name) VALUES (?)", (name,))
            conn.commit()
            self.load_students()  # Reload students list and keep sorted
            self.entry_name.delete(0, tk.END)
        else:
            messagebox.showerror("Eroare", "Numele elevului nu poate fi gol.")

    def add_grade(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Eroare", "Selectați un elev.")
            return

        grade = simpledialog.askfloat("Notă", "Introduceți nota:")
        if grade is None:
            return  # User canceled

        date = datetime.now().strftime("%Y-%m-%d")
        pdf_path = filedialog.askopenfilename(title="Selectați fișierul PDF", filetypes=[("Fișiere PDF", "*.pdf")])
        if not pdf_path:
            messagebox.showerror("Eroare", "Trebuie să selectați un fișier PDF.")
            return

        c.execute("INSERT INTO grades (student_id, grade, date, pdf_path) VALUES (?, ?, ?, ?)",
                  (student_id, grade, date, pdf_path))
        conn.commit()
        messagebox.showinfo("Succes", "Nota a fost adăugată cu succes.")

    def view_grades(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Eroare", "Selectați un elev.")
            return

        c.execute("SELECT id, grade, date, pdf_path FROM grades WHERE student_id = ?", (student_id,))
        grades = c.fetchall()

        if not grades:
            messagebox.showinfo("Fără Note", "Nu există note pentru acest elev.")
            return

        self.grades_text.delete(1.0, tk.END)
        grades_list = [grade[1] for grade in grades]
        median_grade = median(grades_list)

        self.grades_text.insert(tk.END, f"Note pentru Elev ID {student_id}:\n\n")
        for grade_id, grade, date, pdf_path in grades:
            pdf_name = os.path.basename(pdf_path)
            self.grades_text.insert(tk.END, f"ID Notă: {grade_id}, Notă: {grade}, Dată: {date}, PDF: {pdf_name}\n")
        self.grades_text.insert(tk.END, f"\nMedia Notelor: {median_grade:.2f}")

    def view_test_results(self):
        pdf_path = filedialog.askopenfilename(title="Selectați fișierul PDF", filetypes=[("Fișiere PDF", "*.pdf")])
        if not pdf_path:
            messagebox.showerror("Eroare", "Nu ați selectat un fișier PDF.")
            return

        option = messagebox.askquestion("Opțiuni Vizualizare", "Doriți să vizualizați nota unui elev sau media?")
        
        if option == "yes":
            student_name = simpledialog.askstring("Nume Elev", "Introduceți numele elevului:")
            c.execute("SELECT id FROM students WHERE name = ?", (student_name,))
            result = c.fetchone()
            if result:
                student_id = result[0]
                c.execute("SELECT grade FROM grades WHERE student_id = ? AND pdf_path = ?", (student_id, pdf_path))
                grade = c.fetchone()
                if grade:
                    messagebox.showinfo("Notă", f"Nota elevului {student_name}: {grade[0]}")
                else:
                    messagebox.showinfo("Fără Notă", "Nu a fost găsită nicio notă pentru acest elev la testul selectat.")
            else:
                messagebox.showerror("Eroare", "Elevul nu a fost găsit.")
        else:
            c.execute("SELECT grade FROM grades WHERE pdf_path = ?", (pdf_path,))
            grades = [grade[0] for grade in c.fetchall()]
            if grades:
                test_median = median(grades)
                messagebox.showinfo("Media Notei", f"Media notelor pentru acest test este: {test_median}")
            else:
                messagebox.showinfo("Fără Note", "Nu există note înregistrate pentru acest test.")

    def edit_or_delete_grades(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Eroare", "Selectați un elev.")
            return

        grade_id = simpledialog.askinteger("Editează/Șterge Notă", "Introduceți ID-ul notei:")
        if grade_id is None:
            return

        c.execute("SELECT grade, pdf_path FROM grades WHERE id = ? AND student_id = ?", (grade_id, student_id))
        record = c.fetchone()
        if record is None:
            messagebox.showerror("Eroare", "ID-ul notei nu a fost găsit pentru acest elev.")
            return

        action = messagebox.askquestion("Editează/Șterge Notă", "Doriți să editați această notă?")
        if action == "yes":
            self.edit_grade(grade_id)
        else:
            self.delete_grade(grade_id)

    def edit_grade(self, grade_id):
        new_grade = simpledialog.askfloat("Editează Notă", "Introduceți noua notă:")
        if new_grade is None:
            return

        new_pdf_path = filedialog.askopenfilename(title="Selectați fișierul PDF nou (sau anulați pentru a păstra fișierul existent)", filetypes=[("Fișiere PDF", "*.pdf")])
        if not new_pdf_path:
            c.execute("UPDATE grades SET grade = ? WHERE id = ?", (new_grade, grade_id))
        else:
            c.execute("UPDATE grades SET grade = ?, pdf_path = ? WHERE id = ?", (new_grade, new_pdf_path, grade_id))
        conn.commit()
        messagebox.showinfo("Succes", "Notă actualizată cu succes.")

    def delete_grade(self, grade_id):
        confirm = messagebox.askyesno("Șterge Notă", "Sunteți sigur că doriți să ștergeți această notă?")
        if confirm:
            c.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
            conn.commit()
            messagebox.showinfo("Șters", "Notă ștearsă cu succes.")

    def download_pdf(self):
        try:
            student_id = int(self.student_listbox.get(tk.ACTIVE).split(":")[0])
        except IndexError:
            messagebox.showerror("Eroare", "Selectați un elev.")
            return

        c.execute("SELECT pdf_path FROM grades WHERE student_id = ?", (student_id,))
        pdfs = c.fetchall()
        if not pdfs:
            messagebox.showinfo("Fără PDF-uri", "Nu există PDF-uri disponibile pentru acest elev.")
            return

        dest_folder = filedialog.askdirectory(title="Selectați dosarul de destinație")
        if not dest_folder:
            return

        for pdf_path, in pdfs:
            shutil.copy(pdf_path, dest_folder)
        messagebox.showinfo("Succes", "PDF-urile au fost descărcate cu succes.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolRollApp(root)
    root.mainloop()