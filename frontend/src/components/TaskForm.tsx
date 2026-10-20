import React, { useState } from 'react';
import { RefactorRequest } from '../types';

interface TaskFormProps {
  onSubmit: (req: RefactorRequest) => void;
  isLoading: boolean;
}

const PRESET_TASKS = [
  "rename calculate_tax to compute_tax",
  "add retry wrapper with exponential backoff",
  "add audit logging for state mutation",
  "rename DataProcessor to RecordProcessor"
];

export const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, isLoading }) => {
  const [task, setTask] = useState('');
  const [path, setPath] = useState('.');
  const [maxFiles, setMaxFiles] = useState(15);
  const [dryRun, setDryRun] = useState(true);
  const [useLLM, setUseLLM] = useState(false);
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) return;
    onSubmit({ task, path, max_files: maxFiles, dry_run: dryRun, use_llm: useLLM });
  };

  return (
    <div className="card">
      <h2 className="card-title">Compose Refactor Task</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="task-input">Task Description</label>
          <textarea
            id="task-input"
            className="form-textarea"
            placeholder="e.g. rename calculate_tax to compute_tax, or add retry wrapper"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            required
          />
          <div className="presets-container">
            {PRESET_TASKS.map((preset, i) => (
              <button
                key={i}
                type="button"
                className="preset-chip"
                onClick={() => setTask(preset)}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="path-input">Scope Path</label>
          <input
            id="path-input"
            type="text"
            className="form-input"
            value={path}
            onChange={(e) => setPath(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="max-files-select">Max Files to Inspect</label>
          <select
            id="max-files-select"
            className="form-select"
            value={maxFiles}
            onChange={(e) => setMaxFiles(Number(e.target.value))}
          >
            <option value={5}>5 files</option>
            <option value={15}>15 files</option>
            <option value={30}>30 files</option>
          </select>
        </div>

        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input
            id="dry-run-check"
            type="checkbox"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
          />
          <label htmlFor="dry-run-check" className="form-label" style={{ margin: 0, cursor: 'pointer' }}>
            Dry Run Mode (Preview diffs safely without disk modification)
          </label>
        </div>
        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input
            id="use-llm-check"
            type="checkbox"
            checked={useLLM}
            onChange={(e) => setUseLLM(e.target.checked)}
          />
          <label htmlFor="use-llm-check" className="form-label" style={{ margin: 0, cursor: 'pointer' }}>
            Use LLM Advisory Reasoning (requires configured provider)
          </label>
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-full"
          disabled={isLoading || !task.trim()}
        >
          {isLoading ? 'Analyzing AST Context...' : 'Synthesize Refactor Plan'}
        </button>
      </form>
    </div>
  );
};
