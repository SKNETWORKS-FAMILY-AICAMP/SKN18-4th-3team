from django.contrib import admin
from .models import Conversation, Message, SentimentAnalysis, DiseaseQuery


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


@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    """감정 분석 Admin"""
    list_display = ['id', 'message_preview', 'sentiment_type', 'sentiment_score', 'analyzed_at']
    list_filter = ['sentiment_type', 'analyzed_at']
    search_fields = ['message__content']
    readonly_fields = ['message', 'sentiment_type', 'sentiment_score', 'keywords', 'analyzed_at']
    ordering = ['-analyzed_at']
    date_hierarchy = 'analyzed_at'

    def message_preview(self, obj):
        content = obj.message.content[:30]
        return content + '...' if len(obj.message.content) > 30 else content
    message_preview.short_description = '메시지'


@admin.register(DiseaseQuery)
class DiseaseQueryAdmin(admin.ModelAdmin):
    """질환 검색 Admin"""
    list_display = ['id', 'disease_name', 'message_preview', 'searched_at']
    list_filter = ['disease_name', 'searched_at']
    search_fields = ['disease_name', 'message__content']
    readonly_fields = ['message', 'disease_name', 'searched_at']
    ordering = ['-searched_at']
    date_hierarchy = 'searched_at'

    def message_preview(self, obj):
        content = obj.message.content[:30]
        return content + '...' if len(obj.message.content) > 30 else content
    message_preview.short_description = '메시지'
