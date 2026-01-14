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
import GalleryBrowser from './GalleryBrowser';

// Mock fetch
global.fetch = jest.fn();

describe('GalleryBrowser Component', () => {
  const mockGalleries = [
    {
      id: 'gallery-1',
      title: 'Moments with friends',
      description: 'Happy times with close friends',
      creation_method: 'thematic',
      memories: [
        { id: 'mem-1', title: 'Party', image: '/image1.jpg', date: '2023-01-01' },
        { id: 'mem-2', title: 'Dinner', image: '/image2.jpg', date: '2023-01-02' }
      ]
    },
    {
      id: 'gallery-2',
      title: 'Travel adventures',
      description: 'Exploring new places',
      creation_method: 'prompt',
      memories: [
        { id: 'mem-3', title: 'Mountain hike', image: '/image3.jpg', date: '2023-02-01' }
      ]
    }
  ];

  const mockNewGallery = {
    id: 'gallery-3',
    title: 'Creative periods',
    description: 'Times of artistic expression',
    creation_method: 'thematic',
    memories: []
  };

  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders gallery browser with creation controls', () => {
    render(<GalleryBrowser />);
    
    expect(screen.getByText(/Create New Gallery/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Describe the gallery/i)).toBeInTheDocument();
    expect(screen.getByText(/Quick Themes/i)).toBeInTheDocument();
  });

  test('loads existing galleries on mount', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: mockGalleries })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      });

    render(<GalleryBrowser />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/galleries')
      );
    });
  });

  test('displays existing galleries', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: mockGalleries })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      });

    render(<GalleryBrowser />);

    await waitFor(() => {
      expect(screen.getByText('Moments with friends')).toBeInTheDocument();
      expect(screen.getByText('Travel adventures')).toBeInTheDocument();
    });
  });

  test('creates custom gallery from prompt', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => mockNewGallery
      });

    render(<GalleryBrowser />);

    const input = screen.getByPlaceholderText(/Describe the gallery/i);
    const createButton = screen.getByRole('button', { name: '' }); // Button with pi-plus icon

    fireEvent.change(input, { target: { value: 'My creative moments' } });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/galleries/create'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            prompt: 'My creative moments',
            creation_method: 'prompt'
          })
        })
      );
    });
  });

  test('creates thematic gallery from quick theme', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => mockNewGallery
      });

    render(<GalleryBrowser />);

    const themeButton = screen.getByText('Creative periods');
    fireEvent.click(themeButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/galleries/create'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            theme: 'Creative periods',
            creation_method: 'thematic'
          })
        })
      );
    });
  });

  test('opens gallery dialog when gallery is clicked', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: mockGalleries })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      });

    render(<GalleryBrowser />);

    await waitFor(() => {
      expect(screen.getByText('Moments with friends')).toBeInTheDocument();
    });

    const galleryCard = screen.getByText('Moments with friends').closest('.p-card');
    fireEvent.click(galleryCard);

    await waitFor(() => {
      expect(screen.getByText('Create Story from Gallery')).toBeInTheDocument();
    });
  });

  test('converts gallery to story', async () => {
    const mockStory = { id: 'story-1', title: 'Gallery Story' };
    const mockOnCreateStory = jest.fn();

    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: mockGalleries })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => mockStory
      });

    render(<GalleryBrowser onCreateStory={mockOnCreateStory} />);

    await waitFor(() => {
      expect(screen.getByText('Moments with friends')).toBeInTheDocument();
    });

    const galleryCard = screen.getByText('Moments with friends').closest('.p-card');
    fireEvent.click(galleryCard);

    await waitFor(() => {
      const createStoryButton = screen.getByText('Create Story from Gallery');
      fireEvent.click(createStoryButton);
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/galleries/gallery-1/story'),
        expect.objectContaining({
          method: 'POST'
        })
      );
      expect(mockOnCreateStory).toHaveBeenCalledWith(mockStory);
    });
  });

  test('calls onGallerySelect callback when gallery is selected', async () => {
    const mockOnGallerySelect = jest.fn();

    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: mockGalleries })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      });

    render(<GalleryBrowser onGallerySelect={mockOnGallerySelect} />);

    await waitFor(() => {
      expect(screen.getByText('Moments with friends')).toBeInTheDocument();
    });

    const galleryCard = screen.getByText('Moments with friends').closest('.p-card');
    fireEvent.click(galleryCard);

    expect(mockOnGallerySelect).toHaveBeenCalledWith(mockGalleries[0]);
  });

  test('disables create button when input is empty', () => {
    render(<GalleryBrowser />);

    const createButton = screen.getByRole('button', { name: '' }); // Button with pi-plus icon
    expect(createButton).toBeDisabled();
  });

  test('shows empty state when no galleries exist', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      });

    render(<GalleryBrowser />);

    await waitFor(() => {
      expect(screen.getByText(/No galleries yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Create your first gallery/i)).toBeInTheDocument();
    });
  });

  test('shows progress bar during gallery creation', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockResolvedValueOnce({
        json: async () => ({ galleries: [] })
      })
      .mockImplementationOnce(() => new Promise(resolve => {
        setTimeout(() => resolve({ json: async () => mockNewGallery }), 100);
      }));

    render(<GalleryBrowser />);

    const input = screen.getByPlaceholderText(/Describe the gallery/i);
    const createButton = screen.getByRole('button', { name: '' }); // Button with pi-plus icon

    fireEvent.change(input, { target: { value: 'Test gallery' } });
    fireEvent.click(createButton);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });
});