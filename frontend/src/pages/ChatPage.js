import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getChatInfo, getConversations, createConversation, getConversationDetail, sendMessage, sendGuestMessage, deleteConversation } from '../api/chat';
import Header from '../components/Header';
import './ChatPage.css';

function ChatPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [guestHistory, setGuestHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    loadChatInfo();
    // 메인에서 사이드바 토글을 통해 넘어온 경우
    if (location.state?.openSidebar) {
      setIsSidebarOpen(true);
    }
  }, [location]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatInfo = async () => {
    try {
      const data = await getChatInfo();
      setIsAuthenticated(data.is_authenticated);
      setUser(data.user);
      if (data.is_authenticated) {
        loadConversations();
      }
    } catch (err) {
      console.error('채팅 정보 로드 실패:', err);
    }
  };

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      console.error('대화 목록 로드 실패:', err);
    }
  };

  const handleConversationClick = async (conversationId) => {
    try {
      const data = await getConversationDetail(conversationId);
      setSelectedConversation(data);
      setMessages(data.messages);
    } catch (err) {
      console.error('대화 세션 로드 실패:', err);
    }
  };

  const handleNewConversation = async () => {
    try {
      const data = await createConversation();
      setConversations([data, ...conversations]);
      setSelectedConversation(data);
      setMessages([]);
    } catch (err) {
      console.error('대화 세션 생성 실패:', err);
    }
  };

  const handleDeleteConversation = async (conversationId) => {
    if (!window.confirm('정말 이 대화를 삭제하시겠습니까?')) return;
    try {
      await deleteConversation(conversationId);
      setConversations(conversations.filter(c => c.id !== conversationId));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('대화 삭제 실패:', err);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    setIsLoading(true);
    try {
      if (isAuthenticated) {
        // 로그인 사용자
        if (!selectedConversation) {
          // 대화 세션이 없으면 새로 생성
          const newConv = await createConversation();
          setConversations([newConv, ...conversations]);
          setSelectedConversation(newConv);

          const data = await sendMessage(newConv.id, inputMessage);
          setMessages([data.user_message, data.assistant_message]);
        } else {
          const data = await sendMessage(selectedConversation.id, inputMessage);
          setMessages([...messages, data.user_message, data.assistant_message]);
        }
        loadConversations();  // 대화 목록 갱신
      } else {
        // 게스트 사용자
        const userMessage = { role: 'user', content: inputMessage, created_at: new Date().toISOString() };
        const newHistory = [...guestHistory, userMessage];
        setMessages([...messages, userMessage]);

        const data = await sendGuestMessage(inputMessage, guestHistory);
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          thinking_process: data.thinking_process,
          created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, assistantMessage]);
        setGuestHistory([...newHistory, assistantMessage]);
      }
      setInputMessage('');
    } catch (err) {
      console.error('메시지 전송 실패:', err);
      alert('메시지 전송에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="chat-page">
      <Header
        showSidebar={isAuthenticated}
        onToggleSidebar={handleToggleSidebar}
      />

      <div className="chat-container">
        {/* Sidebar - 로그인 사용자만 */}
        {isAuthenticated && (
          <aside className={`chat-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
            <button onClick={handleNewConversation} className="btn-new-chat">+ 새 대화</button>
            <div className="conversation-list">
              {conversations.map(conv => (
                <div
                  key={conv.id}
                  className={`conversation-item ${selectedConversation?.id === conv.id ? 'active' : ''}`}
                  onClick={() => handleConversationClick(conv.id)}
                >
                  <div className="conversation-title">{conv.title || 'Untitled'}</div>
                  <div className="conversation-meta">
                    <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                    <span>{conv.message_count}개 메시지</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteConversation(conv.id);
                    }}
                    className="btn-delete"
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          </aside>
        )}

        {/* Main Chat Area */}
        <main className="chat-main">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>안녕하세요! MindCare입니다.</h2>
                <p>무엇을 도와드릴까요?</p>
                {!isAuthenticated && (
                  <p className="guest-warning">게스트 모드: 대화 내용이 저장되지 않습니다.</p>
                )}
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`}>
                  {/* Message Avatar */}
                  <div className="message-avatar">
                    {msg.role === 'user' ? (
                      user?.profile_image ? (
                        <img src={user.profile_image} alt="user" />
                      ) : (
                        <span className="avatar-placeholder">
                          {user?.username?.[0]?.toUpperCase() || 'U'}
                        </span>
                      )
                    ) : (
                      <span className="avatar-placeholder">AI</span>
                    )}
                  </div>

                  {/* Message Content */}
                  <div className="message-content-wrapper">
                    {msg.role === 'assistant' && msg.thinking_process && (
                      <div className="thinking-process">
                        {msg.thinking_process.map((node, i) => (
                          <div key={i} className="thinking-node">
                            💭 {node.description}
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="message-content">
                      {msg.content}
                    </div>
                    <div className="message-time">
                      {new Date(msg.created_at).toLocaleTimeString('ko-KR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              ))
            )}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="message assistant">
                <div className="message-avatar">
                  <span className="avatar-placeholder">AI</span>
                </div>
                <div className="message-content-wrapper">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input form - centered when no messages */}
          <div className={`message-input-container ${messages.length === 0 ? 'center' : ''}`}>
            <form onSubmit={handleSendMessage} className="message-input-form">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="메시지를 입력하세요..."
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading || !inputMessage.trim()}>
                전송
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}

export default ChatPage;
