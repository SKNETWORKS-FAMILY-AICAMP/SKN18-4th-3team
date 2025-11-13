import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Header from "../components/Header";
import Sphere2D from "../components/Sphere2D";
import { getChatInfo, getConversations } from "../api/chat";
import "./MainPage.css";

function MainPage() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [displayedText, setDisplayedText] = useState("");
  const fullText = useMemo(() => {
    if (isAuthenticated && user?.username) {
      return `안녕하세요, ${user.username}님!\n오늘 마음이 어떠신가요?\n편하게 이야기를 시작해보세요.`;
    }
    return "안녕하세요, 오늘 마음이 어떠신가요?\n편하게 이야기를 시작해보세요.";
  }, [isAuthenticated, user]);

  // 인사말 부분의 끝 인덱스 계산 (로그인 시 첫 번째 \n 전까지)
  const greetingEndIndex = useMemo(() => {
    if (isAuthenticated && user?.username) {
      const greeting = `안녕하세요, ${user.username}님!`;
      return greeting.length;
    }
    return -1; // 비로그인 시에는 인사말 부분 없음
  }, [isAuthenticated, user]);

  const [textIndex, setTextIndex] = useState(0);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const data = await getChatInfo();
        setIsAuthenticated(data.is_authenticated);
        setUser(data.user);
        if (data.is_authenticated) {
          const convs = await getConversations();
          setConversations(convs);
        }
      } catch (err) {
        console.error("메인 정보 로드 실패:", err);
      }
    };
    fetchInfo();
  }, []);

  // fullText가 변경되면 타입라이터 효과 재시작
  useEffect(() => {
    setDisplayedText("");
    setTextIndex(0);
  }, [fullText]);

  useEffect(() => {
    if (textIndex < fullText.length) {
      const delay = fullText[textIndex] === " " ? 40 : 70;
      const timeout = setTimeout(() => {
        setDisplayedText((prev) => prev + fullText[textIndex]);
        setTextIndex((prev) => prev + 1);
      }, delay);
      return () => clearTimeout(timeout);
    }
  }, [textIndex, fullText]);

  const handleToggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
  };

  const handleStart = () => {
    if (isAuthenticated) {
      navigate("/chat");
    } else {
      navigate("/login");
    }
  };

  const handleNewCounseling = () => {
    navigate("/chat", { state: { createNew: true, openSidebar: true } });
  };

  const handleConversationSelect = (conversationId) => {
    navigate("/chat", { state: { openSidebar: true, conversationId } });
  };

  return (
    <div className="main-page">
      <Header
        showSidebar
        onToggleSidebar={handleToggleSidebar}
        isSidebarOpen={isSidebarOpen}
      />

      <div className="main-body">
        {isSidebarOpen && (
          <aside className={`main-sidebar ${isSidebarOpen ? "open" : ""}`}>
            {isAuthenticated && (
              <button className="sidebar-new" onClick={handleNewCounseling}>
                New Counseling
                <span className="material-symbols-outlined paper-plane-icon">
                  send
                </span>
              </button>
            )}
            <div className="sidebar-list">
              {!isAuthenticated ? (
                <div className="sidebar-empty">로그인이 필요합니다.</div>
              ) : conversations.length === 0 ? (
                <div className="sidebar-empty">대화 기록이 없습니다.</div>
              ) : (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    className="sidebar-item"
                    onClick={() => handleConversationSelect(conv.id)}
                  >
                    <strong>{conv.title || "제목 없음"}</strong>
                    <span className="sidebar-meta">
                      {conv.updated_at
                        ? new Date(conv.updated_at).toLocaleString()
                        : ""}
                    </span>
                    <span className="sidebar-snippet">
                      {conv.last_message_preview ||
                        conv.last_message?.content ||
                        "대화 내용을 요약합니다."}
                    </span>
                  </button>
                ))
              )}
            </div>
            <div className="sidebar-fade-top" />
            <div className="sidebar-fade-bottom" />
          </aside>
        )}

        <main className="main-content">
          <div className="typewriter-section">
            <div className="message-text">
              {displayedText.split("").map((char, index) => {
                const isGreeting =
                  greetingEndIndex > 0 && index < greetingEndIndex;
                return (
                  <span
                    key={`${char}-${index}`}
                    style={{ animationDelay: `${index * 0.05}s` }}
                    className={
                      char === "\n"
                        ? "line-break"
                        : isGreeting
                        ? "greeting-text"
                        : ""
                    }
                  >
                    {char === "\n" ? <br /> : char}
                  </span>
                );
              })}
              <span
                className="cursor"
                style={{
                  opacity:
                    displayedText.length === fullText.length &&
                    fullText.length > 0
                      ? 1
                      : 0,
                }}
              />
            </div>
          </div>

          <motion.div
            className="sphere-section"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.3 }}
          >
            <Sphere2D onClick={handleStart} />
          </motion.div>
        </main>
      </div>
    </div>
  );
}

export default MainPage;
