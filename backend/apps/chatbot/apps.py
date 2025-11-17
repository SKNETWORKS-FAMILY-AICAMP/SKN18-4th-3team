from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chatbot'

    def ready(self):
        """
        앱 시작 시 Signal 등록
        """
        import apps.chatbot.models  # Signal 등록을 위해 import
