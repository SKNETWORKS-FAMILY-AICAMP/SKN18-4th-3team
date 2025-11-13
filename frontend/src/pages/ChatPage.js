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
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

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
    } catch (err) {
      console.error("대화 세션 로드 실패:", err);
    }
  };

  const handleNewConversation = () => {
    // 대화 세션은 실제 메시지 전송 시 생성되므로 여기서는 초기화만
    setSelectedConversation(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (conversationId) => {
    if (!window.confirm("정말 이 대화를 삭제하시겠습니까?")) return;
    try {
      await deleteConversation(conversationId);
      setConversations(conversations.filter((c) => c.id !== conversationId));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
        setMessages([]);
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
    setInputMessage("");

    try {
      if (isAuthenticated) {
        // 로그인 사용자
        const userMessage = {
          role: "user",
          content: messageContent,
          created_at: new Date().toISOString(),
        };
        setMessages([...messages, userMessage]);

        if (!selectedConversation) {
          // 대화 세션이 없으면 먼저 생성하지 않고, 메시지 전송 시 백엔드에서 자동 생성되도록
          // 임시 대화 세션 생성 (나중에 실제 대화 세션으로 교체)
          const tempConv = await createConversation();
          setSelectedConversation(tempConv);

          const data = await sendMessage(tempConv.id, messageContent);
          if (!isStopped) {
            // 사용자-에이전트 한쌍이 생성되었으므로 대화 목록 갱신
            await loadConversations();
            // 실제 생성된 대화 세션으로 업데이트
            const updatedConvs = await getConversations();
            const actualConv =
              updatedConvs.find((c) => c.id === tempConv.id) || tempConv;
            setSelectedConversation(actualConv);
            setMessages([userMessage, data.assistant_message]);
          }
        } else {
          const data = await sendMessage(
            selectedConversation.id,
            messageContent
          );
          if (!isStopped) {
            setMessages([...messages, userMessage, data.assistant_message]);
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
        setMessages([...messages, userMessage]);

        if (!isStopped) {
          const data = await sendGuestMessage(messageContent, guestHistory);
          const assistantMessage = {
            role: "assistant",
            content: data.response,
            thinking_process: data.thinking_process,
            created_at: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, assistantMessage]);
          setGuestHistory([...newHistory, assistantMessage]);
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
        showSidebar={isAuthenticated}
        onToggleSidebar={handleToggleSidebar}
        isSidebarOpen={isSidebarOpen}
      />

      {/* Sidebar - 로그인 사용자만, 헤더 아래 고정 */}
      {isAuthenticated && isSidebarOpen && (
        <aside className="chat-sidebar">
          <button onClick={handleNewConversation} className="sidebar-new">
            New Counseling
            <span className="material-symbols-outlined paper-plane-icon">
              send
            </span>
          </button>
          <div className="sidebar-list">
            {conversations.length === 0 ? (
              <div className="sidebar-empty">대화 기록이 없습니다.</div>
            ) : (
              conversations.map((conv) => (
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
                  <span className="sidebar-snippet">
                    {conv.last_message_preview || "대화 내용을 요약합니다."}
                  </span>
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
      <main
        className={`chat-main ${
          isAuthenticated && isSidebarOpen ? "sidebar-open" : ""
        }`}
      >
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
