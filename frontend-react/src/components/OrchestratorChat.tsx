import React, { useEffect, useState } from 'react';
import { chatWithOrchestrator, getOrchestratorChatHealth } from '../api/orchestrator';

interface ChatMessage {
  sender: 'user' | 'orchestrator';
  message: string;
}

const OrchestratorChat: React.FC = () => {
  const [message, setMessage] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [healthStatus, setHealthStatus] = useState<string>('Checking...');
  const [sessionId] = useState<string>(`session-${Date.now()}`);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await getOrchestratorChatHealth();
        setHealthStatus(response.success ? 'Online' : `Degraded: ${response.message || 'Unknown error'}`);
      } catch (error) {
        setHealthStatus('Offline');
        console.error('Orchestrator chat health check failed:', error);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const userMessage: ChatMessage = { sender: 'user', message: message.trim() };
    setChatHistory((prev) => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const response = await chatWithOrchestrator({ message: userMessage.message, session_id: sessionId });
      const orchestratorMessage: ChatMessage = {
        sender: 'orchestrator',
        message: response.data ? JSON.stringify(response.data, null, 2) : response.message || 'No response data',
      };
      setChatHistory((prev) => [...prev, orchestratorMessage]);
    } catch (error: any) {
      console.error('Failed to chat with orchestrator:', error);
      const errorMessage: ChatMessage = {
        sender: 'orchestrator',
        message: `Error: ${error.message || 'Could not reach orchestrator.'}`,
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      <h1>Orchestrator Chat</h1>
      <p>Health Status: <strong>{healthStatus}</strong></p>

      <div style={{ border: '1px solid #ccc', height: '400px', overflowY: 'scroll', padding: '10px', marginBottom: '10px', backgroundColor: '#f9f9f9' }}>
        {chatHistory.map((msg, index) => (
          <div key={index} style={{ marginBottom: '10px', textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
            <strong style={{ color: msg.sender === 'user' ? '#007bff' : '#28a745' }}>{msg.sender}:</strong>
            <div style={{
              backgroundColor: msg.sender === 'user' ? '#e0f7fa' : '#e6ffe6',
              padding: '8px',
              borderRadius: '8px',
              display: 'inline-block',
              maxWidth: '70%',
              wordBreak: 'break-word',
              whiteSpace: 'pre-wrap',
            }}>
              {msg.message}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'left', color: '#6c757d' }}>
            <em>Orchestrator is thinking...</em>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <textarea
          style={{ flexGrow: 1, padding: '10px', borderRadius: '5px', border: '1px solid #ccc', resize: 'vertical' }}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          placeholder="Type your message..."
          rows={3}
          disabled={loading}
        />
        <button
          style={{ padding: '10px 20px', borderRadius: '5px', border: 'none', backgroundColor: '#007bff', color: 'white', cursor: 'pointer' }}
          onClick={handleSendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default OrchestratorChat;
