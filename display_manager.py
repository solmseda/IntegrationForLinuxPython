import pyperclip
from Notification_Data import NotificationData
from Clipboard_Data import ClipboardData

class DisplayManager:
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback

    def show_notification(self, notification_data: NotificationData):
        # Exibe a notificação na interface de usuário
        print(f"Notificação de {notification_data.app_name}: {notification_data.content}")

        if notification_data.is_replyable:
            if self.gui_callback:
                print(f"Esta notificação é respondível. ID da ação de resposta: {notification_data.reply_action_id}. Abrindo GUI para resposta...")
                self.gui_callback(notification_data)
            else:
                # Fallback or alternative if no GUI callback is provided
                print(f"Esta notificação é respondível. ID da ação de resposta: {notification_data.reply_action_id}")
                print("Nenhum callback da GUI configurado para responder.")
                # Optionally, could re-introduce CLI input here as a fallback,
                # but for now, it just prints the info.
        # Non-replyable notifications are just printed as before.

    def update_clipboard(self, clipboard_data: ClipboardData):
        # Atualiza a área de transferência com o conteúdo recebido
        pyperclip.copy(clipboard_data.content)
        print(f"Área de transferência atualizada com: {clipboard_data.content}")

    def send_reply(self, action_id: str, message: str):
        # Envia uma resposta através da conexão Bluetooth
        # Por enquanto, apenas exibe uma mensagem indicando que a resposta está sendo enviada
        print(f"Enviando resposta para a ação {action_id}: {message}")
