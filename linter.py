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
    
    # Объединение строк кода обратно в одну строку
    code = '\n'.join(lines)
    
    # Обновление регулярного выражения для обработки конструкций
    code = re.sub(r'(\b(if|while|for|switch|with|repeat|else|do)\b[^{;]*\))\s*(?=\{)', r'\1', code)
    
    code_lines = code.split('\n')
    inside_enum = False
    enum_lines = []
    enum_start = -1
    inside_block = 0

    i = 0
    while i < len(code_lines):
        line = code_lines[i]
        stripped_line = line.strip()
        
        # Обработка блоков enum
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
                # Удаление запятой после последней переменной в enum
                enum_code = '\n'.join(enum_lines)
                enum_code = re.sub(r',\s*(\})', r'\1', enum_code)
                code_lines[enum_start:i+1] = enum_code.split('\n')
            i += 1
            continue
        
        if stripped_line and not inside_enum:
            leading_whitespace = line[:len(line) - len(line.lstrip())]
            
            # Пропуск строк, начинающихся с ';', '//' или '#'
            if stripped_line.startswith(';') or stripped_line.startswith('//') or stripped_line.startswith('#'):
                i += 1
                continue
            
            # Пропуск строк, содержащих ключевые слова 'break', 'continue', 'return', 'else', 'case'
            if re.search(r'\b(break|continue|return|else|case)\b', stripped_line):
                i += 1
                continue
            
            # Пропуск строк, начинающихся с 'enum' или 'function'
            if stripped_line.startswith('enum') or stripped_line.startswith('function'):
                i += 1
                continue
            
            # Пропуск строк, заканчивающихся на ',' или ':'
            if stripped_line.endswith(',') or stripped_line.endswith(':'):
                i += 1
                continue
            
            # Пропуск строк, которые содержат функцию и заканчиваются на '{'
            if stripped_line.endswith('{') and (re.search(r'\b(function|if|while|for|switch|with|repeat)\b', stripped_line)):
                inside_block += 1
                i += 1
                continue
            
            # Пропуск строк, заканчивающихся на '}'
            if stripped_line.endswith('}'):
                inside_block -= 1
                i += 1
                continue
            
            # Пропуск строк, содержащих вызов функции с последующими фигурными скобками
            if re.search(r'\b\w+\s*=\s*\w+\s*\([^;{]+\)\s*{', stripped_line):
                i += 1
                continue
            
            # Обработка строк с '++' и '--'
            if '++' in stripped_line:
                code_part = stripped_line.split('++')[0]
                if code_part.strip().endswith('++'):
                    i += 1
                    continue
            if '--' in stripped_line:
                code_part = stripped_line.split('--')[0]
                if code_part.strip().endswith('--'):
                    i += 1
                    continue
            
            # Обработка строк с комментариями
            if '//' in stripped_line:
                code_part, comment_part = stripped_line.split('//', 1)
                code_part = code_part.rstrip()
                if not (code_part.endswith(';') or code_part.endswith('{') or code_part.endswith('}') or code_part.endswith(');')):
                    code_part += ';'
                code_lines[i] = leading_whitespace + code_part + ' //' + comment_part
            else:
                # Добавление точки с запятой в конце строки, если это необходимо
                if not (stripped_line.endswith(';') or stripped_line.endswith('{') or stripped_line.endswith('}') or stripped_line.endswith(');') or stripped_line.endswith(':')):
                    # Проверка, что следующая строка не начинается с '{'
                    if i + 1 < len(code_lines) and code_lines[i + 1].strip().startswith('{'):
                        i += 1
                        continue
                    code_lines[i] = leading_whitespace + stripped_line + ';'
        i += 1
    
    # Объединение строк кода обратно в одну строку и удаление лишних пустых строк
    code = '\n'.join(code_lines)
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
    
    # Исправление случаев с пустыми блоками после if
    code = re.sub(r'(\bif\b[^{;]*\));\s*{', r'\1 {', code)
    
    return code

def copy_directory_to_desktop(src_directory):
    # Определение пути к рабочему столу
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    # Создание директории копии на рабочем столе
    dst_directory = os.path.join(desktop_path, os.path.basename(src_directory) + "_copy")
    if os.path.exists(dst_directory):
        shutil.rmtree(dst_directory)
    shutil.copytree(src_directory, dst_directory)
    return dst_directory

def lint_gml_files_in_directory(directory, include_special_files):
    linted_files = []
    # Проход по всем файлам в директории и её поддиректориях
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".gml"):
                if not include_special_files and any(ignore in file.lower() for ignore in ["scribble", "gmlive"]):
                    continue
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                linted_code = lint_gml_code(code)
                # Сохранение отредактированного кода в тот же файл
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(linted_code)
                linted_files.append(file_path)
    
    # Запись списка отредактированных файлов в файл linted_files.txt
    linted_files_path = os.path.join(directory, 'linted_files.txt')
    with open(linted_files_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linted_files))
    
    messagebox.showinfo("Готово", "Все файлы GML обработаны и сохранены в своих исходных директориях!")

def lint_gml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    linted_code = lint_gml_code(code)
    # Сохранение отредактированного кода в новый файл
    linted_file_path = os.path.splitext(file_path)[0] + "_linted.gml"
    with open(linted_file_path, 'w', encoding='utf-8') as f:
        f.write(linted_code)
    messagebox.showinfo("Готово", f"Файл {os.path.basename(file_path)} обработан и сохранен как {os.path.basename(linted_file_path)}!")

def select_directory(include_special_files):
    # Открытие диалога выбора директории
    directory = filedialog.askdirectory()
    if directory:
        # Создание копии директории на рабочем столе
        dst_directory = copy_directory_to_desktop(directory)
        # Линтинг файлов в директории копии
        lint_gml_files_in_directory(dst_directory, include_special_files)

def select_file():
    # Открытие диалога выбора файла
    file_path = filedialog.askopenfilename(filetypes=[("GML files", "*.gml")])
    if file_path:
        lint_gml_file(file_path)

def create_gui():
    # Создание GUI приложения
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