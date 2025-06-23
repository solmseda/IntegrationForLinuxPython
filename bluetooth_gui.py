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

    def open_reply_window(self, app, content):
        win = tk.Toplevel(self)
        win.title(f"Responder a {app}")
        tk.Label(win, text=f"{app}: {content}").pack(padx=10, pady=5)
        entry = tk.Entry(win, width=50)
        entry.pack(padx=10, pady=5)
        def send_reply():
            text = entry.get().strip()
            if not text:
                return
            payload = {
                'replyTo': app,
                'reply': text
            }
            data = json.dumps(payload) + "\n"

            # ——— AQUI EMBAIXO: LOG NO PYTHON ———
            print(f"[Python] Enviando reply JSON para Android: {data!r}")

            try:
                self.manager.bluetooth_socket.send(data.encode('utf-8'))
                print("[Python] send() completou sem exceção")
                win.destroy()
            except Exception as e:
                print(f"[Python] Erro ao enviar reply: {e}")
        tk.Button(win, text="Enviar", command=send_reply).pack(pady=5)


def run_gui():
    srv = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    app = None
    def create_app():
        nonlocal app
        manager = BluetoothConnectionManager(
            uuid=srv,
            status_callback=lambda m: app.update_status(m),
            callback_obj=None,
            message_callback=lambda a,c: app.open_reply_window(a,c)
        )
        app = BluetoothGUI(manager)
        # set callback_obj after init
        manager.callback_obj = app
        return app
    gui = create_app()
    gui.mainloop()
