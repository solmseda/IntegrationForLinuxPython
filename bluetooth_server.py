from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothServer:
    def __init__(self):
        self.connection_manager = BluetoothConnectionManager()

    def start(self):
        self.connection_manager.start_server()
