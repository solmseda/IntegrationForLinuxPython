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
        # Lista de dispositivos
        self.lb = tk.Listbox(self)
        self.lb.pack(fill='x', padx=10)
        tk.Button(self, text="Connect", command=self.connect_selected).pack(pady=5)
        # Inicializa auto-connect
        self.manager.auto_connect_to_paired_devices()

    def start_scan(self):
        self.manager.stop_auto_connect()
        self.lb.delete(0, tk.END)
        self.update_status("Escaneando...")
        devices = self.manager.scan_devices()
        for i, (addr, name) in enumerate(devices):
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
        # Se a janela já existe, insere nova linha no Text e rola
        if key in self.reply_windows:
            text_widget = self.reply_windows[key]['text']
            text_widget.config(state='normal')
            text_widget.insert('end', f"{sender}: {content}\n")
            text_widget.see('end')
            text_widget.config(state='disabled')
            return

        # Cria nova janela de conversa
        win = tk.Toplevel(self)
        win.title(f"Conversa: {sender}")
        win.geometry("450x300")

        # Usa grid para manter Entry sempre visível
        win.rowconfigure(0, weight=1)
        win.rowconfigure(1, weight=0)
        win.columnconfigure(0, weight=1)
        win.columnconfigure(1, weight=0)

        # Text + Scrollbar
        text_widget = tk.Text(win, wrap='word', state='disabled')
        text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar = tk.Scrollbar(win, command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Insere primeira mensagem
        text_widget.config(state='normal')
        text_widget.insert('end', f"{sender}: {content}\n")
        text_widget.config(state='disabled')

        # Entry e botão Enviar na segunda linha
        entry = tk.Entry(win)
        entry.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        def send_reply():
            txt = entry.get().strip()
            if not txt:
                return
            payload = {'key': key, 'reply': txt}
            data = json.dumps(payload) + "\n"
            try:
                self.manager.bluetooth_socket.send(data.encode('utf-8'))
                entry.delete(0, 'end')
                text_widget.config(state='normal')
                text_widget.insert('end', f"Você: {txt}\n")
                text_widget.see('end')
                text_widget.config(state='disabled')
            except Exception as e:
                print(f"[Python] Erro ao enviar reply: {e}")

        send_btn = tk.Button(win, text="Enviar", command=send_reply)
        send_btn.grid(row=1, column=1, sticky='e', padx=5, pady=5)

        # Armazena referências
        self.reply_windows[key] = {'window': win, 'text': text_widget, 'entry': entry}

        # Ao fechar, remove do dicionário
        win.protocol("WM_DELETE_WINDOW", lambda k=key, w=win: (self.reply_windows.pop(k, None), w.destroy()))


def run_gui():
    srv = UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    app = None
    def create_app():
        nonlocal app
        manager = BluetoothConnectionManager(
            uuid=srv,
            status_callback=lambda m: app.update_status(m),
            callback_obj=None,
            message_callback=lambda key, sender, content: app.open_reply_window(key, sender, content)
        )
        app = BluetoothGUI(manager)
        manager.callback_obj = app
        return app
    gui = create_app()
    gui.mainloop()
