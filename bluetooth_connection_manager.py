import bluetooth

class BluetoothConnectionManager:
    def __init__(self):
        self.client_socket = None
        self.server_socket = None

    def start_server(self):
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_socket.bind(("", bluetooth.PORT_ANY))
        self.server_socket.listen(1)
        port = self.server_socket.getsockname()[1]
        
        bluetooth.advertise_service(self.server_socket, "BluetoothServer",
                                    service_id="00001101-0000-1000-8000-00805F9B34FB",
                                    service_classes=["00001101-0000-1000-8000-00805F9B34FB"])
        
        print(f"Servidor Bluetooth iniciado na porta {port}")
        self.client_socket, client_address = self.server_socket.accept()
        print(f"Cliente {client_address} conectado.")

    def start_client(self, address):
        self.client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.client_socket.connect((address, 1))
        print(f"Conectado ao dispositivo {address}")

    def send_message(self, message):
        if self.client_socket:
            self.client_socket.send(message)
            print(f"Mensagem enviada: {message}")
    
    def send_clipboard_data(self, clipboard_data):
        self.send_message(clipboard_data.content)
    
    def receive_data(self):
        try:
            data = self.client_socket.recv(1024)
            return data.decode('utf-8')
        except Exception as e:
            print(f"Erro ao receber dados: {e}")
            return None

    def close_connection(self):
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        print("Conexão Bluetooth fechada.")
