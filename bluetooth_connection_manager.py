import subprocess
import threading
import time
import bluetooth
import json
import base64
import tempfile
import os
import pyperclip
import re
from plyer import notification

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
        self._auto_connect_enabled = True
        # regex para "X mensagens de Y conversas"
        self._summary_re = re.compile(r"\d+\s+mensagens?\s+de\s+\d+\s+conversas?", re.IGNORECASE)

    def update_status(self, message):
        print(f"[STATUS] {message}")
        if self.status_callback and self.callback_obj:
            self.callback_obj.after(0, lambda: self.status_callback(message))

    def scan_devices(self):
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
        try:
            if any(addr == device_address for addr, _ in self.list_paired_devices()):
                self.update_status(f"Dispositivo {device_address} já está pareado.")
                return True
            self.update_status(f"Iniciando pareamento com {device_address}...")
            proc = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            proc.stdin.write("agent KeyboardDisplay\n")
            proc.stdin.write("default-agent\n")
            proc.stdin.write("pairable on\n")
            proc.stdin.flush()
            proc.stdin.write(f"pair {device_address}\n")
            proc.stdin.flush()
            paired = False
            start = time.time()
            while time.time() - start < 30:
                line = proc.stdout.readline().strip()
                if not line:
                    continue
                print("[PAIRCTL]", line)
                if ("Request confirmation" in line
                    or "Confirm passkey" in line
                    or "Confirm PIN" in line):
                    proc.stdin.write("yes\n")
                    proc.stdin.flush()
                    continue
                if "Pairing successful" in line or "Paired: yes" in line:
                    paired = True
                    break
            if not paired:
                self.update_status("Falha no pareamento (timeout).")
                proc.stdin.write("quit\n"); proc.stdin.flush(); proc.terminate()
                return False
            proc.stdin.write(f"trust {device_address}\n")
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=5)
            self.update_status(f"Pareamento com {device_address} realizado com sucesso.")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao parear com {device_address}: {e}")
            self.update_status(f"Erro ao parear com {device_address}.")
            return False

    def start_client(self, address):
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
        except bluetooth.BluetoothError as e:
            print(f"[ERROR] Erro de conexão: {e}")
            self.update_status(f"Erro de conexão: {e}")
            return False
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        return True

    def auto_connect_to_paired_devices(self):
        def loop():
            print("[AUTO] Iniciando auto-connection loop")
            while self._auto_connect_enabled:
                for addr, name in self.list_paired_devices():
                    self.update_status(f"Verificando {name} ({addr})")
                    try:
                        matches = bluetooth.find_service(uuid=self.uuid, address=addr)
                    except Exception:
                        matches = []
                    if matches and self.start_client(addr):
                        print(f"[AUTO] Conectado automaticamente a {addr}")
                        self._auto_connect_enabled = False
                        return
                self.update_status("Nenhum dispositivo compatível. Tentando novamente em 10s...")
                time.sleep(10)
        threading.Thread(target=loop, daemon=True).start()

    def stop_auto_connect(self):
        self._auto_connect_enabled = False

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
                self.update_status("Dispositivo desconectado.")
                return

            buffer += chunk

            # tenta parsear JSON completo
            try:
                data = json.loads(buffer.decode('utf-8'))
                print(f"[DEBUG DATA] {data!r}")
            except json.JSONDecodeError:
                continue  # JSON incompleto

            # 1) Mensagem de clipboard
            if data.get('type') == 'clipboard':
                text = data.get('content', '')
                if text:
                    try:
                        pyperclip.copy(text)
                        print(f"[CLIPBOARD] Copiado para o clipboard: {text!r}")
                        notification.notify(
                            title="Clipboard atualizado",
                            message=text,
                            app_name="Integration4Linux",
                            timeout=5
                        )
                    except Exception as e:
                        print(f"[ERROR] Falha ao atualizar clipboard: {e}")
                buffer = b""
                continue

            # 2) Notificação de app
            key      = data.get('key')
            app      = data.get('appName', '')
            sender   = data.get('sender', app)
            content  = data.get('content', '')
            icon_b64 = data.get('iconBase64')

            # evita duplicatas
            last = self.last_messages.get(key)
            if key and last == content:
                buffer = b""
                continue
            if key:
                self.last_messages[key] = content

            print(f"[MESSAGE] {sender} ({app}): {content}")

            # salva ícone
            icon_path = None
            if icon_b64:
                try:
                    png = base64.b64decode(icon_b64)
                    fd, tmp = tempfile.mkstemp(suffix='.png', prefix='android_icon_')
                    os.write(fd, png)
                    os.close(fd)
                    icon_path = tmp
                    print(f"[ACTION] Ícone salvo em {icon_path}")
                except Exception as e:
                    print(f"[ERROR] Falha ao decodificar ícone: {e}")

            # exibe notificação de desktop
            notification.notify(
                title=f"Notificação de {app}",
                message=content,
                app_name="Integration4Linux",
                timeout=10,
                app_icon=(icon_path or "")
            )
            print("[NOTIFY] Notificação exibida")

            # 3) Popup de resposta só para chats reais
            lower_app   = app.lower()
            lower_cont  = content.lower()
            is_chat_app = 'telegram' in lower_app or 'whatsapp' in lower_app
            is_summary  = 'mensagens de' in lower_cont
            is_scanning = lower_cont.startswith("procurando novas mensagens")
            is_own      = sender.lower().startswith("você")

            if (self.message_callback
                and is_chat_app
                and not is_summary
                and not is_scanning
                and not is_own):
                print(f"[CALLBACK] Abrindo popup para conversa com {sender}")
                def _cb(k=key, s=sender, c=content):
                    self.message_callback(k, s, c)
                self.callback_obj.after(0, _cb)

            buffer = b""

            # limpa ícone temporário
            if icon_path:
                time.sleep(1)
                try:
                    os.remove(icon_path)
                    print(f"[CLEANUP] Ícone removido: {icon_path}")
                except Exception:
                    pass
