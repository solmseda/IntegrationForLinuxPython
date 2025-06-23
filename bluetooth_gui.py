import tkinter as tk
from tkinter import messagebox
import json # Added for json.dumps
from bluetooth_connection_manager import BluetoothConnectionManager
from uuid import UUID

class BluetoothGUI(tk.Tk):
    def __init__(self, connection_manager):
        super().__init__()
        self.title("Integration4Linux")
        self.geometry("800x600")

        # Status label
        self.status_label = tk.Label(self, text="Bem-vindo ao Integration4Linux", font=("Helvetica", 12))
        self.status_label.pack(pady=10)

        # Botão de escaneamento
        self.scan_button = tk.Button(self, text="Scan Devices", command=self.start_scan)
        self.scan_button.pack(pady=10)

        # Listbox para dispositivos descobertos
        self.device_listbox = tk.Listbox(self, width=50, height=10)
        self.device_listbox.pack(pady=10)

        # Botão para conectar
        self.connect_button = tk.Button(self, text="Connect", command=self.connect_to_device)
        self.connect_button.pack(pady=10)

        # --- UI Elements for Notifications and Replies ---
        self.notification_label = tk.Label(self, text="Notifications:", font=("Helvetica", 10))
        self.notification_label.pack(pady=(10,0))

        self.notification_listbox = tk.Listbox(self, width=70, height=10)
        self.notification_listbox.pack(pady=5)

        self.reply_entry = tk.Entry(self, width=50)
        self.reply_entry.pack(pady=5)

        self.reply_button = tk.Button(self, text="Reply to Selected", command=self.send_reply)
        self.reply_button.pack(pady=5)

        self.notifications_data = [] # To store {key, app_name, content}

        # Inicializa o gerenciador de conexão Bluetooth com os callbacks
        self.connection_manager = BluetoothConnectionManager(
            uuid=UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6"),
            status_callback=self.update_status,
            notification_callback=self.handle_incoming_notification # New callback
        )

        # Tenta conectar automaticamente a dispositivos pareados
        self.connection_manager.auto_connect_to_paired_devices()


    def start_scan(self):
        """Realiza uma varredura para encontrar dispositivos Bluetooth próximos."""
        # Limpa a lista de dispositivos descobertos antes de iniciar o novo escaneamento
        self.device_listbox.delete(0, tk.END)
        
        # Atualiza o status para indicar que o escaneamento está em andamento
        self.update_status("Escaneando por dispositivos...")
        
        # Executa o escaneamento de dispositivos Bluetooth
        devices = self.connection_manager.scan_devices()

        # Atualiza o status e preenche a lista com os dispositivos descobertos
        if not devices:
            self.update_status("Nenhum dispositivo encontrado.")
        else:
            self.update_status("Selecione um dispositivo para conectar.")
            for idx, (address, name) in enumerate(devices):
                self.device_listbox.insert(tk.END, f"{idx}: {name or 'Unknown'} ({address})")

    def show_paired_devices(self):
        """Lista dispositivos já pareados na Listbox."""
        paired_devices = self.connection_manager.list_paired_devices()
        self.paired_listbox.delete(0, tk.END)
        
        for idx, (address, name) in enumerate(paired_devices):
            self.paired_listbox.insert(tk.END, f"{idx}: {name or 'Unknown'} ({address})")

    def connect_to_device(self):
        """Conecta ao dispositivo selecionado na lista de dispositivos descobertos."""
        selected_idx = self.device_listbox.curselection()
        if selected_idx:
            device_index = int(self.device_listbox.get(selected_idx).split(":")[0])
            device_address = self.connection_manager.devices[device_index][0]  # Pega o endereço MAC

            if self.connection_manager.start_client(device_address):
                messagebox.showinfo("Connection", f"Conectado ao dispositivo {device_address}")
            else:
                messagebox.showerror("Connection Error", "Não foi possível conectar ao dispositivo.")
        else:
            messagebox.showwarning("Selection Error", "Selecione um dispositivo da lista para conectar.")

    def update_status(self, message):
        """Atualiza a label de status com uma nova mensagem."""
        self.status_label.config(text=message)

    def handle_incoming_notification(self, app_name, content, icon_base64, key):
        """
        Recebe dados da notificação do BluetoothConnectionManager,
        exibe na GUI e armazena para futuras respostas.
        """
        display_text = f"[{app_name}] {content}"
        print(f"GUI received notification: {display_text}, Key: {key}, Icon b64: {'Yes' if icon_base64 else 'No'}")

        # Adiciona à Listbox para visualização
        self.notification_listbox.insert(tk.END, display_text)
        # Armazena os dados completos, incluindo a chave, para referência
        self.notifications_data.append({
            "key": key,
            "app_name": app_name,
            "content": content,
            "icon_base64": icon_base64,
            "listbox_text": display_text # Store to help find it if needed, or use index
        })

        # For now, we don't use plyer here, as the manager might do it if no callback.
        # If we want GUI to control plyer notifications:
        # 1. Manager should not call plyer if callback is present.
        # 2. GUI would handle icon temp file and plyer call here.
        # For simplicity of this step, we rely on the listbox.

    def send_reply(self):
        """
        Envia uma resposta para a notificação selecionada.
        (Implementação do envio do JSON será no próximo passo)
        """
        selected_indices = self.notification_listbox.curselection()
        reply_text = self.reply_entry.get()

        if not selected_indices:
            messagebox.showwarning("Reply Error", "Please select a notification to reply to.")
            return

        if not reply_text.strip():
            messagebox.showwarning("Reply Error", "Reply text cannot be empty.")
            return

        selected_index = selected_indices[0]
        # Ensure the selected_index is valid for notifications_data
        if 0 <= selected_index < len(self.notifications_data):
            notification_to_reply = self.notifications_data[selected_index]
            key_to_reply = notification_to_reply["key"]

            print(f"Attempting to reply to key: {key_to_reply} with text: {reply_text}")

            # Construct the JSON payload
            reply_payload = {
                "key": key_to_reply,
                "reply": reply_text
            }
            try:
                json_payload = json.dumps(reply_payload)
            except TypeError as e:
                messagebox.showerror("Reply Error", f"Could not construct reply JSON: {e}")
                return

            # Send the JSON message via BluetoothConnectionManager
            if self.connection_manager and self.connection_manager.bluetooth_socket:
                # Assuming send_message is not async in the context it's called from GUI
                # If send_message were async, this would need to be handled with asyncio/threading
                self.connection_manager.send_message(json_payload)
                self.reply_entry.delete(0, tk.END)
                messagebox.showinfo("Reply Sent", f"Reply sent for key {key_to_reply}: {reply_text}")
            else:
                messagebox.showerror("Connection Error", "Not connected. Cannot send reply.")
        else:
            messagebox.showerror("Reply Error", "Selected notification data not found. Please try again.")


def run_gui():
    # connection_manager is now created inside BluetoothGUI
    app = BluetoothGUI(None) # Pass None or let BluetoothGUI create its own manager
    app.mainloop()

if __name__ == "__main__":
    run_gui()
