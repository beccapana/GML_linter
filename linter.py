import re
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import time
import threading

# Компиляция регулярных выражений для повторного использования
enum_regex = re.compile(r',\s*(\})')
if_while_for_regex = re.compile(r'(\b(if|while|for|switch|with|repeat|else|do)\b[^{;]*\))\s*(?=\{)')
special_line_regex = re.compile(r'^\s*///?\s*[a-zA-Z]')
block_start_regex = re.compile(r'\b(function|if|while|for|switch|with|repeat)\b')
block_function_call_regex = re.compile(r'\b\w+\s*=\s*\w+\s*\([^;{]+\)\s*{')
comment_regex = re.compile(r'\b(break|continue|return|else|case)\b')

def lint_gml_code(code):
    code = code.lstrip()
    
    lines = code.split('\n')
    while lines and special_line_regex.match(lines[0]):
        lines.pop(0)
    
    while lines and lines[0].strip() == '':
        lines.pop(0)
    
    code = '\n'.join(lines)
    
    code = if_while_for_regex.sub(r'\1', code)
    
    code_lines = code.split('\n')
    inside_enum = False
    enum_lines = []
    enum_start = -1
    inside_block = 0

    i = 0
    while i < len(code_lines):
        line = code_lines[i]
        stripped_line = line.strip()
        
        if stripped_line.startswith('enum'):
            inside_enum = True
            enum_start = i
            enum_lines = [line]
            i += 1
            continue

        if inside_enum:
            enum_lines.append(line)
            if stripped_line.endswith('}'):
                inside_enum = False
                enum_code = '\n'.join(enum_lines)
                enum_code = enum_regex.sub(r'\1', enum_code)
                code_lines[enum_start:i+1] = enum_code.split('\n')
            i += 1
            continue
        
        if stripped_line and not inside_enum:
            leading_whitespace = line[:len(line) - len(line.lstrip())]
            
            if stripped_line.startswith(';') or stripped_line.startswith('//') or stripped_line.startswith('#'):
                i += 1
                continue
            
            if comment_regex.search(stripped_line):
                i += 1
                continue
            
            if stripped_line.startswith('enum') or stripped_line.startswith('function'):
                i += 1
                continue
            
            if stripped_line.endswith(',') or stripped_line.endswith(':'):
                i += 1
                continue
            
            if stripped_line.endswith('{') and block_start_regex.search(stripped_line):
                inside_block += 1
                i += 1
                continue
            
            if stripped_line.endswith('}'):
                inside_block -= 1
                i += 1
                continue
            
            if block_function_call_regex.search(stripped_line):
                i += 1
                continue
            
            if '++' in stripped_line or '--' in stripped_line:
                code_part = stripped_line.split('++' if '++' in stripped_line else '--')[0]
                if code_part.strip().endswith(('++', '--')):
                    i += 1
                    continue
            
            if '//' in stripped_line:
                code_part, comment_part = stripped_line.split('//', 1)
                code_part = code_part.rstrip()
                if not (code_part.endswith(';') or code_part.endswith('{') or code_part.endswith('}') or code_part.endswith(');')):
                    code_part += ';'
                code_lines[i] = leading_whitespace + code_part + ' //' + comment_part
            else:
                if not (stripped_line.endswith(';') or stripped_line.endswith('{') or stripped_line.endswith('}') or stripped_line.endswith(');') or stripped_line.endswith(':')):
                    if i + 1 < len(code_lines) and code_lines[i + 1].strip().startswith('{'):
                        i += 1
                        continue
                    if not (stripped_line.endswith('[') or stripped_line.endswith(']')):
                        code_lines[i] = leading_whitespace + stripped_line + ';'
        i += 1
    
    code = '\n'.join(code_lines)
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
    
    code = re.sub(r'(\bif\b[^{;]*\));\s*{', r'\1 {', code)
    
    return code

def copy_directory_to_desktop(src_directory):
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    dst_directory = os.path.join(desktop_path, os.path.basename(src_directory) + "_copy")
    if os.path.exists(dst_directory):
        shutil.rmtree(dst_directory)
    shutil.copytree(src_directory, dst_directory)
    return dst_directory

def process_gml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    linted_code = lint_gml_code(code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(linted_code)
    return file_path

def lint_gml_files_in_directory(directory, include_special_files):
    linted_files = []
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        futures = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".gml"):
                    if not include_special_files and any(ignore in file.lower() for ignore in ["scribble", "gmlive"]):
                        continue
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(process_gml_file, file_path))
        for future in futures:
            linted_files.append(future.result())
    
    end_time = time.time()
    linting_duration = end_time - start_time

    linted_files_path = os.path.join(directory, 'linted_files.txt')
    with open(linted_files_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linted_files))
    
    messagebox.showinfo("Готово", f"Все файлы GML обработаны и сохранены в своих исходных директориях!\nВремя обработки: {linting_duration:.2f} секунд.")

def lint_gml_file(file_path):
    start_time = time.time()
    linted_file_path = process_gml_file(file_path)
    end_time = time.time()
    linting_duration = end_time - start_time
    messagebox.showinfo("Готово", f"Файл {os.path.basename(file_path)} обработан и сохранен как {os.path.basename(linted_file_path)}!\nВремя обработки: {linting_duration:.2f} секунд.")

def select_directory(include_special_files):
    directory = filedialog.askdirectory()
    if directory:
        threading.Thread(target=lambda: _select_directory(directory, include_special_files)).start()

def _select_directory(directory, include_special_files):
    dst_directory = copy_directory_to_desktop(directory)
    lint_gml_files_in_directory(dst_directory, include_special_files)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("GML files", "*.gml")])
    if file_path:
        threading.Thread(target=lambda: lint_gml_file(file_path)).start()

def create_gui():
    root = tk.Tk()
    root.title("GML Линтер")

    label = tk.Label(root, text="Выберите папку или файл с GML кодом:")
    label.pack(pady=10)

    include_special_files_var = tk.BooleanVar()
    checkbox = tk.Checkbutton(root, text="Обрабатывать файлы со строками 'scribble', 'gmlive' и 'GMLive' в названии", variable=include_special_files_var)
    checkbox.pack(pady=5)

    button_dir = tk.Button(root, text="Выбрать папку", command=lambda: select_directory(include_special_files_var.get()))
    button_dir.pack(pady=5)

    button_file = tk.Button(root, text="Выбрать файл", command=select_file)
    button_file.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()