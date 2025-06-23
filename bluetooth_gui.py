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

        # Inicializa o gerenciador de conexão Bluetooth com o callback de atualização de status
        self.connection_manager = BluetoothConnectionManager(
            uuid=UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6"),
            status_callback=self.update_status
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
        Callback from BluetoothConnectionManager for notifications with a 'key'.
        Creates a new Toplevel window to allow replying to the notification.
        """
        print(f"GUI: handle_incoming_notification for key: {key}")
        reply_window = tk.Toplevel(self)
        reply_window.title(f"Reply to {app_name}")
        reply_window.geometry("400x200")
        reply_window.transient(self) # Makes it behave like a dialog of the main window
        reply_window.grab_set() # Modal behavior

        # Display notification info
        info_text = f"Replying to:\nApp: {app_name}\nMessage: {content}"
        # Use a Message widget for potentially multi-line content
        info_label = tk.Message(reply_window, text=info_text, width=380, anchor="w", justify="left")
        info_label.pack(pady=10, padx=10, expand=True, fill=tk.X)

        reply_entry = tk.Entry(reply_window, width=50)
        reply_entry.pack(pady=5, padx=10)
        reply_entry.focus_set() # Set focus to the entry field

        # Send button
        send_button = tk.Button(
            reply_window,
            text="Send Reply",
            command=lambda k=key, e=reply_entry, rw=reply_window: self.send_reply_from_toplevel(k, e, rw)
        )
        send_button.pack(pady=10)

        # Bind Enter key to send_button's command
        reply_entry.bind("<Return>", lambda event, k=key, e=reply_entry, rw=reply_window: self.send_reply_from_toplevel(k, e, rw))

        # Center the Toplevel window (optional, but good UX)
        reply_window.update_idletasks() # Ensure window dimensions are calculated
        x = self.winfo_x() + (self.winfo_width() // 2) - (reply_window.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (reply_window.winfo_height() // 2)
        reply_window.geometry(f"+{x}+{y}")


    def send_reply_from_toplevel(self, key, entry_widget, toplevel_window):
        """
        Sends the reply constructed in a Toplevel window.
        """
        reply_text = entry_widget.get()
        if not reply_text.strip():
            messagebox.showwarning("Empty Reply", "Reply text cannot be empty.", parent=toplevel_window)
            entry_widget.focus_set()
            return

        print(f"GUI: Sending reply for key '{key}': {reply_text}")
        reply_payload = {"key": key, "reply": reply_text}

        try:
            json_payload = json.dumps(reply_payload)
        except TypeError as e:
            messagebox.showerror("JSON Error", f"Could not construct reply JSON: {e}", parent=toplevel_window)
            return

        if self.connection_manager and self.connection_manager.bluetooth_socket and self.connection_manager.output_stream:
            try:
                self.connection_manager.send_message(json_payload)
                messagebox.showinfo("Reply Sent", "Reply sent successfully!", parent=toplevel_window)
                toplevel_window.destroy()
            except Exception as e:
                messagebox.showerror("Send Error", f"Failed to send reply: {e}", parent=toplevel_window)
                toplevel_window.destroy() # Also close on error after showing message
        else:
            messagebox.showerror("Connection Error", "Not connected or output stream unavailable. Cannot send reply.", parent=toplevel_window)
            toplevel_window.destroy() # Also close on error


def run_gui():
    # This function will be updated in the next step to correctly pass the callback
    app = BluetoothGUI(None)  # Pass None initially

    service_uuid = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    connection_manager = BluetoothConnectionManager(
        uuid=service_uuid,
        status_callback=app.update_status,
        notification_callback=app.handle_incoming_notification # This is key
    )
    app.connection_manager = connection_manager # Assign the configured manager

    if app.connection_manager:
        app.connection_manager.auto_connect_to_paired_devices()

    app.mainloop()

if __name__ == "__main__":
    run_gui()
