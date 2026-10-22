// Tasked: AI Enabled Task Manager - Task List

import { useState } from 'react';
import type { Task } from '../types';
import { api } from '../services/api';
import { formatDate } from '../utils/date';

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  onEdit: (task: Task) => void;
  onChanged: () => void;
  onPageChange: (page: number) => void;
  currentPage: number;
  totalPages: number;
}

export function TaskList({
  tasks,
  isLoading,
  onEdit,
  onChanged,
  onPageChange,
  currentPage,
  totalPages,
}: TaskListProps) {
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);

  const runAction = async (taskId: string, action: () => Promise<unknown>) => {
    setBusyTaskId(taskId);
    try {
      await action();
      onChanged();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setBusyTaskId(null);
    }
  };

  const handleDelete = async (task: Task) => {
    const confirmed = window.confirm(
      `Delete "${task.title}"? This removes it from your lists.`
    );
    if (!confirmed) return;
    await runAction(task.id, () => api.deleteTask(task.id));
  };

  if (isLoading) {
    return <div className="task-list-loading">Loading tasks...</div>;
  }

  if (tasks.length === 0) {
    return (
      <div className="task-list-empty">
        <p>No tasks found.</p>
        <p className="hint">Create your first task or adjust your filters.</p>
      </div>
    );
  }

  return (
    <div className="task-list">
      <div className="task-list-header">
        <h2>Tasks ({tasks.length})</h2>
      </div>

      <div className="task-table-container">
        <table className="task-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Due Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => {
              const busy = busyTaskId === task.id;
              return (
                <tr key={task.id} className={task.is_archived ? 'archived' : ''}>
                  <td className="task-title">
                    <strong>{task.title}</strong>
                    {task.description && <p className="task-description">{task.description}</p>}
                  </td>
                  <td>
                    <span className={`badge badge-status badge-${task.status}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-priority badge-${task.priority}`}>
                      {task.priority}
                    </span>
                  </td>
                  <td className={task.is_overdue ? 'overdue' : ''}>
                    {task.due_at ? formatDate(task.due_at) : '—'}
                    {task.is_overdue && <span className="overdue-badge">Overdue</span>}
                  </td>
                  <td>
                    <div className="task-actions">
                      {task.status === 'pending' && !task.is_archived && (
                        <button
                          className="btn btn-sm btn-secondary"
                          disabled={busy}
                          onClick={() =>
                            runAction(task.id, () =>
                              api.updateTask(task.id, { status: 'in_progress' })
                            )
                          }
                        >
                          Start
                        </button>
                      )}
                      {task.status !== 'completed' && !task.is_archived && (
                        <button
                          className="btn btn-sm btn-success"
                          disabled={busy}
                          onClick={() => runAction(task.id, () => api.completeTask(task.id))}
                        >
                          Complete
                        </button>
                      )}
                      {task.status === 'completed' && (
                        <button
                          className="btn btn-sm btn-secondary"
                          disabled={busy}
                          onClick={() => runAction(task.id, () => api.reopenTask(task.id))}
                        >
                          Reopen
                        </button>
                      )}
                      {task.is_archived ? (
                        <button
                          className="btn btn-sm btn-secondary"
                          disabled={busy}
                          onClick={() => runAction(task.id, () => api.restoreTask(task.id))}
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          className="btn btn-sm btn-secondary"
                          disabled={busy}
                          onClick={() => runAction(task.id, () => api.archiveTask(task.id))}
                        >
                          Archive
                        </button>
                      )}
                      <button
                        className="btn btn-sm btn-secondary"
                        disabled={busy}
                        onClick={() => onEdit(task)}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        disabled={busy}
                        onClick={() => handleDelete(task)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
          >
            Previous
          </button>
          <span className="pagination-info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}