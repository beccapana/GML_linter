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
specific_comments_pattern = re.compile(
    r'^\s*//\s*/?\s*@?\s*d\s*e\s*s\s*c\s*r\s*i\s*p\s*t\s*i\s*o\s*n\s*I\s*n\s*s\s*e\s*r\s*t\s*d\s*e\s*s\s*c\s*r\s*i\s*p\s*t\s*i\s*o\s*n\s*h\s*e\s*r\s*e\s*$|'
    r'^\s*//?\s*Y\s*o\s*u\s*c\s*a\s*n\s*w\s*r\s*i\s*t\s*e\s*y\s*o\s*u\s*r\s*c\s*o\s*d\s*e\s*i\s*n\s*t\s*h\s*i\s*s\s*e\s*d\s*i\s*t\s*o\s*r\s*$|'
    r'^\s*//?\s*В\s*ы\s*м\s*о\s*ж\s*е\s*т\s*е\s*з\s*а\s*п\s*и\s*с\s*а\s*т\s*ь\s*с\s*в\s*о\s*й\s*к\s*о\s*д\s*в\s*э\s*т\s*о\s*м\s*р\s*е\s*д\s*а\s*к\s*т\s*о\s*р\s*е\s*$|'
    r'^\s*//\s*/?\s*@?\s*d\s*e\s*s\s*c\s*r\s*i\s*p\s*t\s*i\s*o\s*n\s*В\s*с\s*т\s*а\s*в\s*ь\s*т\s*е\s*о\s*п\s*и\s*с\s*а\s*н\s*и\s*е\s*з\s*д\s*е\s*с\s*ь\s*$|'
    r'^\s*//?\s*i\s*t\s*t\s*h\s*e\s*p\s*a\s*r\s*e\s*n\s*t\s*e\s*v\s*e\s*n\s*t\s*$|'
    r'^\s*//\s*/?\s*@?\s*d\s*e\s*s\s*c\s*r\s*i\s*p\s*t\s*i\s*o\s*n\s*A\s*n\s*e\s*x\s*a\s*m\s*p\s*l\s*e\s*$',
    re.IGNORECASE | re.VERBOSE)

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

def remove_specific_comments(code):
    lines = code.split('\n')
    filtered_lines = [line for line in lines if not specific_comments_pattern.match(line)]
    return '\n'.join(filtered_lines)

def reduce_empty_lines(code):
    empty_lines_pattern = re.compile(r'\n\s*\n+')
    code = empty_lines_pattern.sub('\n\n', code)
    if code.endswith('\n'):
        code = code.rstrip('\n')
    return code

def lint_gml_code(code):
    code = remove_specific_comments(code)
    code = reduce_empty_lines(code)
    return code

def is_potentially_unwanted_file(code):
    lines = code.split('\n')
    for line in lines:
        # Игнорируем строки, которые содержат только комментарии или пробелы
        if line.strip() and not line.strip().startswith('//'):
            return False
    return True

