class NotificationData:
    def __init__(self, app_name: str, content: str, icon=None, is_replyable: bool = False, reply_action_id: str = None):
        self.app_name = app_name
        self.content = content
        self.icon = icon
        self.is_replyable = is_replyable
        self.reply_action_id = reply_action_id
