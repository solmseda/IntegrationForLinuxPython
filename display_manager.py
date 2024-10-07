import pyperclip
from Notification_Data import NotificationData
from Clipboard_Data import ClipboardData

class DisplayManager:
    def show_notification(self, notification_data: NotificationData):
        # Exibe a notificação na interface de usuário
        print(f"Notificação de {notification_data.app_name}: {notification_data.content}")

    def update_clipboard(self, clipboard_data: ClipboardData):
        # Atualiza a área de transferência com o conteúdo recebido
        pyperclip.copy(clipboard_data.content)
        print(f"Área de transferência atualizada com: {clipboard_data.content}")