def process_file(file_path, log_queue):
    log_queue.put(f'Processing file: {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    linted_code = lint_gml_code(code)
    
    if linted_code.strip() == '' or linted_code.strip() == 'event_inherited();':
        os.remove(file_path)
        log_queue.put(f'Deleted file: {file_path}')
        return []  # Не возвращаем удаленные файлы
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(linted_code)
        log_queue.put(f'Processed file: {file_path}')
        
        # Добавляем в потенциально нежелательные файлы только если они содержат только комментарии
        if is_potentially_unwanted_file(linted_code):
            return [file_path]
        return []

def should_ignore_file(file):
    return ignore_files_pattern.search(file)

def process_files_in_directory(directory, log_file, progress_queue, log_queue):
    start_time = time.time()
    
    processed_files = []
    total_files = 0
    current_file = 0
    potential_unwanted_files = []

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
            potential_unwanted_files.extend(result)
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
    
    # Если есть потенциально нежелательные файлы, показываем алерт
    if potential_unwanted_files:
        show_potential_unwanted_files_alert(potential_unwanted_files)

    # Сигнализируем завершение
    progress_queue.put((total_files, total_files))

def process_individual_files(files, log_file, progress_queue, log_queue):
    start_time = time.time()
    
    processed_files = []
    total_files = len(files)
    current_file = 0
    potential_unwanted_files = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for file_path in files:
            futures.append(executor.submit(process_file, file_path, log_queue))
        
        for future in futures:
            result = future.result()
            processed_files.append(result)
            current_file += 1
            potential_unwanted_files.extend(result)
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
    
    # Если есть потенциально нежелательные файлы, показываем алерт
    if potential_unwanted_files:
        show_potential_unwanted_files_alert(potential_unwanted_files)

    # Сигнализируем завершение
    progress_queue.put((total_files, total_files))

def show_potential_unwanted_files_alert(potential_unwanted_files):
    alert_window = tk.Toplevel(root)
    alert_window.title("Potentially Unwanted Files")

    label = tk.Label(alert_window, text="The following files contain only comments and might be unwanted:")
    label.pack(pady=5)

    listbox = tk.Listbox(alert_window, height=15, width=80)
    for file_path in potential_unwanted_files:
        listbox.insert(tk.END, file_path)
    listbox.pack(pady=5)

    scrollbar = tk.Scrollbar(alert_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    def on_double_click(event):
        selected_file = listbox.get(listbox.curselection())
        open_file(selected_file)

    listbox.bind("<Double-1>", on_double_click)

    ok_button = tk.Button(alert_window, text="OK", command=alert_window.destroy)
    ok_button.pack(pady=5)

def open_file(file_path):
    if os.path.exists(file_path):
        os.startfile(file_path)  # Открытие файла в его ассоциированном приложении

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path.set(folder_selected)

def select_files():
    files_selected = filedialog.askopenfilenames(filetypes=[("GML files", "*.gml")])
    if files_selected:
        file_list.set(','.join(files_selected))

def start_linting():
    selected_files = file_list.get().split(',') if file_list.get() else None
    directory = folder_path.get() if folder_path.get() else None
    
    if not directory and not selected_files:
        messagebox.showerror("Error", "Please select a folder or files for linting")
        return
    
    log_file = os.path.join(os.path.expanduser("~"), 'lint_log.txt')
    
    progress_queue = queue.Queue()
    log_queue = queue.Queue()

    threading.Thread(target=update_progress, args=(progress_queue,)).start()
    threading.Thread(target=show_logs, args=(log_queue,)).start()

    if directory:
        destination_folder = os.path.join(os.path.expanduser("~"), "Desktop", os.path.basename(directory) + "_linted")
        
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)
        shutil.copytree(directory, destination_folder)
        
        threading.Thread(target=process_files_in_directory, args=(destination_folder, log_file, progress_queue, log_queue)).start()
    elif selected_files:
        threading.Thread(target=process_individual_files, args=(selected_files, log_file, progress_queue, log_queue)).start()

def update_progress(progress_queue):
    while True:
        try:
            current_file, total_files = progress_queue.get_nowait()
            progress['value'] = (current_file / total_files) * 100
            root.update_idletasks()
            if current_file >= total_files:
                break
        except queue.Empty:
            time.sleep(0.1)

def show_logs(log_queue):
    while True:
        try:
            log_message = log_queue.get_nowait()
            log_text.insert(tk.END, log_message + '\n')
            log_text.see(tk.END)
            if "Linting process completed" in log_message:
                break
        except queue.Empty:
            time.sleep(0.1)

root = tk.Tk()
root.title("GML Linter")

folder_path = tk.StringVar()
file_list = tk.StringVar()

tk.Label(root, text="Select Folder:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
tk.Entry(root, textvariable=folder_path, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=select_folder).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="or Select Files:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
tk.Entry(root, textvariable=file_list, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=select_files).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Start Linting", command=start_linting).grid(row=2, column=1, padx=10, pady=10)

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

log_text = tk.Text(root, wrap=tk.WORD, height=15, width=80)
log_text.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

scribble_var = tk.BooleanVar(value=True)
gmlive_var = tk.BooleanVar(value=True)
fmod_var = tk.BooleanVar(value=True)

tk.Checkbutton(root, text="Ignore scribble", variable=scribble_var, command=update_ignore_files_pattern).grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
tk.Checkbutton(root, text="Ignore gmlive", variable=gmlive_var, command=update_ignore_files_pattern).grid(row=5, column=1, padx=10, pady=10, sticky=tk.W)
tk.Checkbutton(root, text="Ignore fmod", variable=fmod_var, command=update_ignore_files_pattern).grid(row=5, column=2, padx=10, pady=10, sticky=tk.W)

root.mainloop()