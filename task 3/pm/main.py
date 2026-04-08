import sys
import os
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(__file__))

from database import Database
from auth import LoginForm
from admin_panel import AdminPanel
from user_panel import UserPanel

class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.current_user = None
        self.current_view = None
        
        self.root.withdraw()

        try:
            self.db = Database()
        except Exception as e:
            messagebox.showerror(
                title="Ошибка инициализации",
                message=f"Не удалось подключиться к базе данных.\n\n{e}"
            )
            self.root.destroy()
            return
        
        self.root.deiconify()
        self.show_login()
    
    def show_login(self):
        self.clear_window()
        self.login_form = LoginForm(self.root, self.on_login_success)
    
    def on_login_success(self, user_data):
        self.current_user = user_data
        self.clear_window()
        
        if user_data["role"] == "Администратор":
            self.current_view = AdminPanel(self.root, user_data, self.on_logout)
        else:
            self.current_view = UserPanel(self.root, user_data, self.on_logout)
    
    def on_logout(self):
        self.current_user = None
        self.current_view = None
        self.show_login()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = Application()
    app.run()
