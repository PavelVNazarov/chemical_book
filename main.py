# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import random
from datetime import datetime
from PIL import Image, ImageTk


class BookManager:
    def __init__(self, books_dir="books"):
        self.books_dir = books_dir
        self._books_cache = None

    def load_books(self, force_reload=False):
        if self._books_cache and not force_reload:
            return self._books_cache

        books = []
        for file in os.listdir(self.books_dir):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(self.books_dir, file), 'r', encoding='utf-8-sig') as f:
                        book_data = json.load(f)

                        if not all(key in book_data.get('metadata', {}) for key in ['title', 'description', 'image']):
                            continue

                        books.append({
                            'id': file.split('.')[0],
                            **book_data['metadata'],
                            'paragraphs': [p for p in book_data.get('paragraphs', []) if 'number' in p and 'text' in p]
                        })
                except Exception as e:
                    print(f"Ошибка обработки файла {file}: {str(e)}")

        self._books_cache = books
        return books


class GameState:
    def __init__(self):
        self.current_book = None
        self.current_paragraph = 1
        self.saves_dir = "saves"
        os.makedirs(self.saves_dir, exist_ok=True)

    def save_game(self, title):
        if not self.current_book:
            return

        data = {
            'book_id': self.current_book['id'],
            'paragraph': self.current_paragraph,
            'timestamp': datetime.now().isoformat()
        }
        filename = f"save_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(os.path.join(self.saves_dir, filename), 'w') as f:
            json.dump(data, f)

    def load_saves(self):
        return sorted(
            [{'filename': f, **json.load(open(os.path.join(self.saves_dir, f), 'r'))}
             for f in os.listdir(self.saves_dir) if f.startswith("save_")],
            key=lambda x: x['timestamp'],
            reverse=True
        )

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Химическая Книга-Игра")
        self.geometry("800x600")
        self.book_images = []  # Хранилище для изображений книг
        self._configure_styles()
        self.book_manager = BookManager()
        self.game_state = GameState()
        self.show_welcome_screen()

    def _configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", padding=6, font=('Arial', 10))
        self.style.configure("Accent.TButton", foreground="white", background="#3498db", font=('Arial', 11, 'bold'))
        self.style.configure("Danger.TButton", foreground="white", background="#e74c3c")

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.book_images.clear()  # Очищаем старые изображения

    # Исправленный метод для отображения книг
    def show_book_selection(self):
        self.clear_window()
        ttk.Label(self, text="Выберите сценарий", font=('Arial', 16, 'bold')).pack(pady=20)

        container = ttk.Frame(self)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Загрузка книг с кэшированием
        books = self.book_manager.load_books()

        for book in books:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=5, padx=10)

            # Блок с изображением
            icon_frame = ttk.Frame(frame)
            icon_frame.pack(side="left", padx=10)
            try:
                img_path = os.path.join("images", book['image'])
                if os.path.exists(img_path):
                    img = Image.open(img_path).resize((100, 100), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    self.book_images.append(photo_img)  # Сохраняем ссылку
                    ttk.Label(icon_frame, image=photo_img).pack()
            except Exception as e:
                ttk.Label(icon_frame, text="🚫", font=('Arial', 24)).pack()

            # Блок с текстом
            text_frame = ttk.Frame(frame)
            text_frame.pack(side="left", fill="x", expand=True)
            ttk.Label(text_frame, text=book['title'], font=('Arial', 12, 'bold')).pack(anchor="w")
            ttk.Label(text_frame, text=book['description'], wraplength=500).pack(anchor="w")

            ttk.Button(
                frame,
                text="Выбрать ▶",
                style="Accent.TButton",
                command=lambda b=book: self.select_book(b)
            ).pack(side="right", padx=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        ttk.Button(self, text="← Назад", command=self.show_welcome_screen).pack(side="bottom", pady=10)

    def show_welcome_screen(self):
        self.clear_window()

        try:
            bg_image = Image.open("images/welcome_bg.png")
            bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_image)
            ttk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Ошибка загрузки фона: {str(e)}")

        main_frame = ttk.Frame(self)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        try:
            logo_image = Image.open("images/main_logo.png")
            logo_image = logo_image.resize((300, 150))
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            ttk.Label(main_frame, image=self.logo_photo).pack(pady=20)
        except Exception as e:
            print(f"Ошибка загрузки логотипа: {str(e)}")

        ttk.Button(
            main_frame,
            text="🚀 Начать игру",
            style="Accent.TButton",
            command=self.show_book_selection
        ).pack(pady=20)


    def select_book(self, book):
        self.game_state.current_book = book
        self.show_main_menu()

    def show_main_menu(self):
        self.clear_window()
        if not self.game_state.current_book:
            self.show_book_selection()
            return

        current_book = self.game_state.current_book
        header_frame = ttk.Frame(self)
        header_frame.pack(pady=20)

        try:
            book_image = Image.open(f"images/{current_book['image']}")
            book_image = book_image.resize((150, 150))
            self.book_image = ImageTk.PhotoImage(book_image)
            ttk.Label(header_frame, image=self.book_image).pack(side="left", padx=20)
        except Exception as e:
            print(f"Ошибка загрузки изображения книги: {str(e)}")

        ttk.Label(
            header_frame,
            text=current_book['title'],
            font=('Arial', 16, 'bold'),
            foreground="#2c3e50"
        ).pack(side="left")

        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(pady=50)

        buttons = [
            ("📖 Новая игра", self.start_new_game),
            ("💾 Загрузить игру", self.show_load_menu),
            ("🚪 Выйти", self.quit)
        ]

        for text, cmd in buttons:
            ttk.Button(
                buttons_frame,
                text=text,
                style="Accent.TButton",
                command=cmd
            ).pack(pady=10, fill="x")

    def start_new_game(self):
        self.game_state.current_paragraph = 1
        self.show_paragraph()

    def show_paragraph(self):
        self.clear_window()
        try:
            paragraph = next(
                p for p in self.game_state.current_book['paragraphs']
                if p['number'] == self.game_state.current_paragraph
            )
        except StopIteration:
            messagebox.showerror("Ошибка", "Параграф не найден!")
            return

        # Контейнер с прокруткой
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Содержимое параграфа
        if 'image_path' in paragraph:
            try:
                image = Image.open(f"images/{paragraph['image_path']}")
                image = image.resize((400, 300))
                self.para_image = ImageTk.PhotoImage(image)
                ttk.Label(scrollable_frame, image=self.para_image).pack(pady=10)
            except Exception as e:
                print(f"Ошибка загрузки изображения: {str(e)}")

        ttk.Label(
            scrollable_frame,
            text=paragraph['text'],
            wraplength=700,
            font=('Arial', 11),
            foreground="#2c3e50"
        ).pack(pady=10)

        for idx, option in enumerate(paragraph.get('options', [])):
            ttk.Button(
                scrollable_frame,
                text=f" {option['text']}",
                style="Accent.TButton",
                command=lambda t=option['target']: self.select_option(t)
            ).pack(fill="x", pady=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Панель управления
        toolbar = ttk.Frame(self)
        toolbar.pack(side="bottom", fill="x", pady=10)
        ttk.Button(
            toolbar,
            text="💾 Сохранить игру",
            style="TButton",
            command=self.show_save_dialog
        ).pack(side="left", padx=5)
        ttk.Button(
            toolbar,
            text="🏠 В главное меню",
            style="TButton",
            command=self.confirm_exit_to_menu
        ).pack(side="left", padx=5)

    def confirm_exit_to_menu(self):
        if messagebox.askyesno("Подтверждение", "Вернуться в главное меню?\nНесохраненный прогресс будет потерян!"):
            self.game_state.current_book = None
            self.show_book_selection()

    def select_option(self, target):
        self.game_state.current_paragraph = target
        self.show_paragraph()

    def show_save_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Сохранение игры")
        ttk.Label(dialog, text="Название сохранения:", font=('Arial', 10)).pack(pady=10)
        entry = ttk.Entry(dialog, width=30, font=('Arial', 10))
        entry.pack(pady=5)
        ttk.Button(
            dialog,
            text="Сохранить",
            style="Accent.TButton",
            command=lambda: self.save_and_close(entry.get(), dialog)
        ).pack(pady=10)

    def save_and_close(self, title, dialog):
        self.game_state.save_game(title)
        dialog.destroy()
        messagebox.showinfo("Сохранено", "Игра успешно сохранена!")

    def show_load_menu(self):
        dialog = tk.Toplevel(self)
        dialog.title("Загрузить сохранение")
        saves = self.game_state.load_saves()

        if not saves:
            ttk.Label(dialog, text="Нет доступных сохранений").pack(pady=20)
            return

        for save in saves:
            frame = ttk.Frame(dialog)
            frame.pack(fill="x", pady=2, padx=10)
            ttk.Label(frame, text=save['title'], width=40, font=('Arial', 9)).pack(side="left")
            ttk.Button(
                frame,
                text="🗑",
                style="Danger.TButton",
                command=lambda s=save: self.delete_save(s, dialog)
            ).pack(side="right", padx=5)
            ttk.Button(
                frame,
                text="📂 Загрузить",
                style="Accent.TButton",
                command=lambda s=save: self.load_game(s, dialog)
            ).pack(side="right", padx=5)

    def load_game(self, save, dialog):
        self.game_state.current_paragraph = save['paragraph']
        dialog.destroy()
        self.show_paragraph()

    def delete_save(self, save, dialog):
        if messagebox.askyesno("Удаление", f"Удалить сохранение '{save['title']}'?"):
            os.remove(os.path.join(self.game_state.saves_dir, save['filename']))
            dialog.destroy()
            self.show_load_menu()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
