import os
import json
import threading
import random
import shutil
from PIL import Image, ImageTk
import imagehash
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter.font as tkFont

SETTINGS_FILE = "settings.json"

def find_duplicates(image_dir, progress_callback, stop_flag):
    hashes = defaultdict(list)
    duplicates = []
    files = [f for f in os.listdir(image_dir) if f.lower().endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'))]

    for idx, filename in enumerate(files, 1):
        if stop_flag['stop']:
            break
        path = os.path.join(image_dir, filename)
        try:
            with Image.open(path) as img:
                h = str(imagehash.phash(img))
        except Exception:
            continue
        hashes[h].append(filename)
        progress_callback(f"Перевірено {idx}/{len(files)} файлів", idx, len(files))

    for file_list in hashes.values():
        if len(file_list) > 1:
            duplicates.append(file_list)

    if duplicates:
        dup_dir = os.path.join(image_dir, "Duplicate")
        os.makedirs(dup_dir, exist_ok=True)
        moved = set()
        for group in duplicates:
            for file in group[1:]:
                if file not in moved:
                    shutil.move(os.path.join(image_dir, file), os.path.join(dup_dir, file))
                    moved.add(file)

    return duplicates

def split_dataset(folder, train_pct, val_pct, test_pct, log_callback):
    files = [f for f in os.listdir(folder) if f.lower().endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'))]
    random.shuffle(files)
    train_count = int(len(files) * train_pct / 100)
    val_count = int(len(files) * val_pct / 100)
    train_files = files[:train_count]
    val_files = files[train_count:train_count+val_count]
    test_files = files[train_count+val_count:]

    for subfolder, subfiles in zip(['train', 'val', 'test'], [train_files, val_files, test_files]):
        img_path = os.path.join(folder, 'images', subfolder)
        os.makedirs(img_path, exist_ok=True)
        for f in subfiles:
            shutil.copy2(os.path.join(folder, f), os.path.join(img_path, f))
        log_callback(f"✓ {subfolder.upper()}: {len(subfiles)} файлів")

    stats = {}
    for subfolder in ['train', 'val', 'test']:
        img_path = os.path.join(folder, 'images', subfolder)
        count = len([f for f in os.listdir(img_path) if f.lower().endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'))])
        stats[subfolder] = count

    with open("split_log.txt", "w", encoding='utf-8') as f:
        f.write(f"Dataset Split Results:\n")
        f.write(f"Train: {len(train_files)} files\n")
        f.write(f"Validation: {len(val_files)} files\n")
        f.write(f"Test: {len(test_files)} files\n")
        f.write("\nСтатистика по підпапках:\n")
        for k, v in stats.items():
            f.write(f"{k}: {v} зображень\n")

class ModernApp:
    def __init__(self, master):
        self.master = master
        master.title("ImagePro - Duplicate Checker & Dataset Splitter")
        master.geometry("900x700")
        master.minsize(800, 600)
        master.configure(bg="#f8f9fa")
        
        try:
            master.iconbitmap("app_icon.ico")
        except:
            pass
        
        self.folder = ''
        self.stop_flag = {'stop': False}
        self.load_settings()
        
        self.setup_styles()
        
        self.create_header()
        self.create_main_content()
        self.create_footer()
        
        self.center_window()
        
    def setup_styles(self):
        """Налаштування сучасних стилів"""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.colors = {
            'primary': '#2563eb',
            'primary_hover': '#1d4ed8',
            'secondary': '#64748b',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'light': '#f8fafc',
            'dark': '#1e293b',
            'white': '#ffffff',
            'border': '#e2e8f0'
        }
        
        self.fonts = {
            'title': tkFont.Font(family='Segoe UI', size=20, weight='bold'),
            'subtitle': tkFont.Font(family='Segoe UI', size=12, weight='normal'),
            'button': tkFont.Font(family='Segoe UI', size=10, weight='bold'),
            'label': tkFont.Font(family='Segoe UI', size=10),
            'entry': tkFont.Font(family='Segoe UI', size=10)
        }
        
        style.configure("Primary.TButton", 
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12))
        
        style.configure("Secondary.TButton",
                       background=self.colors['secondary'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 10))
        
        style.configure("Success.TButton",
                       background=self.colors['success'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 10))
        
        style.configure("Danger.TButton",
                       background=self.colors['danger'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 10))
        
        style.configure("Title.TLabel",
                       background=self.colors['light'],
                       foreground=self.colors['dark'],
                       font=self.fonts['title'])
        
        style.configure("Subtitle.TLabel",
                       background=self.colors['light'],
                       foreground=self.colors['secondary'],
                       font=self.fonts['subtitle'])
        
        style.configure("Modern.TLabel",
                       background=self.colors['white'],
                       foreground=self.colors['dark'],
                       font=self.fonts['label'])
        
        style.configure("Modern.TEntry",
                       fieldbackground=self.colors['white'],
                       foreground=self.colors['dark'],
                       borderwidth=2,
                       relief='solid',
                       font=self.fonts['entry'])
        
        style.configure("Modern.Horizontal.TProgressbar",
                       background=self.colors['primary'],
                       troughcolor=self.colors['border'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
    
    def create_header(self):
        """Створення заголовка"""
        header_frame = tk.Frame(self.master, bg=self.colors['light'], height=100)
        header_frame.pack(fill='x', padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        title_label = ttk.Label(header_frame, text="ImagePro", style="Title.TLabel")
        title_label.pack(side='left', padx=10, pady=20)
        
        subtitle_label = ttk.Label(header_frame, 
                                 text="Професійний інструмент для пошуку дублікатів та розподілу датасетів",
                                 style="Subtitle.TLabel")
        subtitle_label.pack(side='left', padx=10, pady=25)
    
    def create_main_content(self):
        """Створення основного контенту"""
        main_frame = tk.Frame(self.master, bg=self.colors['light'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        top_frame = tk.Frame(main_frame, bg=self.colors['light'])
        top_frame.pack(fill='both', expand=True)
        
        self.create_duplicates_panel(top_frame)
        
        self.create_logs_panel(top_frame)
        
        self.create_dataset_panel(top_frame)
    
    def create_duplicates_panel(self, parent):
        """Панель для пошуку дублікатів"""
        duplicates_frame = tk.Frame(parent, bg=self.colors['white'], relief='solid', bd=1)
        duplicates_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        title_frame = tk.Frame(duplicates_frame, bg=self.colors['primary'], height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        ttk.Label(title_frame, text="🔍 Пошук дублікатів", 
                 foreground=self.colors['white'], background=self.colors['primary'],
                 font=self.fonts['button']).pack(pady=15)
        
        content_frame = tk.Frame(duplicates_frame, bg=self.colors['white'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        folder_frame = tk.Frame(content_frame, bg=self.colors['white'])
        folder_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(folder_frame, text="Оберіть папку для сканування:", 
                 style="Modern.TLabel").pack(anchor='w', pady=(0, 10))
        
        self.folder_label = ttk.Label(folder_frame, text="📁 Папка не обрана", 
                                    style="Modern.TLabel",
                                    foreground=self.colors['secondary'])
        self.folder_label.pack(anchor='w', pady=(0, 10))
        
        ttk.Button(folder_frame, text="📂 Обрати папку", 
                  command=self.select_folder, style="Primary.TButton").pack(pady=10)
        
        buttons_frame = tk.Frame(content_frame, bg=self.colors['white'])
        buttons_frame.pack(fill='x', pady=20)
        
        ttk.Button(buttons_frame, text="🚀 Знайти дублікати", 
                  command=self.start_duplicates, style="Success.TButton").pack(fill='x', pady=(0, 10))
        
        ttk.Button(buttons_frame, text="⏹ Зупинити", 
                  command=self.stop_duplicates, style="Danger.TButton").pack(fill='x')
        
        self.stats_frame = tk.Frame(content_frame, bg=self.colors['light'], relief='solid', bd=1)
        self.stats_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Label(self.stats_frame, text="📊 Статистика", 
                 style="Modern.TLabel", font=self.fonts['button']).pack(pady=(10, 5))
        
        self.stats_text = ttk.Label(self.stats_frame, text="Готовий до сканування", 
                                   style="Modern.TLabel")
        self.stats_text.pack(pady=(0, 10))
    
    def create_dataset_panel(self, parent):
        """Панель для розподілу датасету"""
        dataset_frame = tk.Frame(parent, bg=self.colors['white'], relief='solid', bd=1)
        dataset_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        title_frame = tk.Frame(dataset_frame, bg=self.colors['success'], height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        ttk.Label(title_frame, text="📊 Розподіл датасету", 
                 foreground=self.colors['white'], background=self.colors['success'],
                 font=self.fonts['button']).pack(pady=15)
        
        content_frame = tk.Frame(dataset_frame, bg=self.colors['white'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(content_frame, text="Налаштування розподілу (%)", 
                 style="Modern.TLabel", font=self.fonts['button']).pack(anchor='w', pady=(0, 20))
        
        train_frame = tk.Frame(content_frame, bg=self.colors['white'])
        train_frame.pack(fill='x', pady=10)
        
        ttk.Label(train_frame, text="🎯 Тренування:", style="Modern.TLabel").pack(side='left')
        self.train_entry = ttk.Entry(train_frame, style="Modern.TEntry", width=10)
        self.train_entry.pack(side='right')
        self.train_entry.insert(0, self.settings.get("train", "70"))
        
        val_frame = tk.Frame(content_frame, bg=self.colors['white'])
        val_frame.pack(fill='x', pady=10)
        
        ttk.Label(val_frame, text="🔍 Валідація:", style="Modern.TLabel").pack(side='left')
        self.val_entry = ttk.Entry(val_frame, style="Modern.TEntry", width=10)
        self.val_entry.pack(side='right')
        self.val_entry.insert(0, self.settings.get("val", "15"))
        
        test_frame = tk.Frame(content_frame, bg=self.colors['white'])
        test_frame.pack(fill='x', pady=10)
        
        ttk.Label(test_frame, text="🧪 Тестування:", style="Modern.TLabel").pack(side='left')
        self.test_entry = ttk.Entry(test_frame, style="Modern.TEntry", width=10)
        self.test_entry.pack(side='right')
        self.test_entry.insert(0, self.settings.get("test", "15"))
        
        self.create_distribution_chart(content_frame)
        
        ttk.Button(content_frame, text="⚡ Розподілити датасет", 
                  command=self.run_split, style="Success.TButton").pack(fill='x', pady=20)
    
    def create_distribution_chart(self, parent):
        """Створення візуалізації розподілу"""
        chart_frame = tk.Frame(parent, bg=self.colors['light'], relief='solid', bd=1)
        chart_frame.pack(fill='x', pady=20)
        
        ttk.Label(chart_frame, text="📈 Поточний розподіл", 
                 style="Modern.TLabel", font=self.fonts['button']).pack(pady=(10, 5))
        
        self.chart_container = tk.Frame(chart_frame, bg=self.colors['light'])
        self.chart_container.pack(fill='x', padx=20, pady=(0, 10))
        
        self.update_chart()
    
    def update_chart(self):
        """Оновлення візуалізації розподілу"""
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        try:
            train = float(self.train_entry.get() or 0)
            val = float(self.val_entry.get() or 0)
            test = float(self.test_entry.get() or 0)
            
            total = train + val + test
            if total == 0:
                return
            
            for name, value, color in [("Train", train, self.colors['primary']), 
                                     ("Val", val, self.colors['warning']), 
                                     ("Test", test, self.colors['success'])]:
                frame = tk.Frame(self.chart_container, bg=self.colors['light'])
                frame.pack(fill='x', pady=2)
                
                label = tk.Label(frame, text=f"{name}: {value}%", 
                               bg=self.colors['light'], fg=self.colors['dark'],
                               font=self.fonts['label'])
                label.pack(side='left')
                
                bar_frame = tk.Frame(frame, bg=self.colors['border'], height=20)
                bar_frame.pack(side='right', fill='x', expand=True, padx=(10, 0))
                
                if total > 0:
                    width = int((value / 100) * 200)
                    bar = tk.Frame(bar_frame, bg=color, height=20, width=width)
                    bar.pack(side='left')
                    
        except ValueError:
            pass
    
    def create_logs_panel(self, parent):
        """Панель логів"""
        logs_frame = tk.Frame(parent, bg=self.colors['white'], relief='solid', bd=1)
        logs_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        title_frame = tk.Frame(logs_frame, bg=self.colors['secondary'], height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        ttk.Label(title_frame, text="📋 Логи виконання", 
                 foreground=self.colors['white'], background=self.colors['secondary'],
                 font=self.fonts['button']).pack(pady=15)
        
        logs_content = tk.Frame(logs_frame, bg=self.colors['white'])
        logs_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.log = scrolledtext.ScrolledText(logs_content, 
                                           width=40, height=15,
                                           bg=self.colors['dark'],
                                           fg=self.colors['white'],
                                           font=self.fonts['entry'],
                                           wrap=tk.WORD)
        self.log.pack(fill='both', expand=True)
        
        self.progress = ttk.Progressbar(logs_content, style="Modern.Horizontal.TProgressbar")
        self.progress.pack(fill='x', pady=(10, 0))
    
    def create_footer(self):
        """Створення футера"""
        footer_frame = tk.Frame(self.master, bg=self.colors['dark'], height=40)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        status_label = tk.Label(footer_frame, text="Готовий до роботи", 
                               bg=self.colors['dark'], fg=self.colors['white'],
                               font=self.fonts['label'])
        status_label.pack(side='left', padx=20, pady=10)
        
        version_label = tk.Label(footer_frame, text="v2.0 Professional", 
                                bg=self.colors['dark'], fg=self.colors['secondary'],
                                font=self.fonts['label'])
        version_label.pack(side='right', padx=20, pady=10)
    
    def center_window(self):
        """Центрування вікна на екрані"""
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {}
    
    def save_settings(self):
        self.settings = {
            "train": self.train_entry.get(),
            "val": self.val_entry.get(),
            "test": self.test_entry.get()
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f)
    
    def select_folder(self):
        self.folder = filedialog.askdirectory()
        if self.folder:
            self.folder_label.config(text=f"📁 {os.path.basename(self.folder)}")
            self.log.insert(tk.END, f"✓ Обрано папку: {self.folder}\n")
            self.log.see(tk.END)
            
            try:
                files = [f for f in os.listdir(self.folder) if f.lower().endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'))]
                self.stats_text.config(text=f"Знайдено {len(files)} зображень")
            except:
                self.stats_text.config(text="Помилка читання папки")
    
    def start_duplicates(self):
        if not self.folder:
            messagebox.showerror("Помилка", "Будь ласка, оберіть папку для сканування")
            return

        self.stop_flag['stop'] = False
        self.log.insert(tk.END, "🚀 Початок пошуку дублікатів...\n")
        self.log.see(tk.END)

        thread = threading.Thread(target=self.run_duplicates)
        thread.daemon = True
        thread.start()
    
    def stop_duplicates(self):
        self.stop_flag['stop'] = True
        self.log.insert(tk.END, "⏹ Зупинено користувачем\n")
        self.log.see(tk.END)
    
    def run_duplicates(self):
        try:
            files = [f for f in os.listdir(self.folder) if f.lower().endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'))]
            self.progress['maximum'] = len(files)
            self.progress['value'] = 0
            
            def update(text, current, total):
                self.master.after(0, lambda: self.update_progress(text, current, total))
            
            dups = find_duplicates(self.folder, update, self.stop_flag)
            
            if not self.stop_flag['stop']:
                self.master.after(0, lambda: self.show_results(dups))
                
        except Exception as e:
            self.master.after(0, lambda: self.show_error(str(e)))
    
    def update_progress(self, text, current, total):
        self.log.insert(tk.END, f"{text}\n")
        self.log.see(tk.END)
        self.progress['value'] = current
        self.stats_text.config(text=f"Прогрес: {current}/{total}")
    
    def show_results(self, dups):
        self.progress['value'] = 0
        if dups:
            moved_count = sum(len(group) - 1 for group in dups)
            result = f"✅ Знайдено {len(dups)} груп дублікатів\n"
            result += f"📁 Переміщено {moved_count} файлів до папки 'Duplicate'\n"
            self.log.insert(tk.END, result)
            self.stats_text.config(text=f"Знайдено {len(dups)} груп дублікатів")
            self.show_duplicates_preview(dups)
        else:
            result = "✅ Дублікати не знайдено"
            self.log.insert(tk.END, result + "\n")
            self.stats_text.config(text="Дублікати не знайдено")
        
        self.log.see(tk.END)
        messagebox.showinfo("Результат", result)

    def show_duplicates_preview(self, dups):
        """Відкрити вікно з прев’ю знайдених дублікатів з можливістю масштабування"""
        preview_win = tk.Toplevel(self.master)
        preview_win.title("Прев’ю дублікатів")
        preview_win.geometry("900x700")
        canvas = tk.Canvas(preview_win, bg="#f8fafc")
        canvas.pack(fill='both', expand=True, side='left')
        scrollbar = ttk.Scrollbar(preview_win, orient="vertical", command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=scrollbar.set)
        frame = tk.Frame(canvas, bg="#f8fafc")
        canvas.create_window((0, 0), window=frame, anchor='nw')

        size_frame = tk.Frame(preview_win, bg="#f8fafc")
        size_frame.place(relx=0.5, rely=0, anchor='n')
        tk.Label(size_frame, text="Розмір мініатюр (80-500):", bg="#f8fafc").pack(side='left')
        thumb_size_var = tk.StringVar(value="150")
        size_entry = tk.Entry(size_frame, textvariable=thumb_size_var, width=5)
        size_entry.pack(side='left', padx=5)

        preview_win.thumbs = []

        def render_thumbnails():
            for widget in frame.winfo_children():
                widget.destroy()
            preview_win.thumbs.clear()
            try:
                thumb_size = int(thumb_size_var.get())
                if thumb_size < 80:
                    thumb_size = 80
                if thumb_size > 500:
                    thumb_size = 500
            except ValueError:
                thumb_size = 150
            thumb_size_var.set(str(thumb_size))
            for idx, group in enumerate(dups, 1):
                group_label = tk.Label(frame, text=f"Група {idx} ({len(group)}):", font=("Segoe UI", 10, "bold"), bg="#f8fafc")
                group_label.pack(anchor='w', pady=(10, 0))
                row = tk.Frame(frame, bg="#f8fafc")
                row.pack(anchor='w', pady=(0, 10))
                for file in group:
                    img_path = os.path.join(self.folder, "Duplicate", file) if os.path.exists(os.path.join(self.folder, "Duplicate", file)) else os.path.join(self.folder, file)
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((thumb_size, thumb_size))
                        thumb = ImageTk.PhotoImage(img)
                        preview_win.thumbs.append(thumb)
                        lbl = tk.Label(row, image=thumb, text=file, compound='top', bg="#f8fafc")
                        lbl.pack(side='left', padx=5)
                    except Exception:
                        lbl = tk.Label(row, text=file, bg="#f8fafc", fg="red")
                        lbl.pack(side='left', padx=5)
            frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-3, "units")
            elif event.num == 5:
                canvas.yview_scroll(3, "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        def on_entry_change(*args):
            render_thumbnails()
        thumb_size_var.trace_add("write", on_entry_change)
        size_entry.bind('<Return>', lambda e: render_thumbnails())
        size_entry.bind('<FocusOut>', lambda e: render_thumbnails())

        render_thumbnails()
    
    def show_error(self, error):
        self.log.insert(tk.END, f"❌ Помилка: {error}\n")
        self.log.see(tk.END)
        messagebox.showerror("Помилка", error)
    
    def run_split(self):
        try:
            train = float(self.train_entry.get())
            val = float(self.val_entry.get())
            test = float(self.test_entry.get())
            
            if abs(train + val + test - 100) > 0.01:
                messagebox.showerror("Помилка", "Сума відсотків має дорівнювати 100%")
                return
            
            if not self.folder:
                messagebox.showerror("Помилка", "Будь ласка, оберіть папку")
                return
            
            self.save_settings()
            self.update_chart()
            
            self.log.insert(tk.END, "⚡ Початок розподілу датасету...\n")
            self.log.see(tk.END)
            
            def log_callback(text):
                self.log.insert(tk.END, f"{text}\n")
                self.log.see(tk.END)
            
            split_dataset(self.folder, train, val, test, log_callback)
            
            self.log.insert(tk.END, "✅ Датасет успішно розподілено!\n")
            self.log.see(tk.END)
            messagebox.showinfo("Готово", "Датасет успішно розподілено!\nЛог збережено у файл split_log.txt")
            
        except ValueError:
            messagebox.showerror("Помилка", "Будь ласка, введіть коректні числові значення")
        except Exception as e:
            messagebox.showerror("Помилка", f"Виникла помилка: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ModernApp(root)
    
    def on_entry_change(*args):
        app.update_chart()
    
    for entry in [app.train_entry, app.val_entry, app.test_entry]:
        entry.bind('<KeyRelease>', on_entry_change)
    
    root.mainloop()
