import os
import json
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import time
import threading
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
        if line.strip() and not line.strip().startswith('//'):
            return False
    return True

def process_file(file_path, log_queue, do_not_delete_paths, do_not_edit_paths):
    log_queue.put(f'Processing file: {file_path}')
    
    # Проверка исключений для удаления
    if any(os.path.normpath(file_path).startswith(os.path.normpath(path)) for path in do_not_delete_paths):
        log_queue.put(f'Skipped deletion (Do not delete): {file_path}')
        return []  # Не удаляем и не редактируем файл

    # Проверка исключений для редактирования
    if any(os.path.normpath(file_path).startswith(os.path.normpath(path)) for path in do_not_edit_paths):
        log_queue.put(f'Skipped editing (Do not edit): {file_path}')
        return []  # Не редактируем файл, но оставляем его в исходном виде

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except IOError as e:
        log_queue.put(f'Error reading file {file_path}: {e}')
        return []

    linted_code = lint_gml_code(code)
    
    if linted_code.strip() == '' or linted_code.strip() == 'event_inherited();':
        if not any(os.path.normpath(file_path).startswith(os.path.normpath(path)) for path in do_not_delete_paths):
            try:
                os.remove(file_path)
                log_queue.put(f'Deleted file: {file_path}')
            except IOError as e:
                log_queue.put(f'Error deleting file {file_path}: {e}')
        return []  # Не возвращаем удаленные файлы
    else:
        if not any(os.path.normpath(file_path).startswith(os.path.normpath(path)) for path in do_not_edit_paths):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(linted_code)
                log_queue.put(f'Processed file: {file_path}')
            except IOError as e:
                log_queue.put(f'Error writing to file {file_path}: {e}')
        
        # Добавляем в потенциально нежелательные файлы только если они содержат только комментарии
        if is_potentially_unwanted_file(linted_code):
            return [file_path]
        return []

def normalize_paths(paths):
    """Нормализует и очищает пути из исключений."""
    return [os.path.normpath(path.strip()) for path in paths if path.strip()]

def should_ignore_file(file):
    return ignore_files_pattern.search(file)

def process_files_in_directory(directory, log_file, log_queue, do_not_delete_paths, do_not_edit_paths):
    start_time = time.time()
    
    processed_files = []
    potential_unwanted_files = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.gml') and not should_ignore_file(file):
                    file_path = os.path.join(root, file)
                    futures.append(executor.submit(process_file, file_path, log_queue, do_not_delete_paths, do_not_edit_paths))
        
        for future in futures:
            result = future.result()
            if result:
                processed_files.extend(result)
                potential_unwanted_files.extend(result)
                log_queue.put(f'Processed {result}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    log_queue.put(f"Linting process completed in {elapsed_time:.2f} seconds")

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Processed files:\n")
        for file_path in processed_files:
            log.write(f"{file_path}\n")
    
    if potential_unwanted_files:
        show_potential_unwanted_files_alert(potential_unwanted_files)

def process_individual_files(files, log_file, log_queue, do_not_delete_paths, do_not_edit_paths):
    start_time = time.time()
    
    processed_files = []
    potential_unwanted_files = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for file_path in files:
            futures.append(executor.submit(process_file, file_path, log_queue, do_not_delete_paths, do_not_edit_paths))
        
        for future in futures:
            result = future.result()
            if result:
                processed_files.extend(result)
                potential_unwanted_files.extend(result)
                log_queue.put(f'Processed {result}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    log_queue.put(f"Linting process completed in {elapsed_time:.2f} seconds")

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Processed files:\n")
        for file_path in processed_files:
            log.write(f"{file_path}\n")
    
    if potential_unwanted_files:
        show_potential_unwanted_files_alert(potential_unwanted_files)

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
        os.startfile(file_path)

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
        messagebox.showerror("Error", "Please select a folder or files.")
        return

    log_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if not log_file:
        return

    log_queue = queue.Queue()
    
    do_not_delete_paths = normalize_paths(do_not_delete_text.get().strip().split(','))
    do_not_edit_paths = normalize_paths(do_not_edit_text.get().strip().split(','))

    def logging_thread():
        while True:
            message = log_queue.get()
            if message is None:
                break
            log_text.insert(tk.END, message + "\n")
            log_text.see(tk.END)

    threading.Thread(target=logging_thread, daemon=True).start()

    if directory:
        threading.Thread(target=process_files_in_directory, args=(directory, log_file, log_queue, do_not_delete_paths, do_not_edit_paths), daemon=True).start()
    else:
        threading.Thread(target=process_individual_files, args=(selected_files, log_file, log_queue, do_not_delete_paths, do_not_edit_paths), daemon=True).start()

def save_settings():
    settings = {
        "do_not_delete": do_not_delete_text.get().strip(),
        "do_not_edit": do_not_edit_text.get().strip()
    }
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_settings():
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            do_not_delete_text.insert(tk.END, settings.get("do_not_delete", ""))
            do_not_edit_text.insert(tk.END, settings.get("do_not_edit", ""))
    except FileNotFoundError:
        pass

def normalize_paths(paths):
    return [os.path.normpath(path.strip()) for path in paths]

# Основное окно
root = tk.Tk()
root.title("GML Linter")

# Переменные
folder_path = tk.StringVar()
file_list = tk.StringVar()

scribble_var = tk.BooleanVar(value=True)
gmlive_var = tk.BooleanVar(value=True)
fmod_var = tk.BooleanVar(value=True)

# UI элементы
folder_label = tk.Label(root, text="Select folder:")
folder_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

folder_entry = tk.Entry(root, textvariable=folder_path, width=50)
folder_entry.grid(row=0, column=1, padx=5, pady=5)

folder_button = tk.Button(root, text="Browse", command=select_folder)
folder_button.grid(row=0, column=2, padx=5, pady=5)

files_label = tk.Label(root, text="Or select files:")
files_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

files_entry = tk.Entry(root, textvariable=file_list, width=50)
files_entry.grid(row=1, column=1, padx=5, pady=5)

files_button = tk.Button(root, text="Browse", command=select_files)
files_button.grid(row=1, column=2, padx=5, pady=5)

scribble_check = tk.Checkbutton(root, text="Ignore Scribble files", variable=scribble_var, command=update_ignore_files_pattern)
scribble_check.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

gmlive_check = tk.Checkbutton(root, text="Ignore GMlive files", variable=gmlive_var, command=update_ignore_files_pattern)
gmlive_check.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

fmod_check = tk.Checkbutton(root, text="Ignore FMOD files", variable=fmod_var, command=update_ignore_files_pattern)
fmod_check.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)

# Поля для исключений
do_not_delete_label = tk.Label(root, text="Do not delete:")
do_not_delete_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)

do_not_delete_text = tk.Entry(root, width=50)
do_not_delete_text.grid(row=3, column=1, padx=5, pady=5)

do_not_edit_label = tk.Label(root, text="Do not edit:")
do_not_edit_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)

do_not_edit_text = tk.Entry(root, width=50)
do_not_edit_text.grid(row=4, column=1, padx=5, pady=5)

lint_button = tk.Button(root, text="Start Linting", command=start_linting)
lint_button.grid(row=5, column=1, padx=5, pady=15)

log_text = tk.Text(root, height=20, width=80)
log_text.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

# Загрузка настроек при запуске
load_settings()

# Обработчик закрытия окна
def on_closing():
    # Сначала сохраняем настройки
    save_settings()
    # Завершаем основное окно и все связанные с ним потоки
    root.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Запуск основного цикла
root.mainloop()
