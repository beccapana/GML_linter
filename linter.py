import os
import json
import re
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
    # Удаляем пустые строки в начале и в конце
    code = re.sub(r'^\s*\n+', '', code)  # Удаляем пустые строки в начале
    code = re.sub(r'\n+\s*$', '', code)  # Удаляем пустые строки в конце
    
    # Заменяем несколько последовательных пустых строк на одну пустую строку в середине
    code = re.sub(r'\n\s*\n+', '\n\n', code)
    
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

def process_files_in_directory(directory, log_queue, do_not_delete_paths, do_not_edit_paths):
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

    if potential_unwanted_files:
        show_potential_unwanted_files_alert(potential_unwanted_files)

    # Обновляем настройки после обработки файлов
    save_settings()

def process_individual_files(files, log_queue, do_not_delete_paths, do_not_edit_paths):
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

    if potential_unwanted_files:
        show_potential_unwanted_files_alert(potential_unwanted_files)

    # Обновляем настройки после обработки файлов
    save_settings()

def browse_files():
    files = filedialog.askopenfilenames(filetypes=[("GML Files", "*.gml")])
    if files:
        files = list(files)  # Convert tuple to list
        path_entry.delete(0, tk.END)
        path_entry.insert(0, ';'.join(files))

def select_folder():
    global folder_path
    folder_path = filedialog.askdirectory()
    if folder_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_path)
        save_settings()  # Save folder path when a new one is selected

def show_potential_unwanted_files_alert(files):
    message = "The following files are potentially unwanted:\n\n"
    for file_path in files:
        message += f"{file_path}\n"
    messagebox.showwarning("Potentially Unwanted Files", message)

def start_linting():
    path = path_entry.get().strip()
    
    do_not_delete_paths = normalize_paths(do_not_delete_text.get("1.0", tk.END).split('\n'))
    do_not_edit_paths = normalize_paths(do_not_edit_text.get("1.0", tk.END).split('\n'))
    
    if path:
        log_queue = queue.Queue()
        threading.Thread(target=process_path, args=(path, log_queue, do_not_delete_paths, do_not_edit_paths)).start()
        threading.Thread(target=update_log_text, args=(log_queue,)).start()
    else:
        messagebox.showwarning("Warning", "Please select a path.")

def process_path(path, log_queue, do_not_delete_paths, do_not_edit_paths):
    if os.path.isfile(path):
        process_individual_files([path], log_queue, do_not_delete_paths, do_not_edit_paths)
    elif os.path.isdir(path):
        process_files_in_directory(path, log_queue, do_not_delete_paths, do_not_edit_paths)
    else:
        messagebox.showwarning("Warning", "Invalid path. Please select a valid file or directory.")

def update_log_text(log_queue):
    while True:
        try:
            log_message = log_queue.get_nowait()
            log_text.insert(tk.END, log_message + '\n')
            log_text.see(tk.END)
        except queue.Empty:
            time.sleep(0.1)

def save_settings():
    settings = {
        'path': path_entry.get().strip(),
        'do_not_delete_paths': [line.strip() for line in do_not_delete_text.get("1.0", tk.END).split('\n') if line.strip()],
        'do_not_edit_paths': [line.strip() for line in do_not_edit_text.get("1.0", tk.END).split('\n') if line.strip()],
        'scribble': scribble_var.get(),
        'gmlive': gmlive_var.get(),
        'fmod': fmod_var.get(),
        'folder_path': folder_path  # Добавляем путь папки в настройки
    }
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_settings():
    global folder_path
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            path_entry.delete(0, tk.END)
            path_entry.insert(0, settings.get('path', ''))
            do_not_delete_text.delete("1.0", tk.END)
            do_not_delete_text.insert("1.0", '\n'.join(settings.get('do_not_delete_paths', [])))
            do_not_edit_text.delete("1.0", tk.END)
            do_not_edit_text.insert("1.0", '\n'.join(settings.get('do_not_edit_paths', [])))
            scribble_var.set(settings.get('scribble', 0))
            gmlive_var.set(settings.get('gmlive', 0))
            fmod_var.set(settings.get('fmod', 0))
            folder_path = settings.get('folder_path', '')  # Загружаем путь папки из настроек
    except FileNotFoundError:
        pass

root = tk.Tk()
root.title("GML Linter")

# Создание элементов интерфейса
path_label = tk.Label(root, text="Select file or folder:")
path_label.pack()

path_entry = tk.Entry(root, width=50)
path_entry.pack()

browse_button = tk.Button(root, text="Browse Files", command=browse_files)
browse_button.pack()

select_folder_button = tk.Button(root, text="Select Folder", command=select_folder)
select_folder_button.pack()

log_text = tk.Text(root, wrap=tk.WORD, width=80, height=20)
log_text.pack()

do_not_delete_label = tk.Label(root, text="Do not delete paths:")
do_not_delete_label.pack()

do_not_delete_text = tk.Text(root, wrap=tk.WORD, width=50, height=5)
do_not_delete_text.pack()

do_not_edit_label = tk.Label(root, text="Do not edit paths:")
do_not_edit_label.pack()

do_not_edit_text = tk.Text(root, wrap=tk.WORD, width=50, height=5)
do_not_edit_text.pack()

scribble_var = tk.IntVar()
scribble_checkbox = tk.Checkbutton(root, text="Ignore scribble files", variable=scribble_var, command=update_ignore_files_pattern)
scribble_checkbox.pack()

gmlive_var = tk.IntVar()
gmlive_checkbox = tk.Checkbutton(root, text="Ignore GMLive files", variable=gmlive_var, command=update_ignore_files_pattern)
gmlive_checkbox.pack()

fmod_var = tk.IntVar()
fmod_checkbox = tk.Checkbutton(root, text="Ignore FMOD files", variable=fmod_var, command=update_ignore_files_pattern)
fmod_checkbox.pack()

lint_button = tk.Button(root, text="Start Linting", command=start_linting)
lint_button.pack()

load_settings()
root.mainloop()
