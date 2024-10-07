import asyncio
import tkinter as tk
from tkinter import messagebox
from bleak import BleakScanner
from bluetooth_connection_manager import BluetoothConnectionManager
from uuid import UUID

class BluetoothGUI(tk.Tk):
    def __init__(self, connection_manager):
        super().__init__()
        self.title("Bluetooth Scanner")
        self.geometry("400x300")

        # Label de Status
        self.status_label = tk.Label(self, text="Scanning for devices...", font=("Helvetica", 12))
        self.status_label.pack(pady=10)

        # Lista para mostrar os dispositivos encontrados
        self.device_listbox = tk.Listbox(self, width=50, height=10)
        self.device_listbox.pack(pady=10)

        # Botão para conectar ao dispositivo selecionado
        self.connect_button = tk.Button(self, text="Connect", command=self.connect_to_device)
        self.connect_button.pack(pady=10)

        # Gerenciador de conexão Bluetooth
        self.connection_manager = connection_manager

        # Inicia o scan de dispositivos Bluetooth ao abrir
        self.after(100, self.start_scan)

    def start_scan(self):
        # Inicia o scan em um loop de eventos Tkinter
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        # Realiza o scan de dispositivos Bluetooth e exibe na interface
        self.status_label.config(text="Scanning...")
        devices = await self.connection_manager.scan_devices()

        if not devices:
            self.status_label.config(text="No devices found.")
        else:
            self.status_label.config(text="Select a device to connect.")
            self.device_listbox.delete(0, tk.END)  # Limpa a lista
            for idx, device in enumerate(devices):
                self.device_listbox.insert(tk.END, f"{idx}: {device.name} - {device.address}")

    def connect_to_device(self):
        # Tenta conectar ao dispositivo selecionado na lista
        selected_idx = self.device_listbox.curselection()
        if selected_idx:
            device_index = int(self.device_listbox.get(selected_idx).split(":")[0])
            asyncio.run(self.connection_manager.select_device_and_connect(device_index))
        else:
            messagebox.showwarning("Selection Error", "Please select a device from the list.")

# Função principal para executar a GUI
def run_gui():
    # Definir o UUID para o serviço Bluetooth (substitua pelo correto)
    service_uuid = UUID("12345678-1234-5678-1234-56789abcdef0")
    connection_manager = BluetoothConnectionManager(service_uuid)

    # Inicializa a interface gráfica
    app = BluetoothGUI(connection_manager)
    app.mainloop()

if __name__ == "__main__":
    run_gui()
