import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from '../components/Dashboard';

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('/index')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            root_path: '.',
            total_files: 3,
            scanned_extensions: ['.py', '.ts'],
            files: [
              {
                path: '/app/main.py',
                relative_path: 'main.py',
                language: 'python',
                size_bytes: 1200,
                lines_count: 50,
                imports: ['fastapi'],
                symbols: [],
                callers: []
              }
            ],
            dependencies: [],
            symbols_count: 10
          })
        });
      }
      if (url.includes('/benchmark')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            total_tasks: 5,
            passed_tasks: 5,
            valid_syntax_rate: 1.0,
            ast_parse_rate: 1.0,
            dependency_recall_rate: 1.0,
            average_score: 1.0,
            engine: 'deterministic-ast-verifier',
            results: []
          })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));
  });

  it('renders workspace mode with task form and diff inspector', async () => {
    render(<Dashboard activeTab="workspace" />);
    expect(screen.getByText(/Compose Refactor Task/i)).toBeInTheDocument();
    expect(screen.getByText(/Diff & Impact Inspector/i)).toBeInTheDocument();
  });

  it('renders benchmark mode with metrics panel', async () => {
    render(<Dashboard activeTab="benchmark" />);
    expect(screen.getByText(/AI \/ Machine Learning Evaluation Baseline/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Benchmark/i })).toBeInTheDocument();
    });
  });
});
