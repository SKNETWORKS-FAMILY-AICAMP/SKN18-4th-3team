from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    """대화 세션 내 메시지 인라인"""
    model = Message
    extra = 0
    readonly_fields = ['role', 'content', 'thinking_process', 'created_at']
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """대화 세션 Admin"""
    list_display = ['id', 'user', 'title', 'created_at', 'updated_at', 'message_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'user__username', 'title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = '메시지 수'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """메시지 Admin"""
    list_display = ['id', 'conversation', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__user__email']
    readonly_fields = ['conversation', 'role', 'content', 'thinking_process', 'created_at']
    ordering = ['-created_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용'
