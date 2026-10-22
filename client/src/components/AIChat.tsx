// Tasked: AI Enabled Task Manager - AI Chat

import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import type { AIChatMessage, AIChatResponse } from '../types';
import { api } from '../services/api';

interface AIChatProps {
  isOpen: boolean;
  onClose: () => void;
  onTasksChanged: () => void;
}

export function AIChat({ isOpen, onClose, onTasksChanged }: AIChatProps) {
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState<AIChatResponse['confirmation_details'] | null>(null);
  const [confirmationId, setConfirmationId] = useState<string | null>(null);
  const [aiHealth, setAiHealth] = useState<{ mock_mode: boolean; model: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const loadAIHealth = async () => {
    try {
      const health = await api.getAIHealth();
      setAiHealth({ mock_mode: health.gemini.mock_mode, model: health.gemini.model });
    } catch (err) {
      console.error('Failed to load AI health:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadAIHealth();
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: AIChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.chat(currentInput);

      // An AI turn may have created or changed tasks; refresh from the backend.
      onTasksChanged();

      if (response.requires_confirmation && response.confirmation_id && response.confirmation_details) {
        setPendingConfirmation(response.confirmation_details);
        setConfirmationId(response.confirmation_id);

        const assistantMessage: AIChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          isMock: response.is_mock,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        const assistantMessage: AIChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          isMock: response.is_mock,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err) {
      const errorMessage: AIChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to get AI response'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async (confirmed: boolean) => {
    if (!confirmationId) return;

    try {
      const response = await api.confirmAction({ confirmation_id: confirmationId, confirmed });
      onTasksChanged();

      const confirmMessage: AIChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, confirmMessage]);
    } catch (err) {
      const errorMessage: AIChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to confirm action'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setPendingConfirmation(null);
      setConfirmationId(null);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="ai-chat-overlay" onClick={onClose}>
      <div className="ai-chat-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ai-chat-header">
          <div className="ai-chat-title">
            <h2>AI Assistant</h2>
            {aiHealth?.mock_mode && <span className="mock-badge">Mock Mode</span>}
            {aiHealth && !aiHealth.mock_mode && (
              <span className="live-badge" title={aiHealth.model}>Gemini</span>
            )}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>×</button>
        </div>

        <div className="ai-chat-messages" role="log" aria-live="polite">
          {messages.map((msg) => (
            <div key={msg.id} className={`ai-message ${msg.role}`}>
              <div className="ai-message-content">
                {msg.isMock && <span className="mock-indicator">[MOCK] </span>}
                <pre>{msg.content}</pre>
              </div>
              <div className="ai-message-time">
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}
          {pendingConfirmation && (
            <div className="ai-message assistant confirmation">
              <div className="ai-message-content">
                <p><strong>Confirmation Required:</strong> {pendingConfirmation.action} task "{pendingConfirmation.task_identifier}"</p>
                <div className="confirmation-actions">
                  <button className="btn btn-danger btn-sm" onClick={() => handleConfirm(true)}>Confirm</button>
                  <button className="btn btn-secondary btn-sm" onClick={() => handleConfirm(false)}>Cancel</button>
                </div>
              </div>
            </div>
          )}
          {isLoading && (
            <div className="ai-message assistant loading">
              <div className="ai-message-content">
                <span className="typing-indicator">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="ai-chat-input">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your task request... (Shift+Enter for new line)"
            rows={2}
            disabled={isLoading || !!pendingConfirmation}
          />
          <button
            className="btn btn-primary"
            onClick={handleSend}
            disabled={!input.trim() || isLoading || !!pendingConfirmation}
          >
            Send
          </button>
        </div>

        <div className="ai-chat-hints">
          <p>Try: "Create a high-priority task to finish my report by Friday"</p>
          <p>Or: "Show my overdue tasks", "Mark DBMS assignment complete"</p>
        </div>
      </div>
    </div>
  );
}