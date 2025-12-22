/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StoryInterface from './StoryInterface';

// Mock fetch
global.fetch = jest.fn();

describe('StoryInterface Component', () => {
  const mockMemories = [
    { id: '1', title: 'Memory 1', date: '2023-01-01' },
    { id: '2', title: 'Memory 2', date: '2023-01-02' }
  ];

  const mockStory = {
    id: 'story-1',
    title: 'Test Story',
    narrative_mode: 'chronological',
    chapters: [
      {
        id: 'chapter-1',
        title: 'Chapter 1',
        narrative_text: 'This is chapter 1',
        media_elements: [],
        duration_seconds: 5
      },
      {
        id: 'chapter-2',
        title: 'Chapter 2',
        narrative_text: 'This is chapter 2',
        media_elements: [],
        duration_seconds: 5
      }
    ],
    created_at: '2023-01-01T00:00:00Z'
  };

  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders story interface with controls', () => {
    render(<StoryInterface memories={mockMemories} />);
    
    expect(screen.getByText(/Select narrative mode/i)).toBeInTheDocument();
    expect(screen.getByText(/Generate Story/i)).toBeInTheDocument();
  });

  test('narrative mode dropdown shows all options', () => {
    render(<StoryInterface memories={mockMemories} />);
    
    const dropdown = screen.getByRole('combobox');
    expect(dropdown).toBeInTheDocument();
  });

  test('generate story button is disabled without memories', () => {
    render(<StoryInterface memories={[]} />);
    
    const generateButton = screen.getByText(/Generate Story/i);
    expect(generateButton).toBeDisabled();
  });

  test('generates story when button clicked', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockStory
    });

    render(<StoryInterface memories={mockMemories} />);
    
    const generateButton = screen.getByText(/Generate Story/i);
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/stories/generate'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  test('displays story after generation', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockStory
    });

    render(<StoryInterface memories={mockMemories} />);
    
    const generateButton = screen.getByText(/Generate Story/i);
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText('Test Story')).toBeInTheDocument();
      expect(screen.getByText(/Chapter 1 of 2/i)).toBeInTheDocument();
    });
  });

  test('chapter navigation works correctly', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockStory
    });

    render(<StoryInterface memories={mockMemories} />);
    
    const generateButton = screen.getByText(/Generate Story/i);
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(screen.getByText('Chapter 1')).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /step-forward/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/Chapter 2 of 2/i)).toBeInTheDocument();
    });
  });

  test('playback controls are functional', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockStory
    });

    render(<StoryInterface memories={mockMemories} />);
    
    const generateButton = screen.getByText(/Generate Story/i);
    fireEvent.click(generateButton);

    await waitFor(() => {
      const playButton = screen.getByRole('button', { name: /play/i });
      expect(playButton).toBeInTheDocument();
    });
  });

  test('calls onStoryGenerated callback when story is created', async () => {
    const mockCallback = jest.fn();
    fetch.mockResolvedValueOnce({
      json: async () => mockStory
    });

    render(<StoryInterface memories={mockMemories} onStoryGenerated={mockCallback} />);
    
    const generateButton = screen.getByText(/Generate Story/i);
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith(mockStory);
    });
  });
});