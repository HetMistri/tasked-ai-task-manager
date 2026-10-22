// Tasked: AI Enabled Task Manager - Dashboard

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { TaskList } from './TaskList';
import { TaskForm } from './TaskForm';
import { AIChat } from './AIChat';
import { Header } from './Header';
import { FilterBar } from './FilterBar';
import type { Task, FilterState, TaskSummary } from '../types';
import { api } from '../services/api';

export function Dashboard() {
  const { user, logout } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [summary, setSummary] = useState<TaskSummary | null>(null);
  const [filters, setFilters] = useState<FilterState>({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [aiChatOpen, setAiChatOpen] = useState(false);

  const loadTasks = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.getTasks(page, 20, filters);
      setTasks(response.tasks);
      setTotalPages(response.total_pages);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setIsLoading(false);
    }
  }, [page, filters]);

  const loadSummary = useCallback(async () => {
    try {
      setSummary(await api.getTaskSummary());
    } catch (err) {
      console.error('Failed to load summary:', err);
    }
  }, []);

  const refresh = useCallback(() => {
    loadTasks();
    loadSummary();
  }, [loadTasks, loadSummary]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    setPage(1);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="dashboard">
      <Header
        user={user}
        onLogout={logout}
        onToggleAI={() => setAiChatOpen(!aiChatOpen)}
        aiChatOpen={aiChatOpen}
      />

      <main className="dashboard-main">
        <aside className="sidebar">
          <FilterBar filters={filters} onChange={handleFiltersChange} summary={summary} />
          <div className="sidebar-actions">
            <button className="btn btn-primary btn-block" onClick={() => setShowCreateForm(true)}>
              + New Task
            </button>
          </div>
        </aside>

        <section className="content">
          {showCreateForm && (
            <TaskForm
              onClose={() => setShowCreateForm(false)}
              onSuccess={() => {
                setShowCreateForm(false);
                refresh();
              }}
            />
          )}

          {editingTask && (
            <TaskForm
              task={editingTask}
              onClose={() => setEditingTask(null)}
              onSuccess={() => {
                setEditingTask(null);
                refresh();
              }}
            />
          )}

          <TaskList
            tasks={tasks}
            isLoading={isLoading}
            onEdit={setEditingTask}
            onChanged={refresh}
            onPageChange={setPage}
            currentPage={page}
            totalPages={totalPages}
          />
        </section>
      </main>

      <AIChat
        isOpen={aiChatOpen}
        onClose={() => setAiChatOpen(false)}
        onTasksChanged={refresh}
      />
    </div>
  );
}