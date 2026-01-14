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
import EnhancedMapComponent from './EnhancedMapComponent';

// Mock Google Maps
jest.mock('@react-google-maps/api', () => ({
  useLoadScript: () => ({
    isLoaded: true,
    loadError: null
  }),
  GoogleMap: ({ children, onLoad }) => {
    // Simulate map load
    if (onLoad) {
      onLoad({});
    }
    return <div data-testid="google-map">{children}</div>;
  },
  Marker: ({ onClick, position }) => (
    <div 
      data-testid="map-marker" 
      onClick={onClick}
      data-lat={position.lat}
      data-lng={position.lng}
    />
  ),
  InfoWindow: ({ children, onCloseClick }) => (
    <div data-testid="info-window">
      <button onClick={onCloseClick}>Close</button>
      {children}
    </div>
  )
}));

// Mock fetch
global.fetch = jest.fn();

describe('EnhancedMapComponent', () => {
  const mockGeoData = [
    {
      id: 'place-1',
      lat: 47.6062,
      long: -122.3321,
      title: 'Seattle',
      start: '2023-01-01',
      end: '2023-01-02'
    },
    {
      id: 'place-2',
      lat: 47.6205,
      long: -122.3493,
      title: 'Capitol Hill',
      start: '2023-01-03'
    }
  ];

  const mockNarrativeData = {
    'place-1': {
      emotional_context: { joy: 0.8, nostalgia: 0.6 },
      narrative_significance: 0.9,
      life_phase: 'Early Career',
      thematic_tags: ['work', 'friends']
    }
  };

  beforeEach(() => {
    fetch.mockClear();
    // Mock environment variable
    process.env.REACT_APP_GOOGLE_MAP_API = 'test-api-key';
  });

  test('renders map with basic functionality', () => {
    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    expect(screen.getByTestId('google-map')).toBeInTheDocument();
  });

  test('renders markers for each location', () => {
    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    const markers = screen.getAllByTestId('map-marker');
    expect(markers).toHaveLength(2);
    
    expect(markers[0]).toHaveAttribute('data-lat', '47.6062');
    expect(markers[0]).toHaveAttribute('data-lng', '-122.3321');
  });

  test('shows narrative layer controls when enabled', () => {
    render(
      <EnhancedMapComponent 
        geo={mockGeoData} 
        height="400px" 
        showNarrativeLayers={true} 
      />
    );
    
    expect(screen.getByText(/Emotional Layer/i)).toBeInTheDocument();
    expect(screen.getByText(/Significance Layer/i)).toBeInTheDocument();
    expect(screen.getByText(/Journey Paths/i)).toBeInTheDocument();
  });

  test('hides narrative controls when disabled', () => {
    render(
      <EnhancedMapComponent 
        geo={mockGeoData} 
        height="400px" 
        showNarrativeLayers={false} 
      />
    );
    
    expect(screen.queryByText(/Emotional Layer/i)).not.toBeInTheDocument();
  });

  test('fetches narrative data when narrative layers are enabled', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockNarrativeData
    });

    render(
      <EnhancedMapComponent 
        geo={mockGeoData} 
        height="400px" 
        showNarrativeLayers={true} 
      />
    );

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/places/narrative'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  test('opens info window when marker is clicked', () => {
    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    const marker = screen.getAllByTestId('map-marker')[0];
    fireEvent.click(marker);
    
    expect(screen.getByTestId('info-window')).toBeInTheDocument();
  });

  test('closes info window when close button is clicked', () => {
    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    const marker = screen.getAllByTestId('map-marker')[0];
    fireEvent.click(marker);
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('info-window')).not.toBeInTheDocument();
  });

  test('generates place story when button is clicked', async () => {
    const mockStory = { summary: 'A story about Seattle' };
    fetch.mockResolvedValueOnce({
      json: async () => mockStory
    });

    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    const marker = screen.getAllByTestId('map-marker')[0];
    fireEvent.click(marker);
    
    const generateStoryButton = screen.getByText(/Generate Story/i);
    fireEvent.click(generateStoryButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/places/place-1/story'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  test('calls callback functions when view memories is clicked', () => {
    const mockSetSelectedDateRange = jest.fn();
    const mockSetSelectedIDs = jest.fn();

    render(
      <EnhancedMapComponent 
        geo={mockGeoData} 
        height="400px"
        setSelectedDateRange={mockSetSelectedDateRange}
        setSelectedIDs={mockSetSelectedIDs}
      />
    );
    
    const marker = screen.getAllByTestId('map-marker')[0];
    fireEvent.click(marker);
    
    const viewMemoriesButton = screen.getByText(/View Memories/i);
    fireEvent.click(viewMemoriesButton);

    expect(mockSetSelectedDateRange).toHaveBeenCalled();
    expect(mockSetSelectedIDs).toHaveBeenCalledWith(['place-1']);
  });

  test('handles loading state correctly', () => {
    // Mock loading state
    jest.doMock('@react-google-maps/api', () => ({
      useLoadScript: () => ({
        isLoaded: false,
        loadError: null
      })
    }));

    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    expect(screen.getByText(/Loading map/i)).toBeInTheDocument();
  });

  test('handles error state correctly', () => {
    // Mock error state
    jest.doMock('@react-google-maps/api', () => ({
      useLoadScript: () => ({
        isLoaded: false,
        loadError: new Error('Failed to load')
      })
    }));

    render(<EnhancedMapComponent geo={mockGeoData} height="400px" />);
    
    expect(screen.getByText(/Error loading map/i)).toBeInTheDocument();
  });
});