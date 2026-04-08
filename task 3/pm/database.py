import psycopg2
import hashlib
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

ROLES = ["Администратор", "Пользователь"]
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()
        self.init_db()
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.conn.cursor()
            print("Подключено к PostgreSQL")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            raise
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                role_id SERIAL PRIMARY KEY,
                role_name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                is_blocked BOOLEAN DEFAULT FALSE,
                failed_attempts INTEGER DEFAULT 0,
                captcha_failures INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role) REFERENCES user_roles(role_name)
            )
        """)
        self.conn.commit()
        
        for role in ROLES:
            self.cursor.execute(
                "INSERT INTO user_roles (role_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (role,)
            )
        
        self.cursor.execute("SELECT 1 FROM users WHERE username = %s", (ADMIN_USERNAME,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role, is_blocked, failed_attempts, captcha_failures) "
                "VALUES (%s, %s, %s, false, 0, 0)",
                (ADMIN_USERNAME, self.hash_password(ADMIN_PASSWORD), "Администратор")
            )
            print(f"Создан администратор: логин='{ADMIN_USERNAME}', пароль='{ADMIN_PASSWORD}'")
        
        self.cursor.execute("SELECT 1 FROM users WHERE username = %s", ("user",))
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role, is_blocked, failed_attempts, captcha_failures) "
                "VALUES (%s, %s, %s, false, 0, 0)",
                ("user", self.hash_password("user123"), "Пользователь")
            )
            print("Создан тестовый пользователь: логин='user', пароль='user123'")
        
        self.conn.commit()
        print("База данных инициализирована")
    
    def authenticate(self, username, password):
        pwd_hash = self.hash_password(password)
        
        self.cursor.execute(
            "SELECT user_id, username, password_hash, role, is_blocked, failed_attempts, captcha_failures "
            "FROM users WHERE username = %s",
            (username,)
        )
        user = self.cursor.fetchone()
        
        if not user:
            return None, "user_not_found"
        
        user_id, db_username, db_password_hash, role, is_blocked, failed_attempts, captcha_failures = user
        
        if is_blocked and role != "Администратор":
            return None, "blocked"
        
        if pwd_hash == db_password_hash:
            self.cursor.execute(
                "UPDATE users SET failed_attempts = 0 WHERE username = %s",
                (username,)
            )
            self.conn.commit()
            return {"user_id": user_id, "username": db_username, "role": role}, "success"
        else:
            if role != "Администратор":
                new_attempts = failed_attempts + 1
                self.cursor.execute(
                    "UPDATE users SET failed_attempts = %s WHERE username = %s",
                    (new_attempts, username)
                )
                if new_attempts >= 3:
                    self.cursor.execute(
                        "UPDATE users SET is_blocked = TRUE WHERE username = %s",
                        (username,)
                    )
                    self.conn.commit()
                    return None, "blocked_now"
            self.conn.commit()
            return None, "invalid_password"
    
    def increment_captcha_failure(self, username):
        self.cursor.execute(
            "SELECT user_id, role, is_blocked, captcha_failures FROM users WHERE username = %s",
            (username,)
        )
        user = self.cursor.fetchone()
        
        if not user:
            return False, "user_not_found", 0
        
        user_id, role, is_blocked, captcha_failures = user
        
        if role == "Администратор":
            return False, "admin_never_blocked", captcha_failures + 1
        
        if is_blocked:
            return False, "already_blocked", captcha_failures
        
        new_failures = captcha_failures + 1
        self.cursor.execute(
            "UPDATE users SET captcha_failures = %s WHERE username = %s",
            (new_failures, username)
        )
        
        if new_failures >= 3:
            self.cursor.execute(
                "UPDATE users SET is_blocked = TRUE WHERE username = %s",
                (username,)
            )
            self.conn.commit()
            return True, "blocked", new_failures
        
        self.conn.commit()
        return True, "captcha_failed", new_failures
    
    def reset_captcha_failures(self, username):
        self.cursor.execute(
            "UPDATE users SET captcha_failures = 0 WHERE username = %s",
            (username,)
        )
        self.conn.commit()
    
    def get_user(self, username):
        self.cursor.execute(
            "SELECT user_id, username, role, is_blocked, failed_attempts, captcha_failures FROM users WHERE username = %s",
            (username,)
        )
        return self.cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        self.cursor.execute(
            "SELECT user_id, username, role, is_blocked, failed_attempts, captcha_failures FROM users WHERE user_id = %s",
            (user_id,)
        )
        return self.cursor.fetchone()
    
    def get_all_users(self):
        self.cursor.execute(
            "SELECT user_id, username, role, is_blocked, failed_attempts, captcha_failures, created_at FROM users ORDER BY user_id"
        )
        return self.cursor.fetchall()
    
    def get_roles(self):
        self.cursor.execute("SELECT role_name FROM user_roles")
        return [row[0] for row in self.cursor.fetchall()]
    
    def user_exists(self, username):
        self.cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        return self.cursor.fetchone() is not None
    
    def add_user(self, username, password, role, is_blocked=False):
        try:
            pwd_hash = self.hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role, is_blocked, failed_attempts, captcha_failures) "
                "VALUES (%s, %s, %s, %s, 0, 0)",
                (username, pwd_hash, role, is_blocked)
            )
            self.conn.commit()
            return True, "Пользователь успешно добавлен"
        except psycopg2.Error as e:
            self.conn.rollback()
            if "duplicate key" in str(e):
                return False, "Пользователь с таким логином уже существует"
            return False, f"Ошибка: {e}"
    
    def update_user(self, user_id, username, password, role, is_blocked):
        try:
            pwd_hash = self.hash_password(password)
            self.cursor.execute(
                "UPDATE users SET username = %s, password_hash = %s, role = %s, is_blocked = %s, "
                "updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                (username, pwd_hash, role, is_blocked, user_id)
            )
            self.conn.commit()
            return True, "Пользователь успешно обновлен"
        except Exception as e:
            self.conn.rollback()
            return False, f"Ошибка: {e}"
    
    def delete_user(self, user_id):
        try:
            self.cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            self.conn.commit()
            return True, "Пользователь успешно удален"
        except Exception as e:
            self.conn.rollback()
            return False, f"Ошибка: {e}"
    
    def unblock_user(self, user_id):
        self.cursor.execute(
            "UPDATE users SET is_blocked = FALSE, failed_attempts = 0, captcha_failures = 0 WHERE user_id = %s",
            (user_id,)
        )
        self.conn.commit()
        return True, "Пользователь разблокирован"
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
