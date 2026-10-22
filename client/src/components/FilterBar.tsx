// Tasked: AI Enabled Task Manager - Filter Bar

import type { FilterState, TaskSummary, TaskStatus, TaskPriority } from '../types';

interface FilterBarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  summary: TaskSummary | null;
}

export function FilterBar({ filters, onChange, summary }: FilterBarProps) {
  const handleChange = (key: keyof FilterState, value: string | boolean | undefined) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <div className="filter-bar">
      <h3>Filters</h3>

      <div className="filter-group">
        <label htmlFor="status">Status</label>
        <select
          id="status"
          value={filters.status || ''}
          onChange={(e) => handleChange('status', e.target.value as TaskStatus || undefined)}
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="priority">Priority</label>
        <select
          id="priority"
          value={filters.priority || ''}
          onChange={(e) => handleChange('priority', e.target.value as TaskPriority || undefined)}
        >
          <option value="">All</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      <div className="filter-group">
        <label>
          <input
            type="checkbox"
            checked={filters.is_archived === true}
            onChange={(e) => handleChange('is_archived', e.target.checked ? true : undefined)}
          />
          Show Archived
        </label>
      </div>

      <div className="filter-group">
        <label htmlFor="search">Search</label>
        <input
          id="search"
          type="text"
          placeholder="Search tasks..."
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value || undefined)}
        />
      </div>

      {summary && (
        <div className="summary">
          <h4>Summary</h4>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="summary-value">{summary.total}</span>
              <span className="summary-label">Total</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{summary.pending}</span>
              <span className="summary-label">Pending</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{summary.in_progress}</span>
              <span className="summary-label">In Progress</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{summary.completed}</span>
              <span className="summary-label">Completed</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{summary.overdue}</span>
              <span className="summary-label">Overdue</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{summary.archived}</span>
              <span className="summary-label">Archived</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}