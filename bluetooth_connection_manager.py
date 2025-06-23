import subprocess
import threading
import time
import bluetooth
import json
import base64
import tempfile
import os
from plyer import notification

class BluetoothConnectionManager:
    def __init__(self, uuid, status_callback=None, callback_obj=None, message_callback=None):
        self.uuid = str(uuid)
        self.bluetooth_socket = None
        self.devices = []
        self.status_callback = status_callback    # função para atualizar status na GUI
        self.callback_obj = callback_obj          # objeto Tkinter, para usar after()
        self.message_callback = message_callback  # callback para abrir janela de resposta
        self.received_ids = set()                 # para evitar duplicatas via key

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
            output = subprocess.check_output(["bluetoothctl", "paired-devices"]).decode("utf-8")
            for line in output.splitlines():
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    paired.append((parts[1], parts[2]))
            print(f"[RESULT] Dispositivos pareados: {paired}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Erro ao listar dispositivos pareados: {e}")
        return paired

    def pair_device(self, address):
        if any(addr == address for addr, _ in self.list_paired_devices()):
            self.update_status(f"Já pareado: {address}")
            return True
        try:
            self.update_status(f"Pareando com {address}...")
            subprocess.run(["bluetoothctl", "pair", address], check=True)
            subprocess.run(["bluetoothctl", "trust", address], check=True)
            self.update_status(f"Pareamento concluído: {address}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Falha no pareamento: {e}")
            self.update_status(f"Falha no pareamento: {e}")
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
            while True:
                for addr, name in self.list_paired_devices():
                    self.update_status(f"Verificando {name} ({addr})")
                    try:
                        matches = bluetooth.find_service(uuid=self.uuid, address=addr)
                    except Exception:
                        matches = []
                    if matches and self.start_client(addr):
                        print(f"[AUTO] Conectado automaticamente a {addr}")
                        return
                self.update_status("Nenhum dispositivo compatível. Tentando novamente em 10s...")
                time.sleep(10)
        threading.Thread(target=loop, daemon=True).start()

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

            try:
                texto = buffer.decode('utf-8')
                data = json.loads(texto)
            except json.JSONDecodeError:
                continue

            key = data.get('key')
            if key and key in self.received_ids:
                buffer = b""
                continue
            if key:
                self.received_ids.add(key)

            app = data.get('appName', '')
            content = data.get('content', '')
            icon_b64 = data.get('iconBase64')

            print(f"[MESSAGE] Recebida de {app}: {content}")

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
                    icon_path = None

            notification.notify(
                title=f"Notificação de {app}",
                message=content,
                app_name="Integration4Linux",
                timeout=10,
                app_icon=(icon_path or "")
            )
            print("[NOTIFY] Notificação exibida")

            if self.message_callback and app.lower() in ('whatsapp', 'telegram'):
                print(f"[CALLBACK] Abrindo janela de resposta para {app}")
                self.callback_obj.after(0, lambda k=key, a=app, c=content: self.message_callback(k, a, c))

            buffer = b""

            if icon_path:
                time.sleep(1)
                try:
                    os.remove(icon_path)
                    print(f"[CLEANUP] Ícone removido: {icon_path}")
                except OSError as e:
                    print(f"[WARN] Falha ao remover ícone: {e}")
