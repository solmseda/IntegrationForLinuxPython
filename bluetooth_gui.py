import tkinter as tk
from tkinter import messagebox
import threading # Added for running send_message in a separate thread
from bluetooth_connection_manager import BluetoothConnectionManager
from uuid import UUID

from Notification_Data import NotificationData # Added for type hinting
# For type hinting, you might need: from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     pass # Already have NotificationData

class NotificationReplyWindow(tk.Toplevel):
    def __init__(self, master, notification_data, reply_callback):
        """
        Initializes the notification reply window.

        Args:
            master: The parent window (BluetoothGUI instance).
            notification_data: NotificationData object with notification details.
            reply_callback: Function to call when "Send Reply" is pressed.
                            Accepts (action_id, reply_text).
        """
        super().__init__(master)
        self.notification_data = notification_data
        self.reply_callback = reply_callback

        self.title(f"Reply to {self.notification_data.app_name}")
        self.geometry("400x200") # Default size, can be adjusted

        # Display Notification Info
        app_name_label = tk.Label(self, text=f"From: {self.notification_data.app_name}", font=("Helvetica", 12, "bold"))
        app_name_label.pack(pady=(10, 0))

        content_frame = tk.Frame(self)
        content_frame.pack(pady=5, padx=10, fill="x", expand=True)

        content_label = tk.Label(content_frame, text="Notification:", font=("Helvetica", 10, "italic"))
        content_label.pack(anchor="w")

        # Using Message widget for potentially multi-line content
        notification_content_message = tk.Message(content_frame, text=self.notification_data.content, width=380)
        notification_content_message.pack(anchor="w", fill="x", expand=True)

        # Reply Entry
        reply_label = tk.Label(self, text="Your Reply:", font=("Helvetica", 10))
        reply_label.pack(pady=(10,0), anchor="w", padx=10)

        self.reply_entry = tk.Entry(self, width=50)
        self.reply_entry.pack(pady=5, padx=10, fill="x", expand=True)
        self.reply_entry.focus_set() # Set focus to reply entry

        # Send Button
        send_button = tk.Button(self, text="Send Reply", command=self._send_reply)
        send_button.pack(pady=10)

    def _send_reply(self):
        reply_text = self.reply_entry.get().strip()
        if reply_text:
            self.reply_callback(self.notification_data.reply_action_id, reply_text)
            self.destroy() # Close the window after sending
        else:
            # Optional: Show a warning if the reply is empty
            messagebox.showwarning("Empty Reply", "Please enter a message to reply.", parent=self)


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

        # Seção para dispositivos pareados
        self.paired_label = tk.Label(self, text="Dispositivos Pareados", font=("Helvetica", 12))
        self.paired_label.pack(pady=10)

        self.paired_listbox = tk.Listbox(self, width=50, height=10)
        self.paired_listbox.pack(pady=10)

        # Inicializa o gerenciador de conexão Bluetooth com o callback de atualização de status
        self.connection_manager = BluetoothConnectionManager(
            uuid=UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6"),
            status_callback=self.update_status
        )

        # Mostra dispositivos pareados ao iniciar a aplicação
        self.show_paired_devices()

        # Tenta conectar automaticamente a dispositivos pareados
        self.connection_manager.auto_connect_to_paired_devices()

    def _send_message_thread_target(self, message: str):
        """
        Target function for the sending thread.
        This runs the blocking send_message call.
        """
        try:
            # Assuming self.connection_manager.send_message is synchronous and blocking
            self.connection_manager.send_message(message)
            # Success feedback should ideally be done on the main thread
            # For simplicity, we can print here or use self.after to schedule a GUI update
            print(f"Thread: Message '{message}' sent successfully.")
            # To update GUI from thread: self.master.after(0, lambda: self.master.update_status("Reply sent."))
            # However, self.master is not defined here. BluetoothGUI is the master.
            self.after(0, lambda: self.update_status(f"Reply initiated: {message}")) # Update status on main thread
        except Exception as e:
            # Log error, and potentially use self.after to show error on GUI
            print(f"Thread: Error sending message '{message}': {e}")
            self.after(0, lambda: messagebox.showerror("Bluetooth Send Error", f"Failed to send reply in background: {e}", parent=self))
            self.after(0, lambda: self.update_status(f"Error sending reply: {e}"))


    def show_reply_window(self, notification_data: NotificationData):
        """Creates and shows a NotificationReplyWindow."""
        reply_win = NotificationReplyWindow(self, notification_data, self.send_bluetooth_reply)
        reply_win.grab_set() # Make the reply window modal

    def send_bluetooth_reply(self, action_id: str, reply_text: str):
        """
        Sends the reply message via the Bluetooth connection manager in a separate thread.
        """
        print(f"GUI: Preparing to send reply. Action ID: {action_id}, Message: {reply_text}")

        if not self.connection_manager or not self.connection_manager.is_connected():
            messagebox.showerror("Bluetooth Error", "Not connected to any device. Cannot send reply.", parent=self)
            self.update_status("Error: Not connected. Cannot send reply.")
            return

        formatted_message_to_send = f"reply:{action_id}|{reply_text}"

        try:
            thread = threading.Thread(target=self._send_message_thread_target, args=(formatted_message_to_send,))
            thread.daemon = True # Allow main program to exit even if threads are running
            thread.start()

            # Optimistic success message: GUI part is done. Actual send is in thread.
            messagebox.showinfo("Reply Sending", f"Reply process for '{reply_text}' initiated.", parent=self)
            self.update_status(f"Reply initiation for action ID '{action_id}' started.")

        except Exception as e: # Catch errors related to thread creation itself
            print(f"Error creating send thread: {e}")
            messagebox.showerror("Threading Error", f"Failed to start send process: {e}", parent=self)
            self.update_status(f"Error: Failed to start send process ({e}).")

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


def run_gui():
    service_uuid = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    connection_manager = BluetoothConnectionManager(service_uuid)

    app = BluetoothGUI(connection_manager)
    app.mainloop()

if __name__ == "__main__":
    run_gui()
