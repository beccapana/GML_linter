import re
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def lint_gml_code(code):
    # Удаление отступов в самом начале кода
    code = code.lstrip()
    
    # Удаление комментариев в самом начале кода, если они на английском
    lines = code.split('\n')
    while lines and re.match(r'^\s*///?\s*[a-zA-Z]', lines[0]):
        lines.pop(0)
    
    # Удаление пустой строки между комментариями и кодом
    while lines and lines[0].strip() == '':
        lines.pop(0)
        
    code = '\n'.join(lines)
    
    # Добавление точек с запятыми после определённых конструкций
    code = re.sub(r'(\b(if|while|for|switch|with|repeat|else)\b[^{;]*\))\s*(?=\{)', r'\1;', code)
    
    # Добавление точек с запятыми в конце строк, если они не заканчиваются на ;, { или }
    code_lines = code.split('\n')
    inside_enum = False
    
    for i in range(len(code_lines)):
        line = code_lines[i]
        stripped_line = line.strip()
        
        if stripped_line.startswith('enum'):
            inside_enum = True
        
        if stripped_line.endswith('}'):
            inside_enum = False
        
        if stripped_line and not inside_enum:
            leading_whitespace = line[:len(line) - len(line.lstrip())]
            if stripped_line.startswith(';') or stripped_line.startswith('//') or stripped_line.startswith('#'):
                continue
            if re.search(r'\b(break|continue|return|else|case)\b', stripped_line):
                continue
            if stripped_line.startswith('enum') or stripped_line.startswith('function'):
                continue
            if stripped_line.endswith(',') or stripped_line.endswith(':'):
                continue
            if '++' in stripped_line:
                code_part = stripped_line.split('++')[0]
                if code_part.strip().endswith('++'):
                    continue
            if '--' in stripped_line:
                code_part = stripped_line.split('--')[0]
                if code_part.strip().endswith('--'):
                    continue
            if '//' in stripped_line:
                code_part, comment_part = stripped_line.split('//', 1)
                code_part = code_part.rstrip()
                if not (code_part.endswith(';') or code_part.endswith('{') or code_part.endswith('}') or code_part.endswith(');')):
                    code_part += ';'
                code_lines[i] = leading_whitespace + code_part + ' //' + comment_part
            else:
                if not (stripped_line.endswith(';') or stripped_line.endswith('{') or stripped_line.endswith('}') or stripped_line.endswith(');')):
                    code_lines[i] = leading_whitespace + stripped_line + ';'
    
    # Заменяем более одного пустого ряда на один пустой ряд
    code = '\n'.join(code_lines)
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
    
    # Исправление случаев с пустыми блоками после if
    code = re.sub(r'(\bif\b[^{;]*\));\s*{', r'\1 {', code)
    
    return code

def copy_directory_to_desktop(src_directory):
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    dst_directory = os.path.join(desktop_path, os.path.basename(src_directory) + "_copy")
    if os.path.exists(dst_directory):
        shutil.rmtree(dst_directory)
    shutil.copytree(src_directory, dst_directory)
    return dst_directory

def lint_gml_files_in_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".gml"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                linted_code = lint_gml_code(code)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(linted_code)
    
    messagebox.showinfo("Готово", "Все файлы GML обработаны и сохранены в своих исходных директориях!")

def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        dst_directory = copy_directory_to_desktop(directory)
        lint_gml_files_in_directory(dst_directory)

def create_gui():
    root = tk.Tk()
    root.title("GML Линтер")

    label = tk.Label(root, text="Выберите папку с файлами GML:")
    label.pack(pady=10)

    button = tk.Button(root, text="Выбрать папку", command=select_directory)
    button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()