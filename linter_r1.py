import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import time

# Компилируем регулярные выражения для кэширования
comment_pattern = re.compile(r'^\s*//[a-zA-Z\s]*$')
empty_lines_pattern = re.compile(r'\n\s*\n+')
ignore_files_pattern = re.compile(r'scribble|gmlive|GMLive', re.IGNORECASE)

def remove_english_comments_and_trim_start(code):
    lines = code.split('\n')
    
    # Удаляем комментарии в начале кода, если они на английском
    while lines and comment_pattern.match(lines[0]):
        lines.pop(0)
    
    # Удаляем пустые строки в начале кода
    while lines and lines[0].strip() == '':
        lines.pop(0)
    
    return '\n'.join(lines)

def reduce_empty_lines(code):
    # Заменяем более одной пустой строки на одну
    return empty_lines_pattern.sub('\n\n', code)

def lint_gml_code(code):
    code = remove_english_comments_and_trim_start(code)
    code = reduce_empty_lines(code)
    return code

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    linted_code = lint_gml_code(code)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(linted_code)

    return file_path

def process_files_in_directory(directory, log_file):
    start_time = time.time()
    
    processed_files = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.gml') and not ignore_files_pattern.search(file):
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(process_file, file_path))
        
        for future in futures:
            processed_files.append(future.result())
            print(f'Processed {future.result()}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Linting process completed in {elapsed_time:.2f} seconds")

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Processed files:\n")
        for file_path in processed_files:
            log.write(f"{file_path}\n")

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_folder = folder_selected + "_linted"
        
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)
        shutil.copytree(folder_selected, destination_folder)
        
        script_directory = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(script_directory, "processed_files_log.txt")
        
        process_files_in_directory(destination_folder, log_file)
        
        messagebox.showinfo("Complete", f"Linting process is complete! Check the folder: {destination_folder} and the log file: {log_file}")

root = tk.Tk()
root.title("GML Linter")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Select a folder to lint GML files:")
label.pack(pady=5)

button = tk.Button(frame, text="Select Folder", command=select_folder)
button.pack(pady=5)

root.mainloop()