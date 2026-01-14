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

import React, { useState, useEffect } from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Image } from 'primereact/image';
import { Chip } from 'primereact/chip';
import { DataView } from 'primereact/dataview';
import { Dialog } from 'primereact/dialog';
import { ProgressBar } from 'primereact/progressbar';
import { config } from '../Constants';

const GalleryBrowser = ({ onGallerySelect, onCreateStory }) => {
  const [galleries, setGalleries] = useState([]);
  const [selectedGallery, setSelectedGallery] = useState(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [isCreatingGallery, setIsCreatingGallery] = useState(false);
  const [showGalleryDialog, setShowGalleryDialog] = useState(false);
  const [thematicGalleries, setThematicGalleries] = useState([]);

  // Pre-defined thematic gallery suggestions
  const defaultThemes = [
    'Moments with friends',
    'Creative periods',
    'Times of growth',
    'Travel adventures',
    'Quiet moments',
    'Celebrations',
    'Learning experiences',
    'Nature encounters'
  ];

  useEffect(() => {
    loadGalleries();
    loadThematicGalleries();
  }, []);

  const loadGalleries = async () => {
    try {
      const response = await fetch(`${config.API_URL}/galleries`);
      const data = await response.json();
      setGalleries(data.galleries || []);
    } catch (error) {
      console.error('Error loading galleries:', error);
    }
  };

  const loadThematicGalleries = async () => {
    try {
      // Since /galleries/themes doesn't exist, we'll create some default themes
      // based on the available galleries
      const response = await fetch(`${config.API_URL}/galleries`);
      const data = await response.json();
      
      // Create default thematic categories
      const defaultThemes = [
        { id: 'recent', name: 'Recent Photos', description: 'Latest photos in your archive' },
        { id: 'people', name: 'People', description: 'Photos with people' },
        { id: 'places', name: 'Places', description: 'Photos from different locations' },
        { id: 'memories', name: 'Memories', description: 'Special moments and memories' }
      ];
      
      setThematicGalleries(defaultThemes);
    } catch (error) {
      console.error('Error loading thematic galleries:', error);
      // Set default themes even if API call fails
      setThematicGalleries([
        { id: 'recent', name: 'Recent Photos', description: 'Latest photos in your archive' }
      ]);
    }
  };

  const createThematicGallery = async (theme) => {
    setIsCreatingGallery(true);
    try {
      const response = await fetch(`${config.API_URL}/galleries/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          theme: theme
        })
      });
      
      const gallery = await response.json();
      setGalleries(prev => [...prev, gallery]);
      setSelectedGallery(gallery);
      setShowGalleryDialog(true);
    } catch (error) {
      console.error('Error creating thematic gallery:', error);
    } finally {
      setIsCreatingGallery(false);
    }
  };

  const createCustomGallery = async () => {
    if (!customPrompt.trim()) return;
    
    setIsCreatingGallery(true);
    try {
      const response = await fetch(`${config.API_URL}/galleries/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: customPrompt
        })
      });
      
      const gallery = await response.json();
      setGalleries(prev => [...prev, gallery]);
      setSelectedGallery(gallery);
      setShowGalleryDialog(true);
      setCustomPrompt('');
    } catch (error) {
      console.error('Error creating custom gallery:', error);
    } finally {
      setIsCreatingGallery(false);
    }
  };

  const convertGalleryToStory = async (gallery) => {
    try {
      const response = await fetch(`${config.API_URL}/api/galleries/${gallery.id}/story`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const story = await response.json();
      if (onCreateStory) {
        onCreateStory(story);
      }
    } catch (error) {
      console.error('Error converting gallery to story:', error);
    }
  };

  const renderGalleryCard = (gallery) => {
    const previewImages = gallery.memories?.slice(0, 4) || [];
    
    return (
      <Card 
        key={gallery.id}
        className="gallery-card cursor-pointer hover:shadow-3 mb-3"
        onClick={() => {
          setSelectedGallery(gallery);
          setShowGalleryDialog(true);
          if (onGallerySelect) {
            onGallerySelect(gallery);
          }
        }}
      >
        <div className="gallery-preview">
          <div className="gallery-images grid">
            {previewImages.map((memory, index) => (
              <div key={index} className="col-6">
                {memory.image && (
                  <Image
                    src={memory.image}
                    alt={memory.title}
                    width="100%"
                    height="80"
                    className="gallery-thumbnail"
                    style={{ objectFit: 'cover' }}
                  />
                )}
              </div>
            ))}
          </div>
          
          <div className="gallery-info mt-3">
            <h4>{gallery.title}</h4>
            <p className="text-sm text-gray-600 mb-2">{gallery.description}</p>
            
            <div className="gallery-meta flex justify-content-between align-items-center">
              <span className="text-xs text-gray-500">
                {gallery.memories?.length || 0} memories
              </span>
              <Chip 
                label={gallery.creation_method} 
                className="p-chip-outlined"
              />
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderGalleryDialog = () => {
    if (!selectedGallery) return null;
    
    return (
      <Dialog
        header={selectedGallery.title}
        visible={showGalleryDialog}
        onHide={() => setShowGalleryDialog(false)}
        style={{ width: '80vw', maxWidth: '1000px' }}
        maximizable
      >
        <div className="gallery-detail">
          <p className="mb-4">{selectedGallery.description}</p>
          
          <div className="gallery-actions mb-4">
            <Button
              label="Create Story from Gallery"
              icon="pi pi-book"
              onClick={() => convertGalleryToStory(selectedGallery)}
              className="p-button-primary mr-2"
            />
            <Button
              label="View All Memories"
              icon="pi pi-images"
              onClick={() => {
                // This would navigate to a detailed memory view
                console.log('View all memories for gallery:', selectedGallery.id);
              }}
              className="p-button-outlined"
            />
          </div>
          
          <div className="gallery-memories">
            <DataView
              value={selectedGallery.memories || []}
              layout="grid"
              itemTemplate={(memory) => (
                <div className="col-12 md:col-6 lg:col-4 p-2">
                  <Card className="memory-card">
                    {memory.image && (
                      <Image
                        src={memory.image}
                        alt={memory.title}
                        width="100%"
                        height="200"
                        className="mb-2"
                        preview
                      />
                    )}
                    <h5>{memory.title}</h5>
                    <p className="text-sm text-gray-600">
                      {new Date(memory.date).toLocaleDateString()}
                    </p>
                    {memory.summary && (
                      <p className="text-sm mt-2">{memory.summary}</p>
                    )}
                  </Card>
                </div>
              )}
              paginator
              rows={9}
            />
          </div>
        </div>
      </Dialog>
    );
  };

  return (
    <div className="gallery-browser">
      <div className="gallery-creation mb-4">
        <Card title="Create New Gallery" className="mb-4">
          <div className="custom-gallery-creation mb-4">
            <div className="p-inputgroup">
              <InputText
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Describe the gallery you want to create (e.g., 'Photos from my college years' or 'Moments of joy')"
                className="w-full"
              />
              <Button
                icon="pi pi-plus"
                onClick={createCustomGallery}
                disabled={!customPrompt.trim() || isCreatingGallery}
                className="p-button-primary"
              />
            </div>
          </div>
          
          <div className="thematic-suggestions">
            <h5>Quick Themes</h5>
            <div className="flex flex-wrap gap-2">
              {defaultThemes.map(theme => (
                <Button
                  key={theme}
                  label={theme}
                  onClick={() => createThematicGallery(theme)}
                  disabled={isCreatingGallery}
                  className="p-button-outlined p-button-sm"
                />
              ))}
            </div>
          </div>
          
          {isCreatingGallery && (
            <ProgressBar mode="indeterminate" className="mt-3" />
          )}
        </Card>
      </div>

      <div className="existing-galleries">
        <h3>Your Galleries</h3>
        <div className="grid">
          {galleries.map(gallery => (
            <div key={gallery.id} className="col-12 md:col-6 lg:col-4">
              {renderGalleryCard(gallery)}
            </div>
          ))}
        </div>
        
        {galleries.length === 0 && (
          <Card className="text-center p-4">
            <i className="pi pi-images text-6xl text-gray-400 mb-3"></i>
            <h4>No galleries yet</h4>
            <p className="text-gray-600">Create your first gallery using the tools above</p>
          </Card>
        )}
      </div>

      {renderGalleryDialog()}
    </div>
  );
};

export default GalleryBrowser;