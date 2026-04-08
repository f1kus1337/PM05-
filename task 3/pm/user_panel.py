import tkinter as tk
from tkinter import messagebox

class UserPanel:
    def __init__(self, root, user_data, on_logout):
        self.root = root
        self.user_data = user_data
        self.on_logout = on_logout
        self.setup_ui()
    
    def setup_ui(self):
        self.root.title(f"Молочный комбинат Полесье — Рабочий стол")
        self.root.geometry("400x300")
        self.root.minsize(300, 200)
        
        main_frame = tk.Frame(self.root, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text=f"Добро пожаловать, {self.user_data['username']}!", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Label(main_frame, text=f"Ваша роль: {self.user_data['role']}", 
                 font=("Arial", 11)).pack(pady=10)
        
        tk.Button(main_frame, text="Выйти из системы", command=self.logout,
                  bg="#f44336", fg="white", font=("Arial", 11), padx=20, pady=5).pack(pady=30)
    
    def logout(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти?"):
            self.on_logout()
