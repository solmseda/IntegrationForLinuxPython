from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothClient:
    def __init__(self):
        self.connection_manager = BluetoothConnectionManager()

    def connect(self, address):
        self.connection_manager.start_client(address)

    def send_notification(self, notification_data):
        self.connection_manager.send_message(notification_data.content)

    def receive_clipboard_data(self):
        return self.connection_manager.receive_data()
