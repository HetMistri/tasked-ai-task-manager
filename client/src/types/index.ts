// Tasked: AI Enabled Task Manager - TypeScript types

export type TaskStatus = 'pending' | 'in_progress' | 'completed';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_at: string | null;
  is_archived: boolean;
  archived_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  is_overdue: boolean;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: TaskPriority;
  due_at?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_at?: string | null;
  is_archived?: boolean;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskSummary {
  total: number;
  completed: number;
  pending: number;
  in_progress: number;
  archived: number;
  overdue: number;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  timezone: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AIChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isMock?: boolean;
}

export interface AIChatResponse {
  response: string;
  requires_confirmation: boolean;
  confirmation_id?: string;
  confirmation_details?: {
    action: string;
    task_identifier: string;
  };
  is_mock: boolean;
}

export interface AIConfirmRequest {
  confirmation_id: string;
  confirmed: boolean;
}

export interface AIConfirmResponse {
  success: boolean;
  message: string;
  task_id?: string;
}

export interface AIHealthResponse {
  status: string;
  gemini: {
    enabled: boolean;
    configured: boolean;
    model: string;
    mock_mode: boolean;
  };
  task_api: {
    url: string;
    healthy: boolean;
  };
}

export interface Activity {
  id: string;
  user_id: string;
  task_id: string | null;
  action_type: string;
  source: 'manual' | 'ai';
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  outcome: 'success' | 'failure' | 'cancelled';
  error_message: string | null;
  created_at: string;
}

export interface ActivityListResponse {
  activities: Activity[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type FilterState = {
  status?: TaskStatus;
  priority?: TaskPriority;
  is_archived?: boolean;
  search?: string;
};