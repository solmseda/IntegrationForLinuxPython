import subprocess
import threading
import time
import bluetooth
import json
import base64
import tempfile
import os
from plyer import notification
from Clipboard_Data import ClipboardData

class BluetoothConnectionManager:
    # User-facing app names for filtering notifications that can open a reply window
    # These should match the 'appName' value received in the JSON from Android
    WHATSAPP_APP_NAME = "WhatsApp"
    TELEGRAM_APP_NAME = "Telegram"

    def __init__(self, uuid, status_callback=None, notification_callback=None):
        self.bluetooth_adapter = None
        self.bluetooth_socket = None
        self.input_stream = None
        self.output_stream = None
        self.uuid = str(uuid)
        self.device = None
        self.devices = []
        self.status_callback = status_callback  # Callback para atualizar o status na GUI
        self.notification_callback = notification_callback # Callback para GUI para notificações com chave
        self.received_ids = set() # Para evitar notificações duplicadas baseadas em notificationId
        self.is_connected = False # Flag para rastrear o estado da conexão ativa

    def update_status(self, message):
        """Chama o callback para atualizar o status na GUI, se disponível."""
        if self.status_callback:
            self.status_callback(message)

    def start_server(self):
        # Placeholder para o servidor Bluetooth
        pass

    def authenticate(self):
        # Placeholder para lógica de autenticação
        pass

    def start_client(self, device_address):
        # Verifica se o dispositivo já está pareado
        already_paired = any(device[0] == device_address for device in self.list_paired_devices())

        if not already_paired:
            if not self.pair_device(device_address):
                self.update_status("Pareamento falhou. Não foi possível conectar.")
                return False
        else:
            print(f"Dispositivo {device_address} já está pareado. Pulando etapa de pareamento.")

        try:
            print(f"Tentando conectar ao dispositivo {device_address} com UUID {self.uuid}...")
            self.update_status(f"Conectando ao dispositivo {device_address}...")

            # Primeira tentativa: buscar serviço via SDP
            service_matches = bluetooth.find_service(uuid=self.uuid, address=device_address)

            if service_matches:
                first_match = service_matches[0]
                port = first_match["port"]
                host = first_match["host"]
                print(f"Serviço encontrado! Conectando ao host {host} na porta {port}")
            else:
                # Fallback: conecta diretamente
                print("Nenhum serviço encontrado via SDP. Tentando conexão direta na porta 1.")
                port = 1
                host = device_address

            self.bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.bluetooth_socket.connect((host, port))
            # Initialize streams after successful connection
            self.input_stream = self.bluetooth_socket.makefile('rb')
            self.output_stream = self.bluetooth_socket.makefile('wb')
            self.is_connected = True # Set connection flag
            print(f"Conectado ao dispositivo {device_address}. is_connected = {self.is_connected}")
            self.update_status(f"Conectado ao dispositivo {device_address} com sucesso.")
            
            # Inicia o listener para receber dados
            threading.Thread(target=self.listen_for_messages, daemon=True).start()

            return True

        except bluetooth.BluetoothError as e:
            print(f"Erro ao conectar: {e}")
            self.update_status("Erro ao conectar.")
            self.is_connected = False # Ensure flag is false on connection error
            return False

    def receive_notification(self, notification_data):
        try:
            data = self.input_stream.read(1024)
            notification_data.content = data.decode("utf-8")
            print(f"Notificação recebida: {notification_data.content}")

            self.show_system_notification(notification_data)
            
        except Exception as e:
            print(f"Erro ao receber notificação: {e}")

    def show_system_notification(self, notification_data):
        notification.notify(
            title=f"Notificação de {notification_data.app_name}",
            message=notification_data.content,
            app_name=notification_data.app_name,
            timeout=10,
        )
    
    def receive_clipboard_data(self):
        try:
            data = self.input_stream.read(1024)
            clipboard_data = ClipboardData(content=data.decode("utf-8"))
            print(f"Dados da área de transferência recebidos: {clipboard_data.content}")
            return clipboard_data
        except Exception as e:
            print(f"Erro ao receber dados da área de transferência: {e}")
            return None

    def send_message(self, message):
        try:
            self.output_stream.write(message.encode("utf-8"))
            self.output_stream.flush()
            print(f"Mensagem enviada: {message}")
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")

    def send_clipboard(self, clipboard_data):
        try:
            self.output_stream.write(clipboard_data.content.encode("utf-8"))
            self.output_stream.flush()
            print(f"Dados da área de transferência enviados: {clipboard_data.content}")
        except Exception as e:
            print(f"Erro ao enviar dados da área de transferência: {e}")

    def close_connection(self):
        try:
            if self.input_stream:
                self.input_stream.close()
            if self.output_stream:
                self.output_stream.close()
            if self.bluetooth_socket:
                self.bluetooth_socket.close()
            # Reset streams and socket to None after closing
            self.input_stream = None
            self.output_stream = None
            self.bluetooth_socket = None
            self.is_connected = False # Clear connection flag
            print(f"Conexão Bluetooth encerrada. is_connected = {self.is_connected}")
            self.update_status("Desconectado.") # Inform GUI
        except Exception as e:
            print(f"Erro ao fechar conexão: {e}")
            self.is_connected = False # Ensure flag is false even if close had errors

    def scan_devices(self):
        print("Iniciando o scan de dispositivos Bluetooth...")
        self.devices = bluetooth.discover_devices(lookup_names=True)

        if not self.devices:
            print("Nenhum dispositivo encontrado.")
        else:
            print("Dispositivos encontrados:")
            for idx, (address, name) in enumerate(self.devices):
                print(f"{idx}: {name or 'Desconhecido'} ({address})")

        return self.devices
    
    def list_paired_devices(self):
        """Retorna uma lista de dispositivos pareados com endereço e nome."""
        paired_devices = []
        
        try:
            # Executa o comando para listar dispositivos pareados
            output = subprocess.check_output(["bluetoothctl", "paired-devices"]).decode("utf-8")
            for line in output.splitlines():
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    address = parts[1]
                    name = parts[2]
                    paired_devices.append((address, name))
        except subprocess.CalledProcessError as e:
            print(f"Erro ao obter dispositivos pareados: {e}")
        
        return paired_devices
    
    def pair_device(self, device_address):
        try:
            paired_devices = self.list_paired_devices()
            if any(device[0] == device_address for device in paired_devices):
                print(f"Dispositivo {device_address} já está pareado.")
                self.update_status(f"Dispositivo {device_address} já está pareado.")
                return True

            print(f"Tentando parear com o dispositivo {device_address}...")
            self.update_status(f"Iniciando pareamento com {device_address}...")
            subprocess.run(["bluetoothctl", "pair", device_address], check=True)
            subprocess.run(["bluetoothctl", "trust", device_address], check=True)
            print(f"Dispositivo {device_address} pareado com sucesso.")
            self.update_status(f"Pareamento com {device_address} realizado com sucesso.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erro ao parear com o dispositivo {device_address}: {e}")
            self.update_status(f"Erro ao parear com {device_address}.")
            return False

    def auto_connect_to_paired_devices(self):
        def connect_loop():
            while True:
                if self.is_connected:
                    # Connection is active, just sleep and re-check.
                    #print(f"auto_connect_loop: Connection active (is_connected={self.is_connected}). Sleeping.")
                    time.sleep(5)  # Check status every 5 seconds
                    continue

                # If not connected, proceed to attempt connection
                #print(f"auto_connect_loop: No active connection (is_connected={self.is_connected}). Scanning.")
                self.update_status("Procurando dispositivos pareados para conexão automática...")
                paired_devices = self.list_paired_devices()

                if not paired_devices:
                    self.update_status("Nenhum dispositivo pareado encontrado. Tentando novamente em 10s...")
                    time.sleep(10)
                    continue # Go back to check is_connected and potentially retry

                connection_attempted_this_cycle = False
                for address, name in paired_devices:
                    # If by some chance connection was established by another thread/means while iterating
                    if self.is_connected:
                        #print(f"auto_connect_loop: Connection established mid-scan. Breaking device scan.")
                        break # Break from device loop, outer loop will catch is_connected

                    self.update_status(f"Verificando serviço em: {name} ({address})")
                    service_matches = bluetooth.find_service(uuid=str(self.uuid), address=address)

                    if service_matches:
                        self.update_status(f"Dispositivo compatível: {name}. Tentando conectar...")
                        connection_attempted_this_cycle = True
                        if self.start_client(address):  # start_client sets self.is_connected to True on success
                            self.update_status(f"Conectado automaticamente a: {name}")
                            #print(f"auto_connect_loop: Successfully connected to {name}. Breaking device scan.")
                            break  # Successfully connected, break from device loop
                        else:
                            # start_client failed, self.is_connected should be False
                            self.update_status(f"Falha ao conectar com {name}.")
                            # Continue to the next device
                    else:
                        print(f"{name} ({address}) não possui o serviço com UUID esperado.")

                # After iterating through all devices (or breaking due to successful connection)
                if not self.is_connected and connection_attempted_this_cycle:
                    # Attempted connection to one or more compatible devices but none succeeded
                    self.update_status("Falha ao conectar com dispositivos compatíveis. Tentando novamente em 10s...")
                    time.sleep(10)
                elif not self.is_connected and not connection_attempted_this_cycle and paired_devices:
                    # Paired devices exist, but none had the required service
                    self.update_status("Nenhum dispositivo com serviço compatível encontrado. Tentando novamente em 10s...")
                    time.sleep(10)
                # If self.is_connected is True here, the outer loop's `if self.is_connected:` check will handle it.
                # If no paired devices were found at all, that's handled by the first time.sleep(10) in this block.

        threading.Thread(target=connect_loop, daemon=True).start()


    def listen_for_messages(self):
        buffer = b""
        while True:
            try:
                chunk = self.bluetooth_socket.recv(1024) # This might block, consider timeout if needed
            except bluetooth.BluetoothError as e: # More specific exception
                print(f"Erro no recv (BluetoothError): {e}")
                self.update_status("Erro na conexão Bluetooth.")
                self.close_connection() # Sets is_connected to False
                return
            except Exception as e: # Catch other potential errors
                print(f"Erro inesperado no recv: {e}")
                self.update_status("Erro inesperado na conexão.")
                self.close_connection() # Sets is_connected to False
                return

            if not chunk:
                # conexão foi fechada pelo outro lado
                print("Conexão fechada pelo dispositivo Android.")
                self.update_status("Dispositivo desconectado.")
                self.close_connection() # Sets is_connected to False
                return

            # Acumula o pedaço recebido no buffer
            buffer += chunk

            # Tenta decodificar o buffer inteiro como JSON.
            try:
                texto_completo = buffer.decode("utf-8")
                mensagem_json = json.loads(texto_completo)
            except json.JSONDecodeError:
                # JSON ainda incompleto; aguardamos mais bytes
                continue

            # Se chegou aqui, 'mensagem_json' é um dicionário Python válido.

            # Evita duplicação (se existir "notificationId")
            notif_id = mensagem_json.get("notificationId")
            if notif_id and (notif_id in self.received_ids):
                buffer = b""  # limpa buffer para próxima mensagem
                continue
            if notif_id:
                self.received_ids.add(notif_id)

            # Extrai campos
            app_name = mensagem_json.get("appName", "Aplicativo Android")
            content = mensagem_json.get("content", "")
            icon_b64 = mensagem_json.get("iconBase64")
            key = mensagem_json.get("key") # Extract the key

            print(f"Notification JSON received: appName={app_name}, content={content}, key_present={key is not None}, iconBase64_present={icon_b64 is not None}")

            # Always show system notification via Plyer
            plyer_icon_path = None
            if icon_b64:
                try:
                    png_bytes = base64.b64decode(icon_b64)
                    fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="android_icon_")
                    os.write(fd, png_bytes)
                    os.close(fd)
                    plyer_icon_path = tmp_path
                except Exception as e:
                    print(f"Falha ao decodificar ícone para Plyer: {e}")

            notification.notify(
                title=f"Notificação de {app_name}",
                message=content,
                app_name="Integration4Linux", # App name for the notification itself
                timeout=10,
                app_icon=plyer_icon_path or "" # Use temp path for plyer
            )

            if plyer_icon_path: # Cleanup temp file for plyer icon
                # Schedule cleanup, so plyer has time to use it.
                # This could be more robust, e.g., plyer callback if available, or longer delay.
                threading.Timer(5.0, lambda p=plyer_icon_path: os.remove(p) if os.path.exists(p) else None).start()

            # If a key is present and a callback is registered, invoke the callback
            # only for specific apps (WhatsApp, Telegram), comparing with the new app name constants.
            if key and self.notification_callback and \
               (app_name == self.WHATSAPP_APP_NAME or app_name == self.TELEGRAM_APP_NAME):
                print(f"App '{app_name}' is eligible for reply window. Invoking notification_callback for key: {key}")
                # Pass icon_b64 directly to callback; it can decide to decode/save if needed for Toplevel
                self.notification_callback(app_name, content, icon_b64, key)
            elif key and self.notification_callback: # Key and callback exist, but app_name doesn't match
                print(f"Notification from app '{app_name}' with key '{key}' received, but app is not WhatsApp/Telegram. No reply window.")
            elif key: # Key present, but no callback registered at all (should ideally not happen if GUI is running)
                print(f"Notification with key '{key}' received, but no GUI callback registered for reply window (app: '{app_name}').")


            # Limpa buffer para próxima mensagem JSON
            buffer = b""
