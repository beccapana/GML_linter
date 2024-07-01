import re
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class GMLintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GML Линтер")
        self.root.geometry("800x600")
        self.root.attributes('-fullscreen', True)

        self.dark_theme = True  # Переменная для отслеживания текущей темы
        self.create_widgets()
        self.set_theme_colors()

        # Установка обработчиков для изменения размеров окна
        self.root.bind('<Configure>', self.on_window_resize)

    def create_widgets(self):
        self.label = tk.Label(self.root, text="Выберите папку с файлами GML:", font=("Arial", 14))
        self.label.pack(pady=20)

        self.button = tk.Button(self.root, text="Выбрать папку", font=("Arial", 12), command=self.select_directory)
        self.button.pack(pady=10)

        self.log_text = tk.Text(self.root, height=10, width=100, font=("Arial", 12))
        self.log_text.pack(padx=20, pady=20)

        # Добавляем меню для выбора темы
        self.menu_bar = tk.Menu(self.root)
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme_menu.add_command(label="Тёмная тема", command=self.set_dark_theme)
        self.theme_menu.add_command(label="Светлая тема", command=self.set_light_theme)
        self.menu_bar.add_cascade(label="Тема", menu=self.theme_menu)
        self.root.config(menu=self.menu_bar)

        # Добавляем кнопки свернуть, выйти из полноэкранного режима и закрыть приложение
        self.minimize_button = tk.Button(self.root, text="Свернуть", command=self.minimize_window)
        self.minimize_button.pack(side=tk.LEFT, padx=10)
        self.exit_fullscreen_button = tk.Button(self.root, text="Выйти из полноэкранного режима", command=self.exit_fullscreen)
        self.exit_fullscreen_button.pack(side=tk.LEFT, padx=10)
        self.close_button = tk.Button(self.root, text="Закрыть приложение", command=self.close_app)
        self.close_button.pack(side=tk.LEFT, padx=10)

    def set_dark_theme(self):
        self.dark_theme = True
        self.set_theme_colors()

    def set_light_theme(self):
        self.dark_theme = False
        self.set_theme_colors()

    def set_theme_colors(self):
        if self.dark_theme:
            self.root.configure(bg='#2b2b2b')  # Цвет фона окна
            self.label.configure(bg='#2b2b2b', fg='white')  # Цвет фона и текста метки
            self.button.configure(bg='#4b4b4b', fg='white', activebackground='#333333', activeforeground='white')  # Цвет фона, текста и активных состояний кнопки
            self.log_text.configure(bg='#1e1e1e', fg='white')  # Цвет фона и текста текстового поля лога
        else:
            self.root.configure(bg='white')  # Цвет фона окна
            self.label.configure(bg='white', fg='black')  # Цвет фона и текста метки
            self.button.configure(bg='lightgray', fg='black', activebackground='#cccccc', activeforeground='black')  # Цвет фона, текста и активных состояний кнопки
            self.log_text.configure(bg='whitesmoke', fg='black')  # Цвет фона и текста текстового поля лога

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.log_text.insert(tk.END, f"Выбрана папка: {directory}\n")
            self.copy_and_lint_directory(directory)
            self.log_text.insert(tk.END, "Обработка завершена!\n\n")
            self.log_text.see(tk.END)  # Прокрутка текста вниз

    def copy_and_lint_directory(self, src_directory):
        self.log_text.insert(tk.END, "Копирование и обработка файлов...\n")

        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        dst_directory = os.path.join(desktop_path, os.path.basename(src_directory) + "_copy")
        if os.path.exists(dst_directory):
            shutil.rmtree(dst_directory)
        shutil.copytree(src_directory, dst_directory)

        linted_directory = os.path.join(dst_directory, "linted_files")
        os.makedirs(linted_directory, exist_ok=True)

        for root, _, files in os.walk(dst_directory):
            if 'linted_files' in root:
                continue
            for file in files:
                if file.endswith(".gml"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    linted_code = self.lint_gml_code(code)
                    relative_path = os.path.relpath(root, dst_directory)
                    linted_file_directory = os.path.join(linted_directory, relative_path)
                    os.makedirs(linted_file_directory, exist_ok=True)
                    linted_file_path = os.path.join(linted_file_directory, file)
                    with open(linted_file_path, 'w', encoding='utf-8') as f:
                        f.write(linted_code)
                    self.log_text.insert(tk.END, f"Обработан файл: {os.path.join(relative_path, file)}\n")
                    self.log_text.see(tk.END)  # Прокрутка текста вниз

        messagebox.showinfo("Готово", "Все файлы GML обработаны и сохранены в новой папке на рабочем столе!")

    def lint_gml_code(self, code):
        # Удаление отступов в самом начале кода
        code = code.lstrip()

        # Удаление комментариев в самом начале кода, если они на английском
        lines = code.split('\n')
        while lines and re.match(r'^\s*//\s*[a-zA-Z]', lines[0]):
            lines.pop(0)
        code = '\n'.join(lines)

        # Исправленное регулярное выражение для добавления точек с запятыми
        # Теперь точки с запятыми добавляются только после операторов, не завершающихся фигурной скобкой { или ;
        code = re.sub(r'(\b(?!if|else|for|while|switch|catch)\w+\b[^{;]*)\s*(?=\{)', r'\1;', code)

        # Добавление точек с запятыми в конце строк, если они не заканчиваются на ;, { или }
        code_lines = code.split('\n')
        for i in range(len(code_lines)):
            line = code_lines[i].strip()
            if line and not (line.endswith(';') or line.endswith('{') or line.endswith('}') or line.endswith(');')):
                code_lines[i] = code_lines[i] + ';'

        # Заменяем более одного пустого ряда на один пустой ряд
        code = '\n'.join(code_lines)
        code = re.sub(r'\n\s*\n', '\n', code)

        return code

    def on_window_resize(self, event):
        # Обработка изменения размеров окна
        self.root.update_idletasks()

    def minimize_window(self):
        # Свернуть окно
        self.root.iconify()

    def exit_fullscreen(self):
        # Выйти из полноэкранного режима
        self.root.attributes('-fullscreen', False)
        self.root.geometry("800x600")

    def close_app(self):
        # Закрыть приложение
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GMLintApp(root)
    root.mainloop()
