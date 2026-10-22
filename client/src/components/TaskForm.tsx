// Tasked: AI Enabled Task Manager - Create / edit task form

import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import type { Task, TaskPriority, TaskStatus } from '../types';
import { api } from '../services/api';

interface TaskFormProps {
  task?: Task | null;
  onClose: () => void;
  onSuccess: () => void;
}

interface FormState {
  title: string;
  description: string;
  priority: TaskPriority;
  due_at: string;
  status?: TaskStatus;
  is_archived: boolean;
}

function toFormState(task?: Task | null): FormState {
  return {
    title: task?.title ?? '',
    description: task?.description ?? '',
    priority: task?.priority ?? 'medium',
    // datetime-local inputs need "YYYY-MM-DDTHH:mm" in local time.
    due_at: task?.due_at ? toLocalInputValue(task.due_at) : '',
    status: task?.status,
    is_archived: task?.is_archived ?? false,
  };
}

function toLocalInputValue(isoDate: string): string {
  const date = new Date(isoDate);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

export function TaskForm({ task, onClose, onSuccess }: TaskFormProps) {
  const isEditing = Boolean(task);
  const [form, setForm] = useState<FormState>(() => toFormState(task));
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setForm(toFormState(task));
  }, [task]);

  const update = <K extends keyof FormState>(field: K, value: FormState[K]) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    const dueAt = form.due_at ? new Date(form.due_at).toISOString() : null;

    try {
      if (isEditing && task) {
        await api.updateTask(task.id, {
          title: form.title,
          description: form.description || undefined,
          status: form.status,
          priority: form.priority,
          due_at: dueAt,
          is_archived: form.is_archived,
        });
      } else {
        await api.createTask({
          title: form.title,
          description: form.description || undefined,
          priority: form.priority,
          due_at: dueAt ?? undefined,
        });
      }
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save task');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="task-form-overlay" onClick={onClose}>
      <div className="task-form-modal" onClick={(event) => event.stopPropagation()}>
        <div className="task-form-header">
          <h2>{isEditing ? 'Edit Task' : 'Create Task'}</h2>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            ×
          </button>
        </div>

        {error && <div className="form-error">{error}</div>}

        <form onSubmit={handleSubmit} className="task-form">
          <div className="form-group">
            <label htmlFor="title">Title *</label>
            <input
              id="title"
              type="text"
              value={form.title}
              onChange={(event) => update('title', event.target.value)}
              required
              maxLength={255}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={form.description}
              onChange={(event) => update('description', event.target.value)}
              maxLength={5000}
              rows={4}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="priority">Priority</label>
              <select
                id="priority"
                value={form.priority}
                onChange={(event) => update('priority', event.target.value as TaskPriority)}
                disabled={isSubmitting}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="due_at">Due Date</label>
              <input
                id="due_at"
                type="datetime-local"
                value={form.due_at}
                onChange={(event) => update('due_at', event.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {isEditing && (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="status">Status</label>
                <select
                  id="status"
                  value={form.status ?? 'pending'}
                  onChange={(event) => update('status', event.target.value as TaskStatus)}
                  disabled={isSubmitting}
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={form.is_archived}
                    onChange={(event) => update('is_archived', event.target.checked)}
                    disabled={isSubmitting}
                  />
                  Archived
                </label>
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}