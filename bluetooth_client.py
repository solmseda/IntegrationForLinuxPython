from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothClient:
    def __init__(self, connection_manager: BluetoothConnectionManager):
        self.connection_manager = connection_manager

    async def connect(self, device):
        await self.connection_manager.connect(device)

    async def send_notification_data(self, notification_data: str):
        await self.connection_manager.send_message(notification_data)

    async def receive_clipboard_data(self):
        return await self.connection_manager.receive_clipboard_data()
