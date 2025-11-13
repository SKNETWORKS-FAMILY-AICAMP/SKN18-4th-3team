import api from './axios';

// 채팅 메인 페이지 정보
export const getChatInfo = async () => {
  const response = await api.get('/chatbot/');
  return response.data;
};

// 대화 세션 목록 조회
export const getConversations = async () => {
  const response = await api.get('/chatbot/api/conversations/');
  return response.data;
};

// 대화 세션 생성
export const createConversation = async (title = '') => {
  const response = await api.post('/chatbot/api/conversations/', { title });
  return response.data;
};

// 대화 세션 상세 조회
export const getConversationDetail = async (conversationId) => {
  const response = await api.get(`/chatbot/api/conversations/${conversationId}/`);
  return response.data;
};

// 대화 세션 삭제
export const deleteConversation = async (conversationId) => {
  const response = await api.delete(`/chatbot/api/conversations/${conversationId}/`);
  return response.data;
};

// 메시지 전송 (로그인 사용자)
export const sendMessage = async (conversationId, content) => {
  const response = await api.post(`/chatbot/api/conversations/${conversationId}/messages/`, { content });
  return response.data;
};

// 게스트 채팅
export const sendGuestMessage = async (content, conversationHistory = []) => {
  const response = await api.post('/chatbot/api/chat/', { content, conversation_history: conversationHistory });
  return response.data;
};
