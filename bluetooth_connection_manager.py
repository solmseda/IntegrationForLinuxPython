import subprocess
import threading
import time
import bluetooth
import json
import base64
import tempfile
import os
import pyperclip
from plyer import notification
import re

class BluetoothConnectionManager:
    def __init__(self, uuid, status_callback=None, callback_obj=None, message_callback=None):
        self.uuid = str(uuid)
        self.bluetooth_socket = None
        self.devices = []
        self.status_callback = status_callback
        self.callback_obj = callback_obj
        self.message_callback = message_callback
        self.received_ids = set()
        self.last_messages = {}

        # controla auto-connect
        self._auto_connect_enabled = False
        self._auto_connect_stop_event = threading.Event()

        # regex para "X mensagens de Y conversas"
        self._summary_re = re.compile(r"\d+\s+mensagens?\s+de\s+\d+\s+conversas?", re.IGNORECASE)

    def update_status(self, message):
        print(f"[STATUS] {message}")
        if self.status_callback and self.callback_obj:
            self.callback_obj.after(0, lambda: self.status_callback(message))

    def stop_auto_connect(self):
        """Desativa o auto-connect e interrompe o wait() imediatamente."""
        self._auto_connect_enabled = False
        self._auto_connect_stop_event.set()

    def auto_connect_to_paired_devices(self):
        """Ativa o auto-connect e inicia o loop em thread."""
        # prepara o event e flag
        self._auto_connect_stop_event.clear()
        self._auto_connect_enabled = True
        threading.Thread(target=self._auto_connect_loop, daemon=True).start()

    def _auto_connect_loop(self):
        print("[AUTO] Iniciando auto-connection loop")
        while self._auto_connect_enabled:
            for addr, name in self.list_paired_devices():
                if not self._auto_connect_enabled:
                    return
                self.update_status(f"Verificando {name} ({addr})")
                try:
                    matches = bluetooth.find_service(uuid=self.uuid, address=addr)
                except Exception:
                    matches = []
                if matches and self.start_client(addr):
                    print(f"[AUTO] Conectado automaticamente a {addr}")
                    # desliga definitivo
                    self.stop_auto_connect()
                    return
            self.update_status("Nenhum dispositivo compatível. Tentando novamente em 10s...")
            # espera até 10s ou até stop_auto_connect() ser chamado
            self._auto_connect_stop_event.wait(10)

    def scan_devices(self):
        """Para o auto-connect e faz um scan manual de dispositivos."""
        self.stop_auto_connect()
        self.update_status("Iniciando scan de dispositivos...")
        try:
            self.devices = bluetooth.discover_devices(lookup_names=True)
        except Exception as e:
            print(f"[ERROR] Erro no scan: {e}")
            self.update_status("Erro ao escanear dispositivos.")
            return []
        if self.devices:
            self.update_status(f"{len(self.devices)} dispositivo(s) encontrado(s).")
        else:
            self.update_status("Nenhum dispositivo encontrado.")
        return self.devices

    def list_paired_devices(self):
        print("[ACTION] Listando dispositivos pareados...")
        paired = []
        try:
            output = subprocess.check_output(["bluetoothctl", "paired-devices"]).decode()
            for line in output.splitlines():
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    paired.append((parts[1], parts[2]))
            print(f"[RESULT] Dispositivos pareados: {paired}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Erro ao listar dispositivos pareados: {e}")
        return paired

    def pair_device(self, device_address):
        """Para o auto-connect, inicia o pareamento e, em caso de sucesso, desliga o auto-connect."""
        self.stop_auto_connect()
        self.update_status(f"Iniciando pareamento com {device_address}...")
        try:
            proc = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            # configurações iniciais
            proc.stdin.write("agent KeyboardDisplay\n")
            proc.stdin.write("default-agent\n")
            proc.stdin.write("pairable on\n")
            proc.stdin.flush()

            # ativa scan interno para facilitar pairing
            proc.stdin.write("scan on\n"); proc.stdin.flush()
            time.sleep(5)
            proc.stdin.write("scan off\n"); proc.stdin.flush()

            # solicita pareamento
            proc.stdin.write(f"pair {device_address}\n"); proc.stdin.flush()

            paired = False
            start = time.time()
            while time.time() - start < 30:
                line = proc.stdout.readline().strip()
                if not line:
                    continue
                print(f"[PAIRCTL] {line}")
                if ("Request confirmation" in line or
                    "Confirm passkey" in line or
                    "Confirm PIN" in line):
                    proc.stdin.write("yes\n"); proc.stdin.flush()
                    continue
                if "Pairing successful" in line or "Paired: yes" in line:
                    paired = True
                    break

            if not paired:
                self.update_status("Falha no pareamento (timeout).")
                proc.stdin.write("quit\n"); proc.stdin.flush()
                proc.terminate()
                return False

            # confia no dispositivo e sai
            proc.stdin.write(f"trust {device_address}\n")
            proc.stdin.write("quit\n"); proc.stdin.flush()
            proc.wait(timeout=5)

            self.update_status(f"Pareamento com {device_address} realizado com sucesso.")
            # desliga de vez o auto-connect
            self.stop_auto_connect()
            return True

        except Exception as e:
            print(f"[ERROR] Erro ao parear com {device_address}: {e}")
            self.update_status(f"Erro ao parear com {device_address}.")
            return False

    def start_client(self, address):
        """Inicia o cliente RFCOMM; para o auto-connect antes."""
        self.stop_auto_connect()
        self.update_status(f"Iniciando cliente para {address}...")
        if not any(addr == address for addr, _ in self.list_paired_devices()):
            if not self.pair_device(address):
                return False

        print(f"[ACTION] Procurando serviço UUID={self.uuid} em {address}")
        try:
            matches = bluetooth.find_service(uuid=self.uuid, address=address)
        except Exception as e:
            print(f"[ERROR] Erro ao buscar serviço: {e}")
            matches = []

        if matches:
            host = matches[0]["host"]
            port = matches[0]["port"]
            print(f"[RESULT] Serviço encontrado em {host}:{port}")
        else:
            host, port = address, 1
            print(f"[WARN] Nenhum serviço SDP; usando fallback {host}:{port}")

        try:
            self.bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.bluetooth_socket.connect((host, port))
            self.update_status(f"Conectado a {address}")
        except Exception as e:
            print(f"[ERROR] Falha ao conectar RFCOMM: {e}")
            self.update_status("Erro na conexão.")
            return False

        # dispara thread de recepção
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        return True

    def listen_for_messages(self):
        print("[LISTEN] Thread de recepção iniciada")
        buffer = b""
        while True:
            try:
                chunk = self.bluetooth_socket.recv(1024)
            except Exception as e:
                print(f"[ERROR] Erro no recv: {e}")
                self.update_status("Erro na conexão.")
                return

            if not chunk:
                print("[INFO] Conexão fechada pelo dispositivo Android.")
                self.update_status("Dispositivo desconectado")
                return

            buffer += chunk
            try:
                data = json.loads(buffer.decode('utf-8'))
            except json.JSONDecodeError:
                continue

            buffer = b""
            key = data.get('key')
            app = data.get('appName', '')
            sender = data.get('sender', app)
            content = data.get('content', '')
            icon_b64 = data.get('iconBase64')

            last = self.last_messages.get(key)
            if key and last == content:
                continue
            if key:
                self.last_messages[key] = content

            print(f"[MESSAGE] {sender} ({app}): {content}")

            icon_path = None
            if icon_b64:
                try:
                    png = base64.b64decode(icon_b64)
                    fd, tmp = tempfile.mkstemp(suffix='.png', prefix='android_icon_')
                    os.write(fd, png)
                    os.close(fd)
                    icon_path = tmp
                except Exception as e:
                    print(f"[ERROR] Falha ao decodificar ícone: {e}")

            notification.notify(
                title=f"Notificação de {app}",
                message=content,
                app_name="Integration4Linux",
                timeout=10,
                app_icon=(icon_path or "")
            )
            print("[NOTIFY] Notificação exibida")

            lower_app = app.lower()
            lower_cont = content.lower()
            is_chat_app = 'telegram' in lower_app or 'whatsapp' in lower_app
            is_summary = bool(self._summary_re.search(content))
            is_scanning = lower_cont.startswith("procurando novas mensagens")
            is_own = sender.lower().startswith("você")

            if (self.message_callback and is_chat_app and not is_summary and not is_scanning and not is_own):
                print(f"[CALLBACK] Abrindo popup para conversa com {sender}")
                def _cb(k=key, s=sender, c=content):
                    self.message_callback(k, s, c)
                self.callback_obj.after(0, _cb)

            if icon_path:
                time.sleep(1)
                try:
                    os.remove(icon_path)
                except Exception:
                    pass
