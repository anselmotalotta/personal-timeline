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
import PeopleDashboard from './PeopleDashboard';

// Mock Chart component
jest.mock('primereact/chart', () => ({
  Chart: ({ data, type }) => (
    <div data-testid="chart" data-type={type}>
      Chart: {JSON.stringify(data)}
    </div>
  )
}));

// Mock fetch
global.fetch = jest.fn();

describe('PeopleDashboard Component', () => {
  const mockPeople = [
    {
      id: 'person-1',
      name: 'John Doe',
      representative_photos: ['/photo1.jpg'],
      interaction_count: 25,
      last_appearance: '2023-12-01T00:00:00Z',
      shared_contexts: ['work', 'coffee', 'meetings']
    },
    {
      id: 'person-2',
      name: 'Jane Smith',
      representative_photos: [],
      interaction_count: 15,
      last_appearance: '2023-11-15T00:00:00Z',
      shared_contexts: ['family', 'holidays']
    }
  ];

  const mockPersonProfile = {
    id: 'person-1',
    name: 'John Doe',
    representative_photos: ['/photo1.jpg'],
    first_appearance: '2022-01-01T00:00:00Z',
    last_appearance: '2023-12-01T00:00:00Z'
  };

  const mockInteractionData = {
    timeline: [
      { period: '2023-01', count: 5 },
      { period: '2023-02', count: 8 },
      { period: '2023-03', count: 12 }
    ]
  };

  const mockEvolution = {
    phases: [
      {
        phase_name: 'Colleague',
        start_date: '2022-01-01T00:00:00Z',
        emotional_tone: 'neutral',
        description: 'Started working together'
      },
      {
        phase_name: 'Friend',
        start_date: '2022-06-01T00:00:00Z',
        emotional_tone: 'positive',
        description: 'Became close friends'
      }
    ]
  };

  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders people dashboard with header', () => {
    render(<PeopleDashboard />);
    
    expect(screen.getByText(/People in Your Life/i)).toBeInTheDocument();
    expect(screen.getByText(/Explore the relationships/i)).toBeInTheDocument();
  });

  test('loads people on mount', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => ({ people: mockPeople })
    });

    render(<PeopleDashboard />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/people')
      );
    });
  });

  test('displays people cards', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => ({ people: mockPeople })
    });

    render(<PeopleDashboard />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('25 interactions')).toBeInTheDocument();
      expect(screen.getByText('15 interactions')).toBeInTheDocument();
    });
  });

  test('shows avatar for person without photo', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => ({ people: mockPeople })
    });

    render(<PeopleDashboard />);

    await waitFor(() => {
      // Jane Smith has no photo, should show avatar with first letter
      expect(screen.getByText('J')).toBeInTheDocument();
    });
  });

  test('opens person dialog when person card is clicked', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      });

    render(<PeopleDashboard />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const personCard = screen.getByText('John Doe').closest('.p-card');
    fireEvent.click(personCard);

    await waitFor(() => {
      expect(screen.getByText(/Generate 'Best of Us'/i)).toBeInTheDocument();
    });
  });

  test('loads person details when dialog opens', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      });

    render(<PeopleDashboard />);

    await waitFor(() => {
      const personCard = screen.getByText('John Doe');
      fireEvent.click(personCard.closest('.person-card'));
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/people/person-1/profile')
      );
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/people/person-1/interactions')
      );
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/people/person-1/evolution')
      );
    });
  });

  test('displays interaction chart in person dialog', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      });

    render(<PeopleDashboard />);

    await waitFor(() => {
      const personCard = screen.getByText('John Doe');
      fireEvent.click(personCard.closest('.person-card'));
    });

    await waitFor(() => {
      expect(screen.getByText(/Interaction Timeline/i)).toBeInTheDocument();
      expect(screen.getByTestId('chart')).toBeInTheDocument();
    });
  });

  test('displays relationship evolution timeline', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      });

    render(<PeopleDashboard />);

    await waitFor(() => {
      const personCard = screen.getByText('John Doe');
      fireEvent.click(personCard.closest('.person-card'));
    });

    await waitFor(() => {
      expect(screen.getByText(/Relationship Evolution/i)).toBeInTheDocument();
      expect(screen.getByText('Colleague')).toBeInTheDocument();
      expect(screen.getByText('Friend')).toBeInTheDocument();
    });
  });

  test('generates best of us compilation', async () => {
    const mockCompilation = {
      summary: 'Great memories together',
      photos: [
        { url: '/comp1.jpg', caption: 'Fun times' },
        { url: '/comp2.jpg', caption: 'Adventure' }
      ]
    };

    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      })
      .mockResolvedValueOnce({
        json: async () => mockCompilation
      });

    render(<PeopleDashboard />);

    await waitFor(() => {
      const personCard = screen.getByText('John Doe');
      fireEvent.click(personCard.closest('.person-card'));
    });

    await waitFor(() => {
      const bestOfUsButton = screen.getByText(/Generate 'Best of Us'/i);
      fireEvent.click(bestOfUsButton);
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/people/person-1/best-of-us'),
        expect.objectContaining({
          method: 'POST'
        })
      );
      expect(screen.getByText('Great memories together')).toBeInTheDocument();
    });
  });

  test('calls onPersonSelect callback when person is selected', async () => {
    const mockOnPersonSelect = jest.fn();

    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      });

    render(<PeopleDashboard onPersonSelect={mockOnPersonSelect} />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const personCard = screen.getByText('John Doe').closest('.p-card');
    fireEvent.click(personCard);

    expect(mockOnPersonSelect).toHaveBeenCalledWith(mockPeople[0]);
  });

  test('calls onCreateStory callback when create story is clicked', async () => {
    const mockOnCreateStory = jest.fn();

    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      });

    render(<PeopleDashboard onCreateStory={mockOnCreateStory} />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const personCard = screen.getByText('John Doe').closest('.p-card');
    fireEvent.click(personCard);

    await waitFor(() => {
      const createStoryButton = screen.getByText(/Create Story/i);
      fireEvent.click(createStoryButton);
    });

    expect(mockOnCreateStory).toHaveBeenCalledWith({ person: mockPersonProfile });
  });

  test('shows empty state when no people exist', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => ({ people: [] })
    });

    render(<PeopleDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/No people profiles yet/i)).toBeInTheDocument();
      expect(screen.getByText(/automatically generated/i)).toBeInTheDocument();
    });
  });

  test('updates person controls', async () => {
    fetch
      .mockResolvedValueOnce({
        json: async () => ({ people: mockPeople })
      })
      .mockResolvedValueOnce({
        json: async () => mockPersonProfile
      })
      .mockResolvedValueOnce({
        json: async () => mockInteractionData
      })
      .mockResolvedValueOnce({
        json: async () => mockEvolution
      })
      .mockResolvedValueOnce({
        json: async () => ({ visibility: 'hidden' })
      });

    render(<PeopleDashboard />);

    await waitFor(() => {
      const personCard = screen.getByText('John Doe');
      fireEvent.click(personCard.closest('.person-card'));
    });

    await waitFor(() => {
      const saveButton = screen.getByText(/Save Changes/i);
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/people/person-1/controls'),
        expect.objectContaining({
          method: 'PUT'
        })
      );
    });
  });
});