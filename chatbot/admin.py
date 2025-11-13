from django.contrib import admin
from .models import ChatSession, Message, SentimentAnalysis, DiseaseQuery


# ChatSession 관리자 설정
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """
    대화 세션 관리자 페이지 설정
    """
    list_display = ['id', 'user', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


# Message 관리자 설정
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    메시지 관리자 페이지 설정
    """
    list_display = ['id', 'session', 'sender', 'content_preview', 'created_at']
    list_filter = ['sender', 'created_at']
    search_fields = ['content', 'session__user__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        """메시지 내용 미리보기 (50자까지)"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '메시지 내용'


# SentimentAnalysis 관리자 설정
@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    """
    감정 분석 관리자 페이지 설정
    """
    list_display = ['id', 'message_preview', 'sentiment_type', 'sentiment_score', 'analyzed_at']
    list_filter = ['sentiment_type', 'analyzed_at']
    search_fields = ['message__content']
    ordering = ['-analyzed_at']
    date_hierarchy = 'analyzed_at'

    def message_preview(self, obj):
        """메시지 내용 미리보기"""
        return obj.message.content[:30] + '...' if len(obj.message.content) > 30 else obj.message.content
    message_preview.short_description = '메시지'


# DiseaseQuery 관리자 설정
@admin.register(DiseaseQuery)
class DiseaseQueryAdmin(admin.ModelAdmin):
    """
    질환 검색 관리자 페이지 설정
    """
    list_display = ['id', 'disease_name', 'message_preview', 'searched_at']
    list_filter = ['disease_name', 'searched_at']
    search_fields = ['disease_name', 'message__content']
    ordering = ['-searched_at']
    date_hierarchy = 'searched_at'

    def message_preview(self, obj):
        """메시지 내용 미리보기"""
        return obj.message.content[:30] + '...' if len(obj.message.content) > 30 else obj.message.content
    message_preview.short_description = '메시지'
