from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothClient:
    def __init__(self, connection_manager: BluetoothConnectionManager):
        self.connection_manager = connection_manager

    async def connect(self, device):
        await self.connection_manager.connect(device)

    async def send_notification_data(self, notification_data: str):
        await self.connection_manager.send_message(f"notification:{notification_data}")

    async def send_reply_data(self, reply_data: str):
        # Envia dados de resposta para o servidor Bluetooth
        # Adiciona um prefixo "reply:" para identificar o tipo de mensagem
        await self.connection_manager.send_message(f"reply:{reply_data}")

    async def receive_clipboard_data(self):
        return await self.connection_manager.receive_clipboard_data()
