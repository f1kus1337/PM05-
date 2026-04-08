import tkinter as tk
from tkinter import ttk, messagebox
from database import Database


class AdminPanel:
    def __init__(self, root, user_data, on_logout):
        self.root = root
        self.user_data = user_data
        self.on_logout = on_logout
        self.db = Database()
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        self.root.title("Молочный комбинат Полесье — Администратор")
        self.root.geometry("650x500")
        self.root.minsize(600, 400)

        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        columns = ("id", "username", "role", "blocked")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Логин")
        self.tree.heading("role", text="Роль")
        self.tree.heading("blocked", text="Заблокирован")

        self.tree.column("id", width=50)
        self.tree.column("username", width=200)
        self.tree.column("role", width=150)
        self.tree.column("blocked", width=100)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="w")

        tk.Button(btn_frame, text="Добавить", width=12, command=self.add_user_dialog).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Редактировать", width=14, command=self.edit_user_dialog).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Обновить", width=10, command=self.load_users).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Разблокировать", width=12, command=self.unblock_user_dialog).pack(side=tk.LEFT,
                                                                                                     padx=4)

        tk.Button(main_frame, text="Выйти", command=self.logout, bg="#f44336", fg="white").grid(row=2, column=0,
                                                                                                columnspan=2, pady=10)

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            users = self.db.get_all_users()
            for user in users:
                user_id, username, role, is_blocked, failed_attempts, captcha_failures, created_at = user
                self.tree.insert("", "end", values=(
                    user_id, username, role,
                    "Да" if is_blocked else "Нет"
                ))
            print(f"Загружено {len(users)} пользователей")
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e))

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите пользователя в списке.")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def add_user_dialog(self):
        UserDialog(self.root, self.db, self.load_users)

    def edit_user_dialog(self):
        user_id = self.get_selected_id()
        if user_id is None:
            return

        sel = self.tree.selection()[0]
        values = self.tree.item(sel)["values"]
        # Явно преобразуем в строки для корректного сравнения
        username = str(values[1])  # Логин
        role = str(values[2])  # Роль
        blocked = values[3] == "Да"

        UserDialog(self.root, self.db, self.load_users, user_id, username, role, blocked)

    def unblock_user_dialog(self):
        user_id = self.get_selected_id()
        if user_id is None:
            return

        sel = self.tree.selection()[0]
        values = self.tree.item(sel)["values"]
        username, blocked = values[1], values[3]

        if blocked == "Нет":
            messagebox.showinfo("Информация", f"Пользователь '{username}' уже активен.")
            return

        if messagebox.askyesno("Подтверждение", f"Разблокировать пользователя '{username}'?"):
            success, msg = self.db.unblock_user(user_id)
            if success:
                messagebox.showinfo("Успех", f"Пользователь '{username}' разблокирован.")
                self.load_users()
            else:
                messagebox.showerror("Ошибка", msg)

    def logout(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти?"):
            self.db.close()
            self.on_logout()


class UserDialog:
    def __init__(self, parent, db, on_save, user_id=None, username="", role="", is_blocked=False):
        self.db = db
        self.user_id = user_id
        self.on_save = on_save
        # Гарантируем, что original_username будет строкой
        self.original_username = str(username) if username else ""

        top = tk.Toplevel(parent)
        self.top = top
        top.title("Добавление пользователя" if user_id is None else "Редактирование пользователя")
        top.resizable(False, False)
        top.grab_set()

        frame = tk.Frame(top, padx=16, pady=16)
        frame.pack()
        frame.columnconfigure(1, weight=1)

        # Логин
        tk.Label(frame, text="Логин:").grid(row=0, column=0, sticky="w", pady=4)
        self.username_var = tk.StringVar(value=str(username))
        self.username_entry = tk.Entry(frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=0, column=1, pady=4)

        # При редактировании можно запретить изменение логина (опционально)
        if user_id is not None:
            self.username_entry.config(state="readonly", readonlybackground="#f0f0f0")
            # Но сохраняем оригинальное значение для сравнения
            self.original_username = str(username)

        # Пароль
        tk.Label(frame, text="Пароль:").grid(row=1, column=0, sticky="w", pady=4)
        self.password_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.password_var, show="*", width=30).grid(row=1, column=1, pady=4)


        # Роль
        tk.Label(frame, text="Роль:").grid(row=3, column=0, sticky="w", pady=4)
        roles = self.db.get_roles()
        self.role_var = tk.StringVar(value=role if role in roles else (roles[0] if roles else ""))
        ttk.Combobox(frame, textvariable=self.role_var, values=roles, state="readonly", width=27) \
            .grid(row=3, column=1, pady=4)

        # Блокировка
        self.blocked_var = tk.BooleanVar(value=is_blocked)
        tk.Checkbutton(frame, text="Заблокирован", variable=self.blocked_var) \
            .grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        # Кнопки
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        tk.Button(btn_frame, text="Сохранить", width=12, command=lambda: self.save()) \
            .pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", width=12, command=top.destroy) \
            .pack(side=tk.LEFT, padx=5)

    def save(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        role = self.role_var.get()
        is_blocked = self.blocked_var.get()

        # Валидация
        if not username:
            messagebox.showwarning("Ошибка", "Поле «Логин» обязательно.", parent=self.top)
            return

        if self.user_id is None and not password:
            messagebox.showwarning("Ошибка", "Поле «Пароль» обязательно для нового пользователя.", parent=self.top)
            return

        try:
            if self.user_id is None:
                if self.db.user_exists(username):
                    messagebox.showwarning(
                        "Ошибка",
                        f"Пользователь «{username}» уже существует.\n\n"
                        f"Используйте кнопку «Редактировать» для изменения существующего пользователя.",
                        parent=self.top
                    )
                    return
                success, msg = self.db.add_user(username, password, role, is_blocked)
            else:

                if username != self.original_username:
                    if self.db.user_exists(username):
                        messagebox.showwarning(
                            "Ошибка",
                            f"Пользователь «{username}» уже существует.\n\n"
                            f"Выберите другой логин.",
                            parent=self.top
                        )
                        return
                success, msg = self.db.update_user(self.user_id, username, password, role, is_blocked)

            if success:
                messagebox.showinfo("Успех", "Данные сохранены.", parent=self.top)
                self.top.destroy()
                self.on_save()
            else:
                messagebox.showerror("Ошибка", msg, parent=self.top)
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self.top)