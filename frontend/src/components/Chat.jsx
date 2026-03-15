import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import './Chat.css';
import API_BASE from '../config.js';

// Module-level store — survives component unmount/remount
// Keeps in-flight AI reply promises alive even when the user navigates away
const pendingReply = {}; // { [userId]: Promise<{id, role, text}> | null }

export default function Chat({ userId }) {
  const storageKey = `chat_messages_${userId}`;
  const [messages, setMessages] = useState(() => {
    const saved = sessionStorage.getItem(storageKey);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.length > 0) return parsed;
      } catch (e) {}
    }
    return [{ id: '1', role: 'assistant', text: "Loading your welcome summary..." }];
  });
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Persist messages to sessionStorage whenever they change
  useEffect(() => {
    if (messages.length > 0 && messages[0].text !== "Loading your welcome summary...") {
      sessionStorage.setItem(storageKey, JSON.stringify(messages));
    }
  }, [messages]);

  // On mount: fetch welcome message if needed, and re-subscribe to any in-flight reply
  useEffect(() => {
    // Restore welcome message
    if (messages.length === 1 && messages[0].text === "Loading your welcome summary...") {
      const fetchWelcome = async () => {
        try {
          const response = await fetch(`${API_BASE}/api/chat/welcome/${userId}`);
          if (response.ok) {
            const data = await response.json();
            if (mountedRef.current) {
              setMessages([{ id: 'welcome-' + Date.now(), role: 'assistant', text: data.message }]);
            }
          } else {
            if (mountedRef.current) {
              setMessages([{ id: 'err-1', role: 'assistant', text: "Welcome back! (Offline mode)" }]);
            }
          }
        } catch (e) {
          console.error("Failed to fetch welcome message", e);
          if (mountedRef.current) {
            setMessages([{ id: 'err-2', role: 'assistant', text: "Welcome back! (Could not reach API)" }]);
          }
        }
      };
      fetchWelcome();
    }

    // If a reply was in-flight when user navigated away, re-subscribe so it shows on return
    if (pendingReply[userId]) {
      if (mountedRef.current) setIsTyping(true);
      pendingReply[userId].then(replyMsg => {
        if (mountedRef.current && replyMsg) {
          setMessages(prev => {
            // Avoid adding duplicate if it was already written to sessionStorage before remount
            if (prev.some(m => m.id === replyMsg.id)) return prev;
            return [...prev, replyMsg];
          });
        }
      }).finally(() => {
        if (mountedRef.current) setIsTyping(false);
      });
    }
  }, [userId]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim() || pendingReply[userId]) return; // Prevent sending while reply pending

    const userText = inputValue;
    const userMsg = { id: Date.now().toString(), role: 'user', text: userText };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    const replyPromise = fetch(`${API_BASE}/api/chat/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText })
    }).then(async response => {
      const replyId = (Date.now() + 1).toString();
      if (response.ok) {
        const data = await response.json();
        return { id: replyId, role: 'assistant', text: data.reply };
      } else {
        return { id: replyId, role: 'assistant', text: "Sorry, I ran into an error processing your request." };
      }
    }).catch(error => {
      console.error("Chat API error", error);
      return { id: (Date.now() + 1).toString(), role: 'assistant', text: "Make sure the MemoryVest backend API is running!" };
    }).then(replyMsg => {
      // Always persist to sessionStorage so it survives navigation
      try {
        const saved = sessionStorage.getItem('chat_messages');
        const existing = saved ? JSON.parse(saved) : [];
        if (!existing.some(m => m.id === replyMsg.id)) {
          sessionStorage.setItem('chat_messages', JSON.stringify([...existing, replyMsg]));
        }
      } catch (e) {}
      return replyMsg;
    }).finally(() => {
      delete pendingReply[userId];
      if (mountedRef.current) setIsTyping(false);
    });

    // Register globally — the reply will complete even if the component unmounts
    pendingReply[userId] = replyPromise;

    const replyMsg = await replyPromise;
    if (mountedRef.current) {
      setMessages(prev => {
        if (prev.some(m => m.id === replyMsg.id)) return prev; // skip if re-subscribed already added it
        return [...prev, replyMsg];
      });
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message-wrapper ${msg.role === 'assistant' ? 'assistant-wrapper' : 'user-wrapper'}`}>
            <div className={`message-avatar ${msg.role}`}>
              {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
            </div>
            <div className={`message-bubble ${msg.role} glass-panel slide-up`}>
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message-wrapper assistant-wrapper fade-in">
            <div className="message-avatar assistant">
              <Bot size={20} />
            </div>
            <div className="message-bubble assistant glass-panel typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <form onSubmit={handleSend} className="chat-input-wrapper glass-panel">
          <input
            type="text"
            placeholder="Tell MemoryVest about your portfolio..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={!!pendingReply[userId]}
          />
          <button type="submit" disabled={!inputValue.trim() || !!pendingReply[userId]} className={inputValue.trim() && !pendingReply[userId] ? 'active' : ''}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
