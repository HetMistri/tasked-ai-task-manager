// Tasked: AI Enabled Task Manager - Header

import type { User } from '../types';

interface HeaderProps {
  user: User;
  onLogout: () => void;
  onToggleAI: () => void;
  aiChatOpen: boolean;
}

export function Header({ user, onLogout, onToggleAI, aiChatOpen }: HeaderProps) {
  return (
    <header className="dashboard-header">
      <div className="header-left">
        <h1>Tasked</h1>
        <span className="header-subtitle">AI Enabled Task Manager</span>
      </div>
      <div className="header-right">
        <button
          className={`btn ${aiChatOpen ? 'btn-primary' : 'btn-secondary'}`}
          onClick={onToggleAI}
          aria-label="Toggle AI Chat"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span>AI Chat</span>
        </button>
        <div className="user-menu">
          <span className="user-name">{user.display_name}</span>
          <button className="btn btn-ghost" onClick={onLogout}>Logout</button>
        </div>
      </div>
    </header>
  );
}