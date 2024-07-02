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
    while lines and re.match(r'^\s*//\s*[a-zA-Z]', lines[0]):
        lines.pop(0)
    code = '\n'.join(lines)
    
    # Добавление точек с запятыми после определённых конструкций
    code = re.sub(r'(\b(if|while|for|switch|with|repeat|else)\b[^{;]*\))\s*(?=\{)', r'\1;', code)
    
    # Добавление точек с запятыми в конце строк, если они не заканчиваются на ;, { или }
    code_lines = code.split('\n')
    for i in range(len(code_lines)):
        line = code_lines[i].strip()
        if line:
            if '//' in line:
                code_part, comment_part = line.split('//', 1)
                code_part = code_part.rstrip()
                if not (code_part.endswith(';') or code_part.endswith('{') or code_part.endswith('}') or code_part.endswith(');')):
                    code_part += ';'
                code_lines[i] = code_part + ' //' + comment_part
            else:
                if not (line.endswith(';') or line.endswith('{') or line.endswith('}') or line.endswith(');')):
                    code_lines[i] += ';'
    
    # Заменяем более одного пустого ряда на один пустой ряд
    code = '\n'.join(code_lines)
    code = re.sub(r'\n\s*\n', '\n', code)
    
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
    linted_directory = os.path.join(directory, "linted_files")
    os.makedirs(linted_directory, exist_ok=True)

    for root, _, files in os.walk(directory):
        if 'linted_files' in root:
            continue
        for file in files:
            if file.endswith(".gml"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                linted_code = lint_gml_code(code)
                relative_path = os.path.relpath(root, directory)
                linted_file_directory = os.path.join(linted_directory, relative_path)
                os.makedirs(linted_file_directory, exist_ok=True)
                linted_file_path = os.path.join(linted_file_directory, file)
                with open(linted_file_path, 'w', encoding='utf-8') as f:
                    f.write(linted_code)
    
    messagebox.showinfo("Готово", "Все файлы GML обработаны и сохранены в новой папке на рабочем столе!")

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
