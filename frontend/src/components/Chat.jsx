import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import './Chat.css';

export default function Chat({ userId }) {
  const [messages, setMessages] = useState(() => {
    const saved = sessionStorage.getItem('chat_messages');
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (messages.length > 0 && messages[0].text !== "Loading your welcome summary...") {
      sessionStorage.setItem('chat_messages', JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    if (messages.length === 1 && messages[0].text === "Loading your welcome summary...") {
      const fetchWelcome = async () => {
        try {
          const response = await fetch(`http://localhost:8000/api/chat/welcome/${userId}`);
          if (response.ok) {
            const data = await response.json();
            setMessages([{
              id: 'welcome-' + Date.now(),
              role: 'assistant',
              text: data.message
            }]);
          } else {
              setMessages([{ id: 'err-1', role: 'assistant', text: "Welcome back! (Offline mode)" }]);
          }
        } catch (e) {
          console.error("Failed to fetch welcome message", e);
          setMessages([{ id: 'err-2', role: 'assistant', text: "Welcome back! (Could not reach API)" }]);
        }
      };
      fetchWelcome();
    }
  }, []);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim()) return;

    const userText = inputValue;
    const newUserMsg = { id: Date.now().toString(), role: 'user', text: userText };
    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`http://localhost:8000/api/chat/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userText })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: data.reply
        }]);
      } else {
          setMessages(prev => [...prev, {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            text: "Sorry, I ran into an error processing your request."
          }]);
      }
    } catch (error) {
       console.error("Chat API error", error);
       setMessages(prev => [...prev, {
         id: (Date.now() + 1).toString(),
         role: 'assistant',
         text: "Make sure the MemoryVest backend API is running!"
       }]);
    } finally {
       setIsTyping(false);
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
          />
          <button type="submit" disabled={!inputValue.trim()} className={inputValue.trim() ? 'active' : ''}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
