import asyncio
from bleak import BleakScanner, BleakClient
from uuid import UUID
from Notification_Data import NotificationData
from Clipboard_Data import ClipboardData

class BluetoothConnectionManager:
    def __init__(self, uuid: UUID):
        self.bluetooth_adapter = None  # Placeholder para o adaptador Bluetooth
        self.bluetooth_socket = None   # Placeholder para o socket Bluetooth
        self.input_stream = None       # Placeholder para input stream
        self.output_stream = None      # Placeholder para output stream
        self.uuid = uuid               # UUID do serviço Bluetooth
        self.device = None             # Placeholder para o dispositivo conectado
        self.devices = []              # Lista de dispositivos encontrados durante o scan

    async def start_server(self):
        # Método para iniciar o servidor Bluetooth (a ser implementado)
        pass

    async def authenticate(self):
        # Placeholder para lógica de autenticação Bluetooth
        pass

    async def start_client(self, device):
        # Método para conectar ao dispositivo Bluetooth
        self.device = BleakClient(device.address)
        await self.device.connect()
        print(f"Conectado ao dispositivo: {device.name} ({device.address})")

    async def receive_notification(self, notification_data: NotificationData):
        # Recebe dados de notificação de uma característica específica via GATT
        data = await self.device.read_gatt_char(self.uuid)
        notification_data.content = data.decode()  # Atualiza o conteúdo da notificação
        print(f"Notificação recebida: {notification_data.content}")

    async def receive_clipboard_data(self):
        # Recebe dados da área de transferência de uma característica específica via GATT
        data = await self.device.read_gatt_char(self.uuid)
        return ClipboardData(content=data.decode())

    async def send_message(self, message: str):
        # Envia uma mensagem de volta ao dispositivo via GATT
        await self.device.write_gatt_char(self.uuid, message.encode())
        print(f"Mensagem enviada: {message}")

    async def send_clipboard(self, clipboard_data: ClipboardData):
        # Envia dados da área de transferência ao dispositivo Android via GATT
        await self.device.write_gatt_char(self.uuid, clipboard_data.content.encode())
        print(f"Dados da área de transferência enviados: {clipboard_data.content}")

    async def close_connection(self):
        # Fecha a conexão Bluetooth
        await self.device.disconnect()
        print("Conexão Bluetooth encerrada.")

    # Método adicionado para realizar o scan de dispositivos Bluetooth
    async def scan_devices(self):
        print("Iniciando o scan de dispositivos Bluetooth...")
        # Realiza o scan de dispositivos BLE disponíveis
        self.devices = await BleakScanner.discover()

        # Exibe os dispositivos encontrados
        if not self.devices:
            print("Nenhum dispositivo encontrado.")
        else:
            print("Dispositivos encontrados:")
            for idx, device in enumerate(self.devices):
                print(f"{idx}: {device.name} - {device.address}")

        return self.devices
