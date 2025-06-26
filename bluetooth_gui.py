import tkinter as tk
from tkinter import messagebox
from bluetooth_connection_manager import BluetoothConnectionManager
from uuid import UUID
import json

class BluetoothGUI(tk.Tk):
    def __init__(self, manager):
        super().__init__()
        self.title("Integration4Linux")
        self.geometry("600x400")
        self.manager = manager

        # Para rastrear janelas de resposta por 'key'
        self.reply_windows = {}

        # Status
        self.status_label = tk.Label(self, text="Pronto", font=(None,12))
        self.status_label.pack(pady=5)
        # Scan
        tk.Button(self, text="Scan Devices", command=self.start_scan).pack(pady=5)
        # Lista
        self.lb = tk.Listbox(self)
        self.lb.pack(fill='x', padx=10)
        tk.Button(self, text="Connect", command=self.connect_selected).pack(pady=5)
        # Inicializa auto-connect
        self.manager.auto_connect_to_paired_devices()

    def start_scan(self):
        self.lb.delete(0, tk.END)
        self.update_status("Escaneando...")
        devices = self.manager.scan_devices()
        for i,(addr,name) in enumerate(devices):
            self.lb.insert(tk.END, f"{i}: {name} ({addr})")
        self.update_status("Scan completo")

    def connect_selected(self):
        sel = self.lb.curselection()
        if not sel:
            return messagebox.showwarning("Seleção", "Selecione um dispositivo")
        idx = int(self.lb.get(sel).split(':')[0])
        addr = self.manager.devices[idx][0]
        if self.manager.start_client(addr):
            self.update_status(f"Conectado: {addr}")
        else:
            self.update_status("Falha na conexão")

    def update_status(self, msg):
        self.status_label.config(text=msg)

    def open_reply_window(self, key, sender, content):
        # se a janela já existe...
        if key in self.reply_windows:
            frame = self.reply_windows[key]['frame']
            tk.Label(frame, text=f"{sender}: {content}", anchor='w', justify='left', wraplength=400).pack(fill='x', padx=5, pady=2)
            return

        # criação da janela...
        win = tk.Toplevel(self)
        win.title(f"Conversa: {sender}")  # título com o nome da pessoa

        msg_frame = tk.Frame(win)
        msg_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # primeira mensagem com sender
        tk.Label(msg_frame, text=f"{sender}: {content}", anchor='w', justify='left', wraplength=400).pack(fill='x', padx=5, pady=2)

        entry = tk.Entry(win, width=50)
        entry.pack(padx=5, pady=5, side='left', expand=True)

        def send_reply():
            text = entry.get().strip()
            if not text: return
            payload = {'key': key, 'reply': text}
            data = json.dumps(payload) + "\n"
            try:
                self.manager.bluetooth_socket.send(data.encode('utf-8'))
                entry.delete(0, tk.END)
                # exibe a mensagem do usuário
                tk.Label(msg_frame, text=f"Você: {text}", anchor='e', justify='right', wraplength=400).pack(fill='x', padx=5, pady=2)
            except Exception as e:
                print(f"[Python] Erro ao enviar reply: {e}")

        tk.Button(win, text="Enviar", command=send_reply).pack(padx=5, pady=5, side='right')

        # registra janela
        self.reply_windows[key] = {'window': win, 'frame': msg_frame}
        win.protocol("WM_DELETE_WINDOW", lambda: (self.reply_windows.pop(key, None), win.destroy()))



def run_gui():
    srv = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    app = None
    def create_app():
        nonlocal app
        manager = BluetoothConnectionManager(
            uuid=srv,
            status_callback=lambda m: app.update_status(m),
            callback_obj=None,
            # <-- aqui, renomeie os parâmetros para refletir sender e content:
            message_callback=lambda key, sender, content: app.open_reply_window(key, sender, content)
        )
        app = BluetoothGUI(manager)
        manager.callback_obj = app
        return app
    gui = create_app()
    gui.mainloop()
