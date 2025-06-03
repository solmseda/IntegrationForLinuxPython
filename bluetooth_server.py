from bluetooth_connection_manager import BluetoothConnectionManager

class BluetoothServer:
    def __init__(self, connection_manager: BluetoothConnectionManager):
        self.connection_manager = connection_manager

    async def start(self):
        # Inicia o servidor Bluetooth
        await self.connection_manager.start_server()
        print("Servidor Bluetooth em funcionamento.")

    async def receive_reply_data(self):
        # Recebe dados de resposta do cliente Bluetooth
        # Aguarda por uma mensagem do tipo "reply"
        reply_data = await self.connection_manager.receive_message("reply")
        if reply_data:
            print(f"Dados de resposta recebidos: {reply_data}")
            return reply_data
        return None
