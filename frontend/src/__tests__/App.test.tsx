import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App Component', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            version: '1.0.0',
            author: 'Alan Vo <alanvo@gmail.com>',
            offline_engine_available: true
          })
        });
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            username: 'alan_dev',
            roles: ['admin']
          })
        });
      }
      if (url.includes('/index')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            root_path: '.',
            total_files: 2,
            symbols_count: 5,
            files: []
          })
        });
      }
      if (url.includes('/benchmark')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            total_tasks: 5,
            average_score: 1.0,
            valid_syntax_rate: 1.0,
            ast_parse_rate: 1.0,
            dependency_recall_rate: 1.0,
            results: []
          })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));
  });

  it('renders application header and author attribution', async () => {
    render(<App />);
    expect(screen.getByText('AI Pair Programmer')).toBeInTheDocument();
    const authorElements = screen.getAllByText(/Alan Vo/i);
    expect(authorElements.length).toBeGreaterThan(0);
  });

  it('renders navigation tabs for workspace, context, and benchmarks', async () => {
    render(<App />);
    expect(screen.getByText('Refactoring Workspace')).toBeInTheDocument();
    expect(screen.getByText('Codebase Context Tree')).toBeInTheDocument();
    expect(screen.getByText('AI/ML Evaluation Suite')).toBeInTheDocument();
  });
});
