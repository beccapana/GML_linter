import tkinter as tk
from tkinter import filedialog
import re
import os

class GMLLinter:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def lint(self, code):
        self.errors = []
        self.warnings = []
        lines = code.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            line = self.fix_comma_spacing(line, i)
            line = self.fix_brackets_spacing(line, i)
            fixed_lines.append(line)
            self.check_line_length(line, i)
            self.check_indentation(line, i)
            self.check_trailing_spaces(line, i)
            self.check_uninitialized_variables(line, i)
            self.check_syntax(line, i)
        
        return self.errors, self.warnings, "\n".join(fixed_lines)

    def check_line_length(self, line, line_num):
        if len(line) > 80:
            self.warnings.append(f"Line {line_num + 1}: Line too long ({len(line)} characters)")
    
    def check_indentation(self, line, line_num):
        if '\t' in line:
            self.errors.append(f"Line {line_num + 1}: Tabs used for indentation")
        elif re.match(r' {1,3}| {5,}', line):
            self.errors.append(f"Line {line_num + 1}: Incorrect number of spaces used for indentation")
    
    def check_trailing_spaces(self, line, line_num):
        if line.rstrip() != line:
            self.warnings.append(f"Line {line_num + 1}: Trailing whitespace")
    
    def check_uninitialized_variables(self, line, line_num):
        if re.search(r'\bvar\b', line) and not re.search(r'=', line):
            self.errors.append(f"Line {line_num + 1}: Variable declared without initialization")

    def check_syntax(self, line, line_num):
        if re.search(r'\b(if|else|for|while|switch|case|break|continue|return)\b', line):
            if not re.search(r'\(', line) or not re.search(r'\)', line):
                self.errors.append(f"Line {line_num + 1}: Syntax error in control statement")
    
    def check_comma_spacing(self, line, line_num):
        if re.search(r',\S', line):
            self.errors.append(f"Line {line_num + 1}: Missing space after comma")
    
    def check_brackets_spacing(self, line, line_num):
        if re.search(r'\[\S', line):
            self.errors.append(f"Line {line_num + 1}: Missing space after '['")
        if re.search(r'\S\]', line):
            self.errors.append(f"Line {line_num + 1}: Missing space before ']'")
        if re.search(r'\{\S', line):
            self.errors.append(f"Line {line_num + 1}: Missing space after '{{'")
        if re.search(r'\S\}', line):
            self.errors.append(f"Line {line_num + 1}: Missing space before '}}'")

    def fix_comma_spacing(self, line, line_num):
        return re.sub(r',(\S)', r', \1', line)
    
    def fix_brackets_spacing(self, line, line_num):
        line = re.sub(r'\[\s*', '[ ', line)
        line = re.sub(r'\s*\]', ' ]', line)
        line = re.sub(r'\{\s*', '{ ', line)
        line = re.sub(r'\s*\}', ' }', line)
        return line

def open_file():
    filepath = filedialog.askopenfilename(filetypes=[("GML Files", "*.gml"), ("All Files", "*.*")])
    if filepath:
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                code = file.read()
        except UnicodeDecodeError:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Ошибка: не удалось декодировать файл. Попробуйте другой файл или измените его кодировку на UTF-8.")
            return
        
        linter = GMLLinter()
        errors, warnings, fixed_code = linter.lint(code)

        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Errors:\n")
        for error in errors:
            result_text.insert(tk.END, error + "\n")
        
        result_text.insert(tk.END, "\nWarnings:\n")
        for warning in warnings:
            result_text.insert(tk.END, warning + "\n")
        
        save_fixed_code(filepath, fixed_code)

def save_fixed_code(original_filepath, fixed_code):
    dir_path = os.path.dirname(original_filepath)
    base_name = os.path.basename(original_filepath)
    new_filepath = os.path.join(dir_path, f"fixed_{base_name}")

    with open(new_filepath, 'w') as file:
        file.write(fixed_code)

    result_text.insert(tk.END, f"\nFixed code saved to: {new_filepath}")

app = tk.Tk()
app.title("GML Linter")

open_button = tk.Button(app, text="Open GML File", command=open_file)
open_button.pack(pady=10)

result_text = tk.Text(app, wrap='word', height=20, width=80)
result_text.pack(pady=10)

app.mainloop()