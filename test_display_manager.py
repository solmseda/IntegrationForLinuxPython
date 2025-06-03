import unittest
from unittest.mock import patch, call
import io
import sys

# Assuming Notification_Data and DisplayManager are in the same directory or accessible via PYTHONPATH
from Notification_Data import NotificationData
from display_manager import DisplayManager

class TestDisplayManager(unittest.TestCase):

    def setUp(self):
        # This method will be called before each test
        self.display_manager = DisplayManager()

    @patch('builtins.print')
    def test_show_notification_not_replyable(self, mock_print):
        notification = NotificationData(app_name="TestApp", content="Test notification content", is_replyable=False)
        self.display_manager.show_notification(notification)

        # Check that the basic notification is printed
        mock_print.assert_any_call("Notificação de TestApp: Test notification content")

        # Check that reply-specific messages are NOT printed
        printed_text = "\n".join([c[0][0] for c in mock_print.call_args_list])
        self.assertNotIn("Esta notificação é respondível.", printed_text)
        self.assertNotIn("Do you want to reply? (yes/no):", printed_text)

    @patch('display_manager.DisplayManager.send_reply')
    @patch('builtins.input', return_value='no')
    @patch('builtins.print')
    def test_show_notification_replyable_no_reply(self, mock_print, mock_input, mock_send_reply):
        notification = NotificationData(app_name="TestApp", content="Replyable notification", icon=None, is_replyable=True, reply_action_id="action_123")
        self.display_manager.show_notification(notification)

        mock_print.assert_any_call("Notificação de TestApp: Replyable notification")
        mock_print.assert_any_call("Esta notificação é respondível. ID da ação de resposta: action_123")
        mock_input.assert_called_once_with("Do you want to reply? (yes/no): ")
        mock_send_reply.assert_not_called()

    @patch('display_manager.DisplayManager.send_reply')
    @patch('builtins.input', side_effect=['yes', 'Test Reply Message'])
    @patch('builtins.print')
    def test_show_notification_replyable_with_reply(self, mock_print, mock_input, mock_send_reply):
        notification = NotificationData(app_name="TestApp", content="Another replyable notification", icon=None, is_replyable=True, reply_action_id="action_xyz")
        self.display_manager.show_notification(notification)

        mock_print.assert_any_call("Notificação de TestApp: Another replyable notification")
        mock_print.assert_any_call("Esta notificação é respondível. ID da ação de resposta: action_xyz")

        expected_input_calls = [
            call("Do you want to reply? (yes/no): "),
            call("Enter your reply: ")
        ]
        mock_input.assert_has_calls(expected_input_calls)
        mock_send_reply.assert_called_once_with("action_xyz", "Test Reply Message")

    @patch('builtins.print')
    def test_send_reply_method(self, mock_print):
        action_id = "test_action_id_send"
        message = "Hello, this is a reply."
        self.display_manager.send_reply(action_id, message)

        mock_print.assert_called_once_with(f"Enviando resposta para a ação {action_id}: {message}")

if __name__ == '__main__':
    unittest.main()
