from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothServer:
    def __init__(self, connection_manager: BluetoothConnectionManager):
        self.connection_manager = connection_manager

    async def start(self):
        # Inicia o servidor Bluetooth
        await self.connection_manager.start_server()
        print("Servidor Bluetooth em funcionamento.")
