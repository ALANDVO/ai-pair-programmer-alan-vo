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

  it('includes use_llm checkbox and passes it in onSubmit', () => {
    const handleSubmit = vi.fn();
    render(<TaskForm onSubmit={handleSubmit} isLoading={false} />);

    const llmCheckbox = screen.getByLabelText(/Use LLM Advisory Reasoning/i);
    expect(llmCheckbox).toBeInTheDocument();
    expect(llmCheckbox).not.toBeChecked();

    fireEvent.click(llmCheckbox);
    expect(llmCheckbox).toBeChecked();

    const textarea = screen.getByLabelText(/Task Description/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'add retry wrapper' } });

    const submitBtn = screen.getByText(/Synthesize Refactor Plan/i);
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
      task: 'add retry wrapper',
      dry_run: true,
      use_llm: true
    }));
  });
});
