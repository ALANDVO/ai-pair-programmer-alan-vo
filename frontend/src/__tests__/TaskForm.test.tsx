import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskForm } from '../components/TaskForm';

describe('TaskForm Component', () => {
  it('renders task input, preset chips, and submit button', () => {
    const handleSubmit = vi.fn();
    render(<TaskForm onSubmit={handleSubmit} isLoading={false} />);

    expect(screen.getByLabelText(/Task Description/i)).toBeInTheDocument();
    expect(screen.getByText(/Compose Refactor Task/i)).toBeInTheDocument();
    expect(screen.getByText(/Synthesize Refactor Plan/i)).toBeInTheDocument();
  });

  it('populates task input when preset chip is clicked and calls onSubmit', () => {
    const handleSubmit = vi.fn();
    render(<TaskForm onSubmit={handleSubmit} isLoading={false} />);

    const chip = screen.getByText('rename calculate_tax to compute_tax');
    fireEvent.click(chip);

    const textarea = screen.getByLabelText(/Task Description/i) as HTMLTextAreaElement;
    expect(textarea.value).toBe('rename calculate_tax to compute_tax');

    const submitBtn = screen.getByText(/Synthesize Refactor Plan/i);
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
      task: 'rename calculate_tax to compute_tax',
      dry_run: true
    }));
  });
});
