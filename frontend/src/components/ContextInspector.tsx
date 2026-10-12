import React from 'react';
import { CodebaseIndex } from '../types';

interface ContextInspectorProps {
  index: CodebaseIndex | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const ContextInspector: React.FC<ContextInspectorProps> = ({ index, onRefresh, isLoading }) => {
  return (
    <div className="card">
      <div className="card-title">
        <span>Codebase AST Context</span>
        <button className="btn btn-secondary" onClick={onRefresh} disabled={isLoading}>
          {isLoading ? 'Scanning...' : 'Rescan Codebase'}
        </button>
      </div>

      {!index ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No codebase index loaded.</p>
      ) : (
        <>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
            <span><strong>Root:</strong> {index.root_path}</span>
            <span><strong>Files:</strong> {index.total_files}</span>
            <span><strong>Symbols:</strong> {index.symbols_count}</span>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Language</th>
                <th>Lines</th>
                <th>Symbols</th>
                <th>Callers</th>
              </tr>
            </thead>
            <tbody>
              {index.files.map((file, idx) => (
                <tr key={idx}>
                  <td><code>{file.relative_path}</code></td>
                  <td><span className="badge badge-blue">{file.language}</span></td>
                  <td>{file.lines_count}</td>
                  <td>{file.symbols.length}</td>
                  <td>{file.callers.length ? file.callers.join(', ') : 'None'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};
