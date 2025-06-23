import tkinter as tk
from tkinter import messagebox
import json # For json.dumps
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

        self.notification_listbox = tk.Listbox(self, width=70, height=10, exportselection=False)
        self.notification_listbox.pack(pady=5)

        self.reply_entry = tk.Entry(self, width=50)
        self.reply_entry.pack(pady=5)

        self.reply_button = tk.Button(self, text="Reply to Selected", command=self.send_reply)
        self.reply_button.pack(pady=5)

        self.notifications_data = [] # To store {'key': key, 'app_name': app, 'content': content, 'icon_base64': icon_b64}

        # O connection_manager é passado pelo construtor, já configurado com callbacks
        self.connection_manager = connection_manager
        if self.connection_manager:
            # Tenta conectar automaticamente a dispositivos pareados
            self.connection_manager.auto_connect_to_paired_devices()
        else:
            self.update_status("Error: Connection Manager not provided.")


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
        Callback para o BluetoothConnectionManager. Chamado quando uma nova notificação é recebida.
        Exibe a notificação na GUI e armazena seus dados para futuras respostas.
        """
        display_text = f"[{app_name}] {content}"
        # Adiciona à Listbox para visualização
        self.notification_listbox.insert(tk.END, display_text)
        # Armazena os dados completos, incluindo a chave
        self.notifications_data.append({
            "key": key,
            "app_name": app_name,
            "content": content,
            "icon_base64": icon_base64, # GUI pode usar isso para exibir ícone se desejado
            "listbox_text": display_text
        })
        print(f"GUI: Received notification '{key}' from '{app_name}'. Stored.")
        # Optionally, scroll to the new notification
        self.notification_listbox.see(tk.END)

    def send_reply(self):
        """
        Prepara e envia uma resposta para a notificação selecionada na Listbox.
        (A lógica de envio do JSON será completada na Etapa 3 do plano)
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

        if 0 <= selected_index < len(self.notifications_data):
            notification_to_reply = self.notifications_data[selected_index]
            key_to_reply = notification_to_reply["key"]

            print(f"GUI: Preparing to send reply to key '{key_to_reply}' with text: '{reply_text}'")

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
            if self.connection_manager and self.connection_manager.bluetooth_socket and self.connection_manager.output_stream:
                try:
                    self.connection_manager.send_message(json_payload)
                    self.reply_entry.delete(0, tk.END)
                    messagebox.showinfo("Reply Sent", f"Reply sent for notification key {key_to_reply}.")
                except Exception as e:
                    messagebox.showerror("Send Error", f"Failed to send reply: {e}")
            else:
                messagebox.showerror("Connection Error", "Not connected or output stream unavailable. Cannot send reply.")
        else:
            messagebox.showerror("Reply Error", "Selected notification data not found. Index out of range.")


def run_gui():
    app = BluetoothGUI(None)  # Pass None initially, connection_manager is created inside

    # Criar e configurar o BluetoothConnectionManager
    # Precisamos de uma instância de app para os callbacks
    service_uuid = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    connection_manager = BluetoothConnectionManager(
        uuid=service_uuid,
        status_callback=app.update_status, # GUI method
        notification_callback=app.handle_incoming_notification # GUI method
    )
    app.connection_manager = connection_manager # Assign the configured manager to the app instance

    # Agora que o manager está configurado e atribuído, podemos chamar auto_connect
    if app.connection_manager:
        app.connection_manager.auto_connect_to_paired_devices()
    else: # Deve ser redundante se a lógica acima estiver correta
        app.update_status("Critical Error: Connection Manager could not be initialized.")

    app.mainloop()

if __name__ == "__main__":
    run_gui()
