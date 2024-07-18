import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def remove_english_comments_and_trim_start(code):
    lines = code.split('\n')
    
    # Удаляем комментарии в начале кода, если они на английском
    while lines and re.match(r'^\s*//[a-zA-Z\s]*$', lines[0]):
        lines.pop(0)
    
    # Удаляем пустые строки в начале кода
    while lines and lines[0].strip() == '':
        lines.pop(0)
    
    return '\n'.join(lines)

def reduce_empty_lines(code):
    # Заменяем более одной пустой строки на одну
    return re.sub(r'\n\s*\n+', '\n\n', code)

def lint_gml_code(code):
    code = remove_english_comments_and_trim_start(code)
    code = reduce_empty_lines(code)
    return code

def process_files_in_directory(directory, log_file):
    processed_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.gml') and not re.search(r'scribble|gmlive|GMLive', file, re.IGNORECASE):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                linted_code = lint_gml_code(code)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(linted_code)
                
                processed_files.append(file_path)
                print(f'Processed {file_path}')
    
    # Записываем список обработанных файлов в лог файл
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Processed files:\n")
        for file_path in processed_files:
            log.write(f"{file_path}\n")

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_folder = folder_selected + "_linted"
        
        # Копируем выбранную папку в новую директорию
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)
        shutil.copytree(folder_selected, destination_folder)
        
        # Путь к лог-файлу в директории линтера
        script_directory = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(script_directory, "processed_files_log.txt")
        
        # Обрабатываем файлы в новой директории
        process_files_in_directory(destination_folder, log_file)
        
        messagebox.showinfo("Complete", f"Linting process is complete! Check the folder: {destination_folder} and the log file: {log_file}")

# Создание UI
root = tk.Tk()
root.title("GML Linter")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Select a folder to lint GML files:")
label.pack(pady=5)

button = tk.Button(frame, text="Select Folder", command=select_folder)
button.pack(pady=5)

root.mainloop()