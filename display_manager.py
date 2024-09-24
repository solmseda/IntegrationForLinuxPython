import tkinter as tk
from tkinter import messagebox

class DisplayManager:
    def __init__(self, root):
        self.root = root

    def show_notification(self, notification_data):
        messagebox.showinfo("Notificação", f"App: {notification_data.app_name}\nConteúdo: {notification_data.content}")

    def update_clipboard_data(self, clipboard_data):
        print(f"Dados da área de transferência: {clipboard_data.content}")
