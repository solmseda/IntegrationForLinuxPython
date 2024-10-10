import tkinter as tk
from tkinter import messagebox
from bluetooth_connection_manager import BluetoothConnectionManager
from uuid import UUID

class BluetoothGUI(tk.Tk):
    def __init__(self, connection_manager):
        super().__init__()
        self.title("Bluetooth Scanner")
        self.geometry("800x600")

        self.status_label = tk.Label(self, text="Escaneando por dispositivos...", font=("Helvetica", 12))
        self.status_label.pack(pady=10)

        self.device_listbox = tk.Listbox(self, width=50, height=10)
        self.device_listbox.pack(pady=10)

        self.connect_button = tk.Button(self, text="Connect", command=self.connect_to_device)
        self.connect_button.pack(pady=10)

        self.connection_manager = connection_manager

        self.after(100, self.start_scan)

    def start_scan(self):
        self.status_label.config(text="Escaneando...")
        devices = self.connection_manager.scan_devices()

        if not devices:
            self.status_label.config(text="Nenhum dispositivo encontrado.")
        else:
            self.status_label.config(text="Selecione um dispositivo para conectar.")
            self.device_listbox.delete(0, tk.END)
            for idx, (address, name) in enumerate(devices):
                self.device_listbox.insert(tk.END, f"{idx}: {name or 'Unknown'} ({address})")

    def connect_to_device(self):
        selected_idx = self.device_listbox.curselection()
        if selected_idx:
            device_index = int(self.device_listbox.get(selected_idx).split(":")[0])
            device_address = self.connection_manager.devices[device_index][0]  # Pega o endereço MAC

            if self.connection_manager.start_client(device_address):
                messagebox.showinfo("Connection", f"Conectado ao dispositivo {device_address}")
            else:
                messagebox.showerror("Connection Error", "Não foi possível conectar ao dispositivo.")
        else:
            messagebox.showwarning("Selection Error", "Please select a device from the list.")

def run_gui():
    service_uuid = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    connection_manager = BluetoothConnectionManager(service_uuid)

    app = BluetoothGUI(connection_manager)
    app.mainloop()

if __name__ == "__main__":
    run_gui()
