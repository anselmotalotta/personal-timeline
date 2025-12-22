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

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { GoogleMap, useLoadScript, Marker, InfoWindow } from '@react-google-maps/api';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Chip } from 'primereact/chip';
import { ToggleButton } from 'primereact/togglebutton';
import { config } from '../Constants';

const libraries = ["places"];

const options = {
  disableDefaultUI: true,
  zoomControl: true,
  styles: [
    {
      featureType: "poi",
      elementType: "labels",
      stylers: [{ visibility: "off" }]
    }
  ]
};

const EnhancedMapComponent = ({ 
  geo, 
  height, 
  width, 
  setSelectedDateRange, 
  setSelectedIDs,
  showNarrativeLayers = true 
}) => {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env["REACT_APP_GOOGLE_MAP_API"],
    libraries
  });

  const [selectedPlace, setSelectedPlace] = useState(null);
  const [narrativeData, setNarrativeData] = useState({});
  const [showEmotionalLayer, setShowEmotionalLayer] = useState(false);
  const [showTemporalLayer, setShowTemporalLayer] = useState(false);
  const [showJourneyPaths, setShowJourneyPaths] = useState(false);
  const [placeStories, setPlaceStories] = useState({});

  const mapRef = useRef();

  const onMapLoad = useCallback((map) => {
    mapRef.current = map;
  }, []);

  // Fetch narrative data for places
  useEffect(() => {
    if (geo && geo.length > 0 && showNarrativeLayers) {
      fetchNarrativeData();
    }
  }, [geo, showNarrativeLayers]);

  const fetchNarrativeData = async () => {
    try {
      const response = await fetch(`${config.API_URL}/api/places/narrative`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          places: geo.map(place => ({
            lat: place.lat,
            lng: place.long,
            id: place.id
          }))
        })
      });
      
      const data = await response.json();
      setNarrativeData(data);
    } catch (error) {
      console.error('Error fetching narrative data:', error);
    }
  };

  const generatePlaceStory = async (place) => {
    try {
      const response = await fetch(`${config.API_URL}/api/places/${place.id}/story`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const story = await response.json();
      setPlaceStories(prev => ({
        ...prev,
        [place.id]: story
      }));
    } catch (error) {
      console.error('Error generating place story:', error);
    }
  };

  const getMarkerColor = (place) => {
    if (!showEmotionalLayer || !narrativeData[place.id]) {
      return '#3a86ff'; // Default blue
    }
    
    const emotional_context = narrativeData[place.id].emotional_context;
    if (emotional_context.joy > 0.7) return '#4CAF50'; // Green for joy
    if (emotional_context.nostalgia > 0.7) return '#FF9800'; // Orange for nostalgia
    if (emotional_context.adventure > 0.7) return '#E91E63'; // Pink for adventure
    if (emotional_context.peace > 0.7) return '#2196F3'; // Blue for peace
    
    return '#757575'; // Gray for neutral
  };

  const getMarkerSize = (place) => {
    if (!showTemporalLayer || !narrativeData[place.id]) {
      return 30;
    }
    
    const significance = narrativeData[place.id].narrative_significance || 0;
    return Math.max(20, Math.min(50, 20 + significance * 30));
  };

  const renderInfoWindow = (place) => {
    const narrative = narrativeData[place.id];
    const story = placeStories[place.id];
    
    return (
      <InfoWindow
        position={{ lat: place.lat, lng: place.long }}
        onCloseClick={() => setSelectedPlace(null)}
      >
        <div style={{ maxWidth: '300px' }}>
          <Card>
            <h4>{place.title || 'Unknown Location'}</h4>
            
            {narrative && (
              <div className="narrative-info mb-3">
                <p className="text-sm mb-2">
                  <strong>Life Phase:</strong> {narrative.life_phase}
                </p>
                
                {narrative.emotional_context && (
                  <div className="emotional-tags mb-2">
                    {Object.entries(narrative.emotional_context)
                      .filter(([_, value]) => value > 0.5)
                      .map(([emotion, value]) => (
                        <Chip 
                          key={emotion}
                          label={`${emotion} (${Math.round(value * 100)}%)`}
                          className="mr-1 mb-1"
                        />
                      ))
                    }
                  </div>
                )}
                
                {narrative.thematic_tags && (
                  <div className="thematic-tags mb-2">
                    {narrative.thematic_tags.map(tag => (
                      <Chip 
                        key={tag}
                        label={tag}
                        className="mr-1 mb-1 p-chip-outlined"
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {story && (
              <div className="place-story mb-3">
                <h5>Your Story Here</h5>
                <p className="text-sm">{story.summary}</p>
              </div>
            )}
            
            <div className="place-actions">
              <Button
                label="Generate Story"
                icon="pi pi-book"
                size="small"
                onClick={() => generatePlaceStory(place)}
                className="p-button-text mr-2"
              />
              <Button
                label="View Memories"
                icon="pi pi-images"
                size="small"
                onClick={() => {
                  if (setSelectedDateRange && place.start) {
                    setSelectedDateRange([new Date(place.start), new Date(place.end || place.start)]);
                  }
                  if (setSelectedIDs) {
                    setSelectedIDs([place.id]);
                  }
                }}
                className="p-button-text"
              />
            </div>
          </Card>
        </div>
      </InfoWindow>
    );
  };

  if (loadError) return "Error loading map";
  if (!isLoaded) return "Loading map...";

  const center = (geo && geo.length > 0) ? {
    lat: geo[0].lat,
    lng: geo[0].long,
  } : {
    lat: 47.6062,
    lng: -122.3321
  };

  return (
    <div className="enhanced-map-container">
      {showNarrativeLayers && (
        <div className="map-controls mb-3">
          <div className="flex gap-2 flex-wrap">
            <ToggleButton
              checked={showEmotionalLayer}
              onChange={(e) => setShowEmotionalLayer(e.value)}
              onLabel="Emotional Layer"
              offLabel="Emotional Layer"
              onIcon="pi pi-heart-fill"
              offIcon="pi pi-heart"
              className="p-button-sm"
            />
            <ToggleButton
              checked={showTemporalLayer}
              onChange={(e) => setShowTemporalLayer(e.value)}
              onLabel="Significance Layer"
              offLabel="Significance Layer"
              onIcon="pi pi-clock"
              offIcon="pi pi-clock"
              className="p-button-sm"
            />
            <ToggleButton
              checked={showJourneyPaths}
              onChange={(e) => setShowJourneyPaths(e.value)}
              onLabel="Journey Paths"
              offLabel="Journey Paths"
              onIcon="pi pi-map"
              offIcon="pi pi-map"
              className="p-button-sm"
            />
          </div>
        </div>
      )}
      
      <GoogleMap
        id="enhanced-map"
        mapContainerStyle={{ height: height, width: width || "100%" }}
        zoom={12}
        center={center}
        options={options}
        onLoad={onMapLoad}
      >
        {geo && geo.map((place, index) => (
          <Marker
            key={place.id || index}
            position={{ lat: place.lat, lng: place.long }}
            onClick={() => setSelectedPlace(place)}
            icon={{
              path: window.google?.maps?.SymbolPath?.CIRCLE || 0,
              fillColor: getMarkerColor(place),
              fillOpacity: 0.8,
              strokeColor: '#ffffff',
              strokeWeight: 2,
              scale: getMarkerSize(place) / 10
            }}
          />
        ))}
        
        {selectedPlace && renderInfoWindow(selectedPlace)}
        
        {/* Journey paths - simplified implementation */}
        {showJourneyPaths && geo && geo.length > 1 && (
          // This would require additional logic to draw paths between locations
          // For now, we'll just show the markers with enhanced styling
          null
        )}
      </GoogleMap>
    </div>
  );
};

export default EnhancedMapComponent;