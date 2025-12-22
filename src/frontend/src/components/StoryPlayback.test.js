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
import StoryPlayback from './StoryPlayback';

// Mock fetch
global.fetch = jest.fn();

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-audio-url');

describe('StoryPlayback Component', () => {
  const mockStory = {
    id: 'story-1',
    title: 'Test Story',
    chapters: [
      {
        id: 'chapter-1',
        title: 'Chapter 1',
        narrative_text: 'This is the first chapter of our story.',
        duration_seconds: 5,
        media_elements: [
          {
            type: 'image',
            url: '/image1.jpg',
            caption: 'A beautiful moment'
          }
        ]
      },
      {
        id: 'chapter-2',
        title: 'Chapter 2',
        narrative_text: 'This is the second chapter.',
        duration_seconds: 4,
        media_elements: [
          {
            type: 'video',
            url: '/video1.mp4',
            caption: 'An exciting adventure'
          }
        ]
      }
    ]
  };

  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test('renders empty state when no story provided', () => {
    render(<StoryPlayback />);
    
    expect(screen.getByText(/No story selected/i)).toBeInTheDocument();
    expect(screen.getByText(/Select a story to begin playback/i)).toBeInTheDocument();
  });

  test('renders story playback controls with story', () => {
    render(<StoryPlayback story={mockStory} />);
    
    expect(screen.getByText('Test Story')).toBeInTheDocument();
    expect(screen.getByText(/Chapter 1 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument();
  });

  test('displays first chapter content by default', () => {
    render(<StoryPlayback story={mockStory} />);
    
    expect(screen.getByText('Chapter 1')).toBeInTheDocument();
    expect(screen.getByText('This is the first chapter of our story.')).toBeInTheDocument();
  });

  test('shows chapter media elements', () => {
    render(<StoryPlayback story={mockStory} />);
    
    expect(screen.getByAltText('A beautiful moment')).toBeInTheDocument();
  });

  test('navigates to next chapter', () => {
    const mockOnChapterChange = jest.fn();
    render(<StoryPlayback story={mockStory} onChapterChange={mockOnChapterChange} />);
    
    const nextButton = screen.getByRole('button', { name: /step-forward/i });
    fireEvent.click(nextButton);
    
    expect(screen.getByText(/Chapter 2 of 2/i)).toBeInTheDocument();
    expect(screen.getByText('Chapter 2')).toBeInTheDocument();
    expect(mockOnChapterChange).toHaveBeenCalledWith(1);
  });

  test('navigates to previous chapter', () => {
    const mockOnChapterChange = jest.fn();
    render(<StoryPlayback story={mockStory} onChapterChange={mockOnChapterChange} />);
    
    // First go to chapter 2
    const nextButton = screen.getByRole('button', { name: /step-forward/i });
    fireEvent.click(nextButton);
    
    // Then go back to chapter 1
    const prevButton = screen.getByRole('button', { name: /step-backward/i });
    fireEvent.click(prevButton);
    
    expect(screen.getByText(/Chapter 1 of 2/i)).toBeInTheDocument();
    expect(mockOnChapterChange).toHaveBeenCalledWith(0);
  });

  test('disables navigation buttons at boundaries', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const prevButton = screen.getByRole('button', { name: /step-backward/i });
    const nextButton = screen.getByRole('button', { name: /step-forward/i });
    
    // At first chapter, previous should be disabled
    expect(prevButton).toBeDisabled();
    expect(nextButton).not.toBeDisabled();
    
    // Go to last chapter
    fireEvent.click(nextButton);
    
    // At last chapter, next should be disabled
    expect(prevButton).not.toBeDisabled();
    expect(nextButton).toBeDisabled();
  });

  test('plays story and updates progress', async () => {
    render(<StoryPlayback story={mockStory} />);
    
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);
    
    // Should show pause button when playing
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
    
    // Progress should start updating
    jest.advanceTimersByTime(1000);
    
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  test('pauses story playback', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);
    
    const pauseButton = screen.getByRole('button', { name: /pause/i });
    fireEvent.click(pauseButton);
    
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument();
  });

  test('stops story playback', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);
    
    const stopButton = screen.getByRole('button', { name: /stop/i });
    fireEvent.click(stopButton);
    
    expect(screen.getByText(/Chapter 1 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument();
  });

  test('seeks to specific chapter using thumbnails', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const chapterThumbnails = screen.getAllByText(/^\d+$/);
    fireEvent.click(chapterThumbnails[1]); // Click chapter 2 thumbnail
    
    expect(screen.getByText(/Chapter 2 of 2/i)).toBeInTheDocument();
  });

  test('toggles audio narration', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const audioToggle = screen.getByRole('button', { name: /Audio/i });
    fireEvent.click(audioToggle);
    
    // Should show "Audio On" when enabled
    expect(screen.getByText(/Audio On/i)).toBeInTheDocument();
  });

  test('toggles captions', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const captionsToggle = screen.getByRole('button', { name: /Captions/i });
    fireEvent.click(captionsToggle);
    
    // Captions should be hidden when toggled off
    expect(screen.queryByText('This is the first chapter of our story.')).not.toBeInTheDocument();
  });

  test('changes playback speed', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const speedDropdown = screen.getByDisplayValue('1x');
    expect(speedDropdown).toBeInTheDocument();
  });

  test('generates audio narration when audio is enabled', async () => {
    const mockAudioBlob = new Blob(['audio data'], { type: 'audio/mp3' });
    fetch.mockResolvedValueOnce({
      blob: async () => mockAudioBlob
    });

    render(<StoryPlayback story={mockStory} />);
    
    // Enable audio
    const audioToggle = screen.getByRole('button', { name: /Audio/i });
    fireEvent.click(audioToggle);
    
    // Start playback
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/stories/narrate'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  test('calls onPlaybackComplete when story finishes', () => {
    const mockOnPlaybackComplete = jest.fn();
    render(<StoryPlayback story={mockStory} onPlaybackComplete={mockOnPlaybackComplete} />);
    
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);
    
    // Fast forward through all chapters
    jest.advanceTimersByTime(10000); // More than total duration
    
    expect(mockOnPlaybackComplete).toHaveBeenCalled();
  });

  test('auto-advances through chapters when enabled', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);
    
    // Should start at chapter 1
    expect(screen.getByText(/Chapter 1 of 2/i)).toBeInTheDocument();
    
    // Fast forward past first chapter duration
    jest.advanceTimersByTime(6000);
    
    // Should auto-advance to chapter 2
    expect(screen.getByText(/Chapter 2 of 2/i)).toBeInTheDocument();
  });

  test('disables auto-advance when toggle is off', () => {
    render(<StoryPlayback story={mockStory} />);
    
    const autoAdvanceToggle = screen.getByRole('button', { name: /Auto-advance/i });
    fireEvent.click(autoAdvanceToggle); // Turn off auto-advance
    
    const playButton = screen.getByRole('button', { name: /play/i });
    fireEvent.click(playButton);
    
    // Fast forward past first chapter duration
    jest.advanceTimersByTime(6000);
    
    // Should still be at chapter 1
    expect(screen.getByText(/Chapter 1 of 2/i)).toBeInTheDocument();
  });
});