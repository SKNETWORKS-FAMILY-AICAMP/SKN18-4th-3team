import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  getChatInfo,
  getConversations,
  createConversation,
  getConversationDetail,
  sendMessage,
  sendGuestMessage,
  deleteConversation,
} from "../api/chat";
import { buildAbsoluteMediaUrl } from "../utils/media";
import Header from "../components/Header";
import "./ChatPage.css";

function ChatPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [guestHistory, setGuestHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStopped, setIsStopped] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const [conversationState, setConversationState] = useState(null);
  const [requiresAnswer, setRequiresAnswer] = useState(false);
  const resetConversationFlow = () => {
    setConversationState(null);
    setRequiresAnswer(false);
  };

  useEffect(() => {
    loadChatInfo();
    // 메인에서 사이드바 토글을 통해 넘어온 경우
    if (location.state?.openSidebar) {
      setIsSidebarOpen(true);
    }
    // createNew로 넘어온 경우에도 사이드바 열기
    if (location.state?.createNew) {
      setIsSidebarOpen(true);
    }
  }, [location]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
      console.error("채팅 정보 로드 실패:", err);
    }
  };

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      console.error("대화 목록 로드 실패:", err);
    }
  };

  const handleConversationClick = async (conversationId) => {
    try {
      const data = await getConversationDetail(conversationId);
      setSelectedConversation(data);
      setMessages(data.messages);
      resetConversationFlow();
    } catch (err) {
      console.error("대화 세션 로드 실패:", err);
    }
  };

  const handleNewConversation = () => {
    // 대화 세션은 실제 메시지 전송 시 생성되므로 여기서는 초기화만
    setSelectedConversation(null);
    setMessages([]);
    resetConversationFlow();
  };

  const handleDeleteConversation = async (conversationId) => {
    if (!window.confirm("정말 이 대화를 삭제하시겠습니까?")) return;
    try {
      await deleteConversation(conversationId);
      setConversations(conversations.filter((c) => c.id !== conversationId));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
        setMessages([]);
        resetConversationFlow();
      }
    } catch (err) {
      console.error("대화 삭제 실패:", err);
    }
  };

  const handleStop = () => {
    setIsStopped(true);
    setIsLoading(false);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    setIsLoading(true);
    setIsStopped(false);
    const messageContent = inputMessage;
    const isAnswerMode = requiresAnswer;
    const statePayload = conversationState;
    setInputMessage("");

    try {
      if (isAuthenticated) {
        // 로그인 사용자
        const userMessage = {
          role: "user",
          content: messageContent,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);

        if (!selectedConversation) {
          // 대화 세션이 없으면 먼저 생성하지 않고, 메시지 전송 시 백엔드에서 자동 생성되도록
          // 임시 대화 세션 생성 (나중에 실제 대화 세션으로 교체)
          const tempConv = await createConversation();
          setSelectedConversation(tempConv);

          const data = await sendMessage(
            tempConv.id,
            messageContent,
            statePayload,
            isAnswerMode
          );
          if (!isStopped) {
            const updatedConvs = await getConversations();
            setConversations(updatedConvs);
            const actualConv =
              updatedConvs.find((c) => c.id === tempConv.id) || tempConv;
            setSelectedConversation(actualConv);
            if (data?.assistant_message) {
              setMessages((prev) => [...prev, data.assistant_message]);
            }
            setConversationState(data?.conversation_state || null);
            setRequiresAnswer(!!data?.requires_answer);
          }
        } else {
          const data = await sendMessage(
            selectedConversation.id,
            messageContent,
            statePayload,
            isAnswerMode
          );
          if (!isStopped) {
            if (data?.assistant_message) {
              setMessages((prev) => [...prev, data.assistant_message]);
            }
            setConversationState(data?.conversation_state || null);
            setRequiresAnswer(!!data?.requires_answer);
            loadConversations(); // 대화 목록 갱신
          }
        }
      } else {
        // 게스트 사용자
        const userMessage = {
          role: "user",
          content: messageContent,
          created_at: new Date().toISOString(),
        };
        const newHistory = [...guestHistory, userMessage];
        setMessages((prev) => [...prev, userMessage]);

        if (!isStopped) {
          const data = await sendGuestMessage(
            messageContent,
            statePayload,
            isAnswerMode,
            guestHistory
          );
          const assistantMessage = {
            role: "assistant",
            content: data.response,
            thinking_process: data.thinking_process,
            created_at: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, assistantMessage]);
          setGuestHistory([...newHistory, assistantMessage]);
          setConversationState(data?.conversation_state || null);
          setRequiresAnswer(!!data?.requires_answer);
        }
      }
    } catch (err) {
      console.error("메시지 전송 실패:", err);
      alert("메시지 전송에 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="chat-page">
      {/* Header - 페이지 최상단 고정 */}
      <Header
        showSidebar={true}
        onToggleSidebar={handleToggleSidebar}
        isSidebarOpen={isSidebarOpen}
      />

      {/* Sidebar - 헤더 아래 고정 */}
      {isSidebarOpen && (
        <aside className="chat-sidebar">
          <button onClick={handleNewConversation} className="sidebar-new">
            New Counseling
            <span className="material-symbols-outlined paper-plane-icon">
              send
            </span>
          </button>

          {/* 검색 기능 - 로그인 사용자만 */}
          {isAuthenticated && (
            <div className="sidebar-search">
              <input
                type="text"
                placeholder="대화 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <span className="material-symbols-outlined search-icon">
                search
              </span>
            </div>
          )}

          <div className="sidebar-list">
            {!isAuthenticated ? (
              <div className="sidebar-empty">
                게스트 모드: 대화 내용이 저장되지 않습니다.
              </div>
            ) : conversations.length === 0 ? (
              <div className="sidebar-empty">대화 기록이 없습니다.</div>
            ) : (
              conversations
                .filter((conv) =>
                  searchQuery
                    ? conv.title
                        ?.toLowerCase()
                        .includes(searchQuery.toLowerCase()) ||
                      conv.last_message_preview
                        ?.toLowerCase()
                        .includes(searchQuery.toLowerCase())
                    : true
                )
                .map((conv) => (
                  <div
                    key={conv.id}
                    className={`sidebar-item ${
                      selectedConversation?.id === conv.id ? "active" : ""
                    }`}
                    onClick={() => handleConversationClick(conv.id)}
                  >
                    <strong>{conv.title || "제목 없음"}</strong>
                    <span className="sidebar-meta">
                      {conv.updated_at
                        ? new Date(conv.updated_at).toLocaleString()
                        : ""}
                    </span>
                    {/* 감정 퍼센테이지 바 */}
                    {conv.sentiment_percentages && (
                      <div className="sidebar-sentiment-bar">
                        <div className="sentiment-tooltip">
                          <strong>나쁨</strong>{" "}
                          {conv.sentiment_percentages.negative}% |{" "}
                          <strong>중립</strong>{" "}
                          {conv.sentiment_percentages.neutral}% |{" "}
                          <strong>기쁨</strong>{" "}
                          {conv.sentiment_percentages.positive}%
                        </div>
                        {conv.sentiment_percentages.negative > 0 && (
                          <div
                            className="sentiment-segment negative"
                            style={{
                              width: `${conv.sentiment_percentages.negative}%`,
                            }}
                          />
                        )}
                        {conv.sentiment_percentages.neutral > 0 && (
                          <div
                            className="sentiment-segment neutral"
                            style={{
                              width: `${conv.sentiment_percentages.neutral}%`,
                            }}
                          />
                        )}
                        {conv.sentiment_percentages.positive > 0 && (
                          <div
                            className="sentiment-segment positive"
                            style={{
                              width: `${conv.sentiment_percentages.positive}%`,
                            }}
                          />
                        )}
                      </div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteConversation(conv.id);
                      }}
                      className="sidebar-delete-btn"
                      aria-label="삭제"
                    >
                      <span className="material-symbols-outlined">delete</span>
                    </button>
                  </div>
                ))
            )}
          </div>
        </aside>
      )}

      {/* Main Chat Area - 헤더 아래, 사이드바 옆 */}
      <main className={`chat-main ${isSidebarOpen ? "sidebar-open" : ""}`}>
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>안녕하세요! MindCare입니다.</h2>
              <p>무엇을 도와드릴까요?</p>
              {!isAuthenticated && (
                <p className="guest-warning">
                  게스트 모드: 대화 내용이 저장되지 않습니다.
                </p>
              )}
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                {/* Message Avatar */}
                <div className="message-avatar">
                  {msg.role === "user" ? (
                    user?.profile_image ? (
                      <img
                        src={buildAbsoluteMediaUrl(user.profile_image)}
                        alt="user"
                        className="avatar-image"
                      />
                    ) : (
                      <div className="avatar-placeholder">
                        {user?.username?.charAt(0).toUpperCase() || "U"}
                      </div>
                    )
                  ) : (
                    <span className="avatar-placeholder">AI</span>
                  )}
                </div>

                {/* Message Content */}
                <div className="message-content-wrapper">
                  {msg.role === "assistant" && msg.thinking_process && (
                    <div className="thinking-process">
                      {msg.thinking_process.map((node, i) => (
                        <div key={i} className="thinking-node">
                          <span className="material-symbols-outlined thinking-icon">
                            cloud
                          </span>
                          <span>{node.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="message-content">{msg.content}</div>
                  <div className="message-time">
                    {new Date(msg.created_at).toLocaleTimeString("ko-KR", {
                      hour: "2-digit",
                      minute: "2-digit",
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

        {/* Input form - 하단 고정 */}
        <div
          className={`message-input-container ${
            messages.length === 0 ? "center" : ""
          }`}
        >
          <form onSubmit={handleSendMessage} className="message-input-form">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
            />
            <button
              type={isLoading ? "button" : "submit"}
              disabled={!inputMessage.trim() && !isLoading}
              onClick={isLoading ? handleStop : undefined}
              className={isLoading ? "loading" : ""}
            >
              {isLoading ? <span className="stop-icon">■</span> : "전송"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
