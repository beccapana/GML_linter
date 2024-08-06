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
comment_pattern = re.compile(r'^\s*//[/@\w\s]*$')
empty_lines_pattern = re.compile(r'\n\s*\n+')

ignore_files_pattern = re.compile(r'scribble|gmlive|fmod', re.IGNORECASE)

def update_ignore_files_pattern():
    global ignore_files_pattern
    patterns = []
    if scribble_var.get():
        patterns.append('scribble')
    if gmlive_var.get():
        patterns.append('gmlive')
    if fmod_var.get():
        patterns.append('fmod')
    
    if patterns:
        ignore_files_pattern = re.compile('|'.join(patterns), re.IGNORECASE)
    else:
        ignore_files_pattern = re.compile(r'$^')  # Паттерн, который никогда не совпадет

def remove_english_comments_and_trim_start(code):
    lines = code.split('\n')
    comment_block_started = False
    
    while lines:
        line = lines[0]
        if comment_pattern.match(line):
            comment_block_started = True
            lines.pop(0)
        elif comment_block_started and line.strip() == '':
            lines.pop(0)
        else:
            break
    
    while lines and lines[0].strip() == '':
        lines.pop(0)
    
    return '\n'.join(lines)

def reduce_empty_lines(code):
    return empty_lines_pattern.sub('\n\n', code)

def lint_gml_code(code):
    code = remove_english_comments_and_trim_start(code)
    code = reduce_empty_lines(code)
    return code

def process_file(file_path, log_queue):
    log_queue.put(f'Processing file: {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    linted_code = lint_gml_code(code)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(linted_code)

    log_queue.put(f'Processed file: {file_path}')
    return file_path

def should_ignore_file(file):
    return ignore_files_pattern.search(file)

def process_files_in_directory(directory, log_file, progress_queue, log_queue):
    start_time = time.time()
    
    processed_files = []
    total_files = 0
    current_file = 0

    # Подсчёт общего количества файлов
    for _, _, files in os.walk(directory):
        total_files += len([file for file in files if file.endswith('.gml') and not should_ignore_file(file)])
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.gml') and not should_ignore_file(file):
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(process_file, file_path, log_queue))
        
        for future in futures:
            result = future.result()
            processed_files.append(result)
            current_file += 1
            # Публикуем обновление в очередь
            if current_file % 10 == 0:
                progress_queue.put((current_file, total_files))
            log_queue.put(f'Processed {result}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    log_queue.put(f"Linting process completed in {elapsed_time:.2f} seconds")

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Processed files:\n")
        for file_path in processed_files:
            log.write(f"{file_path}\n")

    # Сигнализируем завершение
    progress_queue.put((total_files, total_files))

def process_individual_files(files, log_file, progress_queue, log_queue):
    start_time = time.time()
    
    processed_files = []
    total_files = len(files)
    current_file = 0

    with ThreadPoolExecutor() as executor:
        futures = []
        for file_path in files:
            futures.append(executor.submit(process_file, file_path, log_queue))
        
        for future in futures:
            result = future.result()
            processed_files.append(result)
            current_file += 1
            # Публикуем обновление в очередь
            if current_file % 1 == 0:  # Обновляем прогресс на каждый файл
                progress_queue.put((current_file, total_files))
            log_queue.put(f'Processed {result}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    log_queue.put(f"Linting process completed in {elapsed_time:.2f} seconds")

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
        log_queue = queue.Queue()
        threading.Thread(target=lambda: _process_selected_folder(folder_selected, progress_queue, log_queue)).start()
        threading.Thread(target=lambda: update_progress_bar(progress_queue)).start()
        threading.Thread(target=lambda: update_log(log_queue)).start()

def select_files():
    files_selected = filedialog.askopenfilenames(filetypes=[("GML files", "*.gml")])
    if files_selected:
        progress_queue = queue.Queue()
        log_queue = queue.Queue()
        threading.Thread(target=lambda: _process_selected_files(files_selected, progress_queue, log_queue)).start()
        threading.Thread(target=lambda: update_progress_bar(progress_queue)).start()
        threading.Thread(target=lambda: update_log(log_queue)).start()

def _process_selected_folder(folder_selected, progress_queue, log_queue):
    destination_folder = os.path.join(os.path.expanduser("~"), "Desktop", os.path.basename(folder_selected) + "_linted")
    
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    shutil.copytree(folder_selected, destination_folder)
    
    script_directory = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_directory, "processed_files_log.txt")
    
    process_files_in_directory(destination_folder, log_file, progress_queue, log_queue)
    
    messagebox.showinfo("Complete", f"Linting process is complete! Check the folder: {destination_folder} and the log file: {log_file}")

def _process_selected_files(files_selected, progress_queue, log_queue):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_directory, "processed_files_log.txt")
    
    process_individual_files(files_selected, log_file, progress_queue, log_queue)
    
    messagebox.showinfo("Complete", f"Linting process is complete! Check the log file: {log_file}")

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

def update_log(log_queue):
    while True:
        try:
            message = log_queue.get_nowait()
            log_text.insert(tk.END, message + '\n')
            log_text.yview(tk.END)
            root.update_idletasks()
        except queue.Empty:
            time.sleep(0.1)  # Немного задержки для предотвращения загрузки CPU

root = tk.Tk()
root.title("GML Linter")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Select a folder or files to lint GML files:")
label.pack(pady=5)

button_folder = tk.Button(frame, text="Select Folder", command=select_folder)
button_folder.pack(pady=5)

button_files = tk.Button(frame, text="Select Files", command=select_files)
button_files.pack(pady=5)

scribble_var = tk.BooleanVar(value=True)
gmlive_var = tk.BooleanVar(value=True)
fmod_var = tk.BooleanVar(value=True)

check_scribble = tk.Checkbutton(frame, text="Ignore scribble", variable=scribble_var, command=update_ignore_files_pattern)
check_scribble.pack(anchor=tk.W)
check_gmlive = tk.Checkbutton(frame, text="Ignore gmlive", variable=gmlive_var, command=update_ignore_files_pattern)
check_gmlive.pack(anchor=tk.W)
check_fmod = tk.Checkbutton(frame, text="Ignore fmod", variable=fmod_var, command=update_ignore_files_pattern)
check_fmod.pack(anchor=tk.W)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
progress_bar.pack(pady=5, fill=tk.X)

log_text = tk.Text(frame, height=15, width=80, wrap=tk.WORD)
log_text.pack(pady=5)

root.mainloop()