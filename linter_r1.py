import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import time
import threading
from tkinter import ttk
import queue

# Компилируем регулярные выражения для кэширования
comment_pattern = re.compile(r'^\s*//[a-zA-Z\s]*$')
empty_lines_pattern = re.compile(r'\n\s*\n+')
ignore_files_pattern = re.compile(r'scribble|gmlive|GMLive', re.IGNORECASE)

def remove_english_comments_and_trim_start(code):
    lines = code.split('\n')
    
    while lines and comment_pattern.match(lines[0]):
        lines.pop(0)
    
    while lines and lines[0].strip() == '':
        lines.pop(0)
    
    return '\n'.join(lines)

def reduce_empty_lines(code):
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

def process_files_in_directory(directory, log_file, progress_queue):
    start_time = time.time()
    
    processed_files = []
    total_files = 0
    current_file = 0

    # Подсчёт общего количества файлов
    for _, _, files in os.walk(directory):
        total_files += len([file for file in files if file.endswith('.gml') and not ignore_files_pattern.search(file)])
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.gml') and not ignore_files_pattern.search(file):
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(process_file, file_path))
        
        for future in futures:
            result = future.result()
            processed_files.append(result)
            current_file += 1
            # Публикуем обновление в очередь
            if current_file % 10 == 0:
                progress_queue.put((current_file, total_files))
            print(f'Processed {result}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Linting process completed in {elapsed_time:.2f} seconds")

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Processed files:\n")
        for file_path in processed_files:
            log.write(f"{file_path}\n")

    # Сигнализируем завершение
    progress_queue.put((total_files, total_files))

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        progress_queue = queue.Queue()
        threading.Thread(target=lambda: _process_selected_folder(folder_selected, progress_queue)).start()
        threading.Thread(target=lambda: update_progress_bar(progress_queue)).start()

def _process_selected_folder(folder_selected, progress_queue):
    destination_folder = folder_selected + "_linted"
    
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    shutil.copytree(folder_selected, destination_folder)
    
    script_directory = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_directory, "processed_files_log.txt")
    
    process_files_in_directory(destination_folder, log_file, progress_queue)
    
    messagebox.showinfo("Complete", f"Linting process is complete! Check the folder: {destination_folder} and the log file: {log_file}")

def update_progress_bar(progress_queue):
    while True:
        try:
            current, total = progress_queue.get_nowait()
            progress_var.set((current / total) * 100)
            root.update_idletasks()
            if current >= total:
                break
        except queue.Empty:
            time.sleep(0.1)  # Немного задержки для предотвращения загрузки CPU

root = tk.Tk()
root.title("GML Linter")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Select a folder to lint GML files:")
label.pack(pady=5)

button = tk.Button(frame, text="Select Folder", command=select_folder)
button.pack(pady=5)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
progress_bar.pack(pady=5, fill=tk.X)

root.mainloop()