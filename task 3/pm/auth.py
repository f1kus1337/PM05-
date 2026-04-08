import tkinter as tk
from tkinter import messagebox
from database import Database
from captcha import CaptchaPuzzle

class LoginForm:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.db = Database()
        self.setup_ui()
    
    def setup_ui(self):
        self.root.title("Молочный комбинат Полесье - Система управления")
        self.root.geometry("420x620")
        self.root.minsize(400, 600)
        
        main_container = tk.Frame(self.root, padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        font_title = ("Arial", 14, "bold")
        tk.Label(main_container, text="Вход в систему", font=font_title).pack(pady=(0, 15))
        
        auth_frame = tk.LabelFrame(main_container, text="Авторизация", font=("Arial", 10, "italic"), padx=15, pady=10)
        auth_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(auth_frame, text="Имя пользователя (Логин):", font=("Arial", 11)).pack(anchor="w")
        self.username_entry = tk.Entry(auth_frame, font=("Arial", 11), relief="solid")
        self.username_entry.pack(fill=tk.X, pady=(2, 10))
        
        tk.Label(auth_frame, text="Ваш пароль:", font=("Arial", 11)).pack(anchor="w")
        self.password_entry = tk.Entry(auth_frame, font=("Arial", 11), show="•", relief="solid")
        self.password_entry.pack(fill=tk.X, pady=(2, 5))
        
        captcha_frame = tk.LabelFrame(main_container, font=("Arial", 10, "italic"), padx=10, pady=10)
        captcha_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.captcha = CaptchaPuzzle(captcha_frame)
        self.captcha.pack(pady=5)
        
        btn_frame = tk.Frame(captcha_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Сменить картинку", command=self.captcha.reset, font=("Arial", 9)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="Проверить капчу", command=self.check_captcha, font=("Arial", 9)).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)
        
        self.btn_login = tk.Button(main_container, text="Войти в аккаунт", command=self.login,
                                    bg="#e0e0e0", font=("Arial", 12, "bold"), height=2)
        self.btn_login.pack(fill=tk.X, pady=(15, 0))
        
        self.root.bind("<Return>", lambda e: self.login())
    
    def check_captcha(self):
        if self.captcha.is_solved():
            messagebox.showinfo("Капча", "Капча пройдена успешно!")
        else:
            messagebox.showwarning("Капча", "Фрагменты расставлены неверно. Попробуйте ещё раз.")
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Предупреждение", "Поля «Логин» и «Пароль» обязательны для заполнения.")
            return
        
        user = self.db.get_user(username)
        
        if user and user[3] and user[2] != "Администратор":
            messagebox.showerror("Доступ запрещён", "Вы заблокированы. Обратитесь к администратору.")
            return
        
        if not self.captcha.is_solved():
            success, status, failures = self.db.increment_captcha_failure(username)
            
            if status == "blocked":
                messagebox.showerror("Блокировка", "Вы 3 раза неверно собрали капчу.\nУчетная запись заблокирована. Обратитесь к администратору.")
                self.captcha.reset()
                return
            elif status == "captcha_failed":
                remaining = 3 - failures
                messagebox.showerror("Ошибка", f"Капча собрана неверно.\nОсталось попыток: {remaining}")
                self.captcha.reset()
                return
            elif status == "admin_never_blocked":
                messagebox.showerror("Ошибка", "Капча собрана неверно. Попробуйте еще раз.")
                self.captcha.reset()
                return
            
            self.captcha.reset()
            return
        
        self.db.reset_captcha_failures(username)
        
        auth_result, status = self.db.authenticate(username, password)
        
        if status == "success":
            messagebox.showinfo("Успех", "Вы успешно авторизовались.")
            self.on_success(auth_result)
        elif status == "blocked":
            messagebox.showerror("Доступ запрещён", "Вы заблокированы. Обратитесь к администратору.")
        elif status == "blocked_now":
            messagebox.showerror("Ошибка", "Вы ввели неверный пароль 3 раза.\nУчетная запись заблокирована. Обратитесь к администратору.")
        elif status == "user_not_found":
            messagebox.showerror("Ошибка входа", "Вы ввели неверный логин или пароль.")
        else:
            user_data = self.db.get_user(username)
            if user_data:
                attempts_left = 3 - user_data[4]
                if attempts_left > 0:
                    messagebox.showerror("Ошибка", f"Вы ввели неверный пароль.\nОсталось попыток: {attempts_left}")
                else:
                    messagebox.showerror("Ошибка", "Вы ввели неверный пароль 3 раза.\nУчетная запись заблокирована. Обратитесь к администратору.")
            else:
                messagebox.showerror("Ошибка", "Вы ввели неверный логин или пароль.")
    
    def close(self):
        self.db.close()
