import tkinter as tk
from tkinter import messagebox
import bluetooth
from bluetooth_connection_manager import BluetoothClient
from display_manager import DisplayManager

class BluetoothApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador Bluetooth")
        self.root.geometry("400x300")

        self.manager = BluetoothClient()  # Você pode alternar entre Server e Client
        self.display_manager = DisplayManager(self.root)

        self.device_list = tk.Listbox(self.root, width=50, height=10)
        self.device_list.pack(pady=20)

        self.search_button = tk.Button(self.root, text="Buscar Dispositivos", command=self.search_devices)
        self.search_button.pack(pady=10)

        self.connect_button = tk.Button(self.root, text="Conectar ao Dispositivo", command=self.connect_device)
        self.connect_button.pack(pady=10)

    def search_devices(self):
        self.device_list.delete(0, tk.END)
        devices = bluetooth.discover_devices(lookup_names=True)
        if devices:
            for addr, name in devices:
                self.device_list.insert(tk.END, f"{name} - {addr}")
        else:
            messagebox.showinfo("Busca Bluetooth", "Nenhum dispositivo encontrado.")

    def connect_device(self):
        selected_device = self.device_list.curselection()
        if selected_device:
            device_info = self.device_list.get(selected_device)
            device_address = device_info.split(" - ")[1]
            self.manager.connect(device_address)
            messagebox.showinfo("Conexão", f"Conectado ao dispositivo {device_info}")
        else:
            messagebox.showwarning("Seleção de Dispositivo", "Por favor, selecione um dispositivo.")
