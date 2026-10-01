import json
import os
import openpyxl

ACCOUNTS_FILE = "data/accounts.json"

class AccountManager:
    def __init__(self):
        self.accounts = []
        self.load_accounts()

    def load_accounts(self):
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    self.accounts = json.load(f)
            except Exception as e:
                print(f"Lỗi tải file tài khoản: {e}")
                self.accounts = []
        else:
            self.accounts = []

    def save_accounts(self):
        os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.accounts, f, indent=4)

    def add_from_text(self, text):
        lines = text.strip().split('\n')
        count = 0
        for line in lines:
            parts = line.split('\t') # Tách bằng phím tab
            if len(parts) >= 2:
                email = parts[0].strip()
                password = parts[1].strip()
                # Kiểm tra trùng lặp
                if not any(acc['email'] == email for acc in self.accounts):
                    self.accounts.append({'email': email, 'password': password, 'status': 'Ready'})
                    count += 1
        self.save_accounts()
        return count

    def add_from_excel(self, file_path):
        count = 0
        try:
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                if len(row) >= 2 and row[0] and row[1]:
                    email = str(row[0]).strip()
                    password = str(row[1]).strip()
                    if not any(acc['email'] == email for acc in self.accounts):
                        self.accounts.append({'email': email, 'password': password, 'status': 'Ready'})
                        count += 1
            self.save_accounts()
        except Exception as e:
            print(f"Lỗi đọc file excel: {e}")
        return count

    def get_accounts(self):
        return self.accounts

    def get_pending_accounts(self):
        return [acc for acc in self.accounts if acc.get('status') == 'Ready']

    def update_status(self, email, status):
        for acc in self.accounts:
            if acc['email'] == email:
                acc['status'] = status
                break
        self.save_accounts()

    def clear_accounts(self):
        self.accounts = []
        self.save_accounts()
