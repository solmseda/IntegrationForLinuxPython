import subprocess
import bluetooth
from plyer import notification
from Clipboard_Data import ClipboardData

class BluetoothConnectionManager:
    def __init__(self, uuid, status_callback=None):
        self.bluetooth_adapter = None
        self.bluetooth_socket = None
        self.input_stream = None
        self.output_stream = None
        self.uuid = str(uuid)
        self.device = None
        self.devices = []
        self.status_callback = status_callback  # Callback para atualizar o status na GUI

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
        if not self.pair_device(device_address):
            self.update_status("Pareamento falhou. Não foi possível conectar.")
            return False

        try:
            print(f"Tentando conectar ao dispositivo {device_address} com UUID {self.uuid}...")
            self.update_status(f"Conectando ao dispositivo {device_address}...")
            
            service_matches = bluetooth.find_service(uuid=self.uuid, address=device_address)
            
            if len(service_matches) == 0:
                print("Nenhum serviço encontrado no dispositivo especificado.")
                self.update_status("Nenhum serviço encontrado no dispositivo.")
                return False

            first_match = service_matches[0]
            port = first_match["port"]
            host = first_match["host"]

            print(f"Conectando ao host {host} na porta {port}")
            self.bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.bluetooth_socket.connect((host, port))
            print(f"Conectado ao dispositivo {device_address}")
            self.update_status(f"Conectado ao dispositivo {device_address} com sucesso.")
            return True
        except bluetooth.BluetoothError as e:
            print(f"Erro ao conectar: {e}")
            self.update_status("Erro ao conectar.")
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
            print("Conexão Bluetooth encerrada.")
        except Exception as e:
            print(f"Erro ao fechar conexão: {e}")

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

