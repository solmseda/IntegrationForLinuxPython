import tkinter as tk
from tkinter import messagebox
from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador Bluetooth")
        self.root.geometry("400x300")

        # Instanciando o gerenciador de conexões Bluetooth
        self.manager = BluetoothConnectionManager()
        
        # Lista de dispositivos encontrados
        self.device_list = tk.Listbox(self.root, width=50, height=10)
        self.device_list.pack(pady=20)

        # Botão para buscar dispositivos
        self.search_button = tk.Button(self.root, text="Buscar Dispositivos", command=self.search_devices)
        self.search_button.pack(pady=10)

        # Botão para conectar ao dispositivo selecionado
        self.connect_button = tk.Button(self.root, text="Conectar ao Dispositivo", command=self.connect_device)
        self.connect_button.pack(pady=10)

    # Função para buscar dispositivos e atualizar a lista
    def search_devices(self):
        self.device_list.delete(0, tk.END)  # Limpa a lista
        devices = self.manager.discover_devices()  # Busca dispositivos
        if devices:
            for addr, name in devices:
                self.device_list.insert(tk.END, f"{name} - {addr}")
        else:
            messagebox.showinfo("Busca Bluetooth", "Nenhum dispositivo encontrado.")

    # Função para conectar ao dispositivo selecionado
    def connect_device(self):
        selected_device = self.device_list.curselection()  # Obtém a seleção
        if selected_device:
            device_info = self.device_list.get(selected_device)
            device_address = device_info.split(" - ")[1]  # Extrai o endereço Bluetooth
            try:
                self.manager.connect_to_device(device_address)  # Conecta ao dispositivo
                messagebox.showinfo("Conexão", f"Conectado ao dispositivo {device_info}")
            except Exception as e:
                messagebox.showerror("Erro de Conexão", f"Erro ao conectar: {str(e)}")
        else:
            messagebox.showwarning("Seleção de Dispositivo", "Por favor, selecione um dispositivo.")

# Rodar a interface gráfica
if __name__ == "__main__":
    root = tk.Tk()
    app = BluetoothApp(root)
    root.mainloop()
