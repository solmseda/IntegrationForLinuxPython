import subprocess
import bluetooth
from plyer import notification
from Clipboard_Data import ClipboardData

class BluetoothConnectionManager:
    def __init__(self, uuid):
        self.bluetooth_adapter = None  # Placeholder para o adaptador Bluetooth
        self.bluetooth_socket = None   # Placeholder para o socket Bluetooth
        self.input_stream = None       # Placeholder para input stream
        self.output_stream = None      # Placeholder para output stream
        self.uuid = str(uuid)          # UUID do serviço Bluetooth
        self.device = None             # Placeholder para o dispositivo conectado
        self.devices = []              # Lista de dispositivos encontrados durante o scan

    def start_server(self):
        # Placeholder para o servidor Bluetooth
        pass

    def authenticate(self):
        # Placeholder para lógica de autenticação
        pass

    def start_client(self, device):
        try:
            print(f"Tentando conectar ao dispositivo {device}...")
            service_matches = bluetooth.find_service(uuid=self.uuid, address=device)
            
            if len(service_matches) == 0:
                print("Nenhum serviço encontrado no dispositivo especificado.")
                return False

            first_match = service_matches[0]
            port = first_match["port"]
            name = first_match["name"]
            host = first_match["host"]

            print(f"Conectando ao host {host} na porta {port}")
            self.bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.bluetooth_socket.connect((host, port))
            self.input_stream = self.bluetooth_socket.makefile('rb')
            self.output_stream = self.bluetooth_socket.makefile('wb')

            print(f"Conectado ao serviço \"{name}\" no dispositivo ({device})")
            return True
        except bluetooth.BluetoothError as e:
            print(f"Erro ao conectar: {e}")
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
