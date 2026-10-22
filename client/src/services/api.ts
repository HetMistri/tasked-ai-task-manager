// Tasked: AI Enabled Task Manager - API Service

import type {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskListResponse,
  TaskSummary,
  User,
  Token,
  AIChatResponse,
  AIConfirmRequest,
  AIConfirmResponse,
  AIHealthResponse,
  ActivityListResponse,
  Activity,
  FilterState,
} from '../types';

const API_BASE = '/api';
const AI_BASE = '/ai';

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  private async aiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${AI_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'AI request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async register(email: string, password: string, displayName: string, timezone = 'UTC'): Promise<Token> {
    return this.request<Token>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name: displayName, timezone }),
    });
  }

  async login(email: string, password: string): Promise<Token> {
    return this.request<Token>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Tasks
  async getTasks(
    page = 1,
    pageSize = 20,
    filters: FilterState = {}
  ): Promise<TaskListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (filters.status) params.append('status', filters.status);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.is_archived !== undefined) params.append('is_archived', filters.is_archived.toString());
    if (filters.search) params.append('search', filters.search);

    return this.request<TaskListResponse>(`/tasks?${params.toString()}`);
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}`);
  }

  async createTask(task: TaskCreate): Promise<Task> {
    return this.request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  async updateTask(taskId: string, task: TaskUpdate): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(task),
    });
  }

  async completeTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}/complete`, {
      method: 'POST',
    });
  }

  async reopenTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}/reopen`, {
      method: 'POST',
    });
  }

  async setTaskPriority(taskId: string, priority: Task['priority']): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}/priority`, {
      method: 'POST',
      body: JSON.stringify({ priority }),
    });
  }

  async archiveTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}/archive`, {
      method: 'POST',
    });
  }

  async restoreTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}/restore`, {
      method: 'POST',
    });
  }

  async deleteTask(taskId: string): Promise<void> {
    return this.request<void>(`/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async getTaskSummary(): Promise<TaskSummary> {
    return this.request<TaskSummary>('/tasks/summary');
  }

  // AI
  async chat(message: string): Promise<AIChatResponse> {
    return this.aiRequest<AIChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  async confirmAction(request: AIConfirmRequest): Promise<AIConfirmResponse> {
    return this.aiRequest<AIConfirmResponse>(`/actions/${request.confirmation_id}/confirm`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getAIHealth(): Promise<AIHealthResponse> {
    return this.aiRequest<AIHealthResponse>('/health');
  }

  // Activity
  async getActivity(page = 1, pageSize = 20, taskId?: string): Promise<ActivityListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (taskId) params.append('task_id', taskId);

    return this.request<ActivityListResponse>(`/activity?${params.toString()}`);
  }

  async getTaskActivity(taskId: string): Promise<Activity[]> {
    return this.request<Activity[]>(`/activity/tasks/${taskId}`);
  }

  // Health
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }
}

export const api = new ApiService();