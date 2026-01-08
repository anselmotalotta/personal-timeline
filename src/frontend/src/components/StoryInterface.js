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
import { Dropdown } from 'primereact/dropdown';
import { ProgressBar } from 'primereact/progressbar';
import { Image } from 'primereact/image';
import { Divider } from 'primereact/divider';
import { config } from '../Constants';

const StoryInterface = ({ memories, onStoryGenerated }) => {
  const [stories, setStories] = useState([]);
  const [selectedStory, setSelectedStory] = useState(null);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [narrativeMode, setNarrativeMode] = useState('chronological');
  const [isPlaying, setIsPlaying] = useState(false);

  const narrativeModes = [
    { label: 'Chronological', value: 'chronological' },
    { label: 'Thematic', value: 'thematic' },
    { label: 'People-Centered', value: 'people-centered' },
    { label: 'Place-Centered', value: 'place-centered' }
  ];

  // Load existing stories when component mounts
  useEffect(() => {
    loadExistingStories();
  }, []);

  const loadExistingStories = async () => {
    try {
      const response = await fetch(`${config.API_URL}/stories`);
      const data = await response.json();
      if (data.stories && data.stories.length > 0) {
        setStories(data.stories);
        // Automatically load the first story with full details
        await loadFullStory(data.stories[0].id);
      }
    } catch (error) {
      console.error('Error loading existing stories:', error);
    }
  };

  const loadFullStory = async (storyId) => {
    try {
      const response = await fetch(`${config.API_URL}/stories/${storyId}`);
      const fullStory = await response.json();
      setSelectedStory(fullStory);
      setCurrentChapter(0);
    } catch (error) {
      console.error('Error loading full story:', error);
    }
  };

  const generateStory = async () => {
    if (!memories || memories.length === 0) return;
    
    setIsGenerating(true);
    try {
      const response = await fetch(`${config.API_URL}/stories/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          memories: memories.map(m => m.id),
          narrative_mode: narrativeMode
        })
      });
      
      const story = await response.json();
      setStories(prev => [...prev, story]);
      setSelectedStory(story);
      setCurrentChapter(0);
      
      if (onStoryGenerated) {
        onStoryGenerated(story);
      }
    } catch (error) {
      console.error('Error generating story:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const playStory = () => {
    if (!selectedStory?.chapters || selectedStory.chapters.length === 0) return;
    
    setIsPlaying(true);
    // Auto-advance through chapters
    const interval = setInterval(() => {
      setCurrentChapter(prev => {
        if (prev >= selectedStory.chapters.length - 1) {
          setIsPlaying(false);
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 5000); // 5 seconds per chapter
  };

  const pauseStory = () => {
    setIsPlaying(false);
  };

  const nextChapter = () => {
    if (selectedStory?.chapters && currentChapter < selectedStory.chapters.length - 1) {
      setCurrentChapter(prev => prev + 1);
    }
  };

  const previousChapter = () => {
    if (currentChapter > 0) {
      setCurrentChapter(prev => prev - 1);
    }
  };

  const renderChapter = (chapter) => {
    return (
      <Card key={chapter.id} className="mb-3 shadow-2">
        <div className="story-chapter">
          <h3 className="chapter-title">{chapter.title}</h3>
          <p className="chapter-text">{chapter.narrative_text}</p>
          
          {chapter.media_elements && chapter.media_elements.map((media, index) => (
            <div key={index} className="chapter-media">
              {media.type === 'image' && (
                <Image 
                  src={media.url} 
                  alt={media.caption || 'Chapter image'} 
                  width="300" 
                  height="200" 
                  className="shadow-1 mb-2" 
                  preview 
                />
              )}
              {media.type === 'video' && (
                <video 
                  width="300" 
                  height="200" 
                  controls 
                  className="shadow-1 mb-2"
                >
                  <source src={media.url} type="video/mp4" />
                </video>
              )}
              {media.caption && (
                <p className="media-caption text-sm text-gray-600">{media.caption}</p>
              )}
            </div>
          ))}
        </div>
      </Card>
    );
  };

  return (
    <div className="story-interface">
      <div className="story-controls mb-4">
        <div className="flex align-items-center gap-3 mb-3">
          <Dropdown
            value={narrativeMode}
            options={narrativeModes}
            onChange={(e) => setNarrativeMode(e.value)}
            placeholder="Select narrative mode"
            className="w-12rem"
          />
          <Button
            label="Generate Story"
            icon="pi pi-book"
            onClick={generateStory}
            disabled={isGenerating || !memories || memories.length === 0}
            className="p-button-primary"
          />
        </div>
        
        {isGenerating && (
          <ProgressBar mode="indeterminate" className="mb-3" />
        )}
      </div>

      {selectedStory && (
        <div className="story-viewer">
          <Card className="story-header mb-3">
            <div className="flex justify-content-between align-items-center">
              <div>
                <h2>{selectedStory.title}</h2>
                <p className="text-gray-600">
                  {selectedStory.chapters ? (
                    `Chapter ${currentChapter + 1} of ${selectedStory.chapters.length}`
                  ) : (
                    `${selectedStory.chapter_count || 0} chapters available`
                  )}
                </p>
              </div>
              <div className="story-playback-controls">
                <Button
                  icon="pi pi-step-backward"
                  onClick={previousChapter}
                  disabled={currentChapter === 0 || !selectedStory.chapters}
                  className="p-button-text mr-2"
                />
                <Button
                  icon={isPlaying ? "pi pi-pause" : "pi pi-play"}
                  onClick={isPlaying ? pauseStory : playStory}
                  disabled={!selectedStory.chapters || selectedStory.chapters.length === 0}
                  className="p-button-rounded mr-2"
                />
                <Button
                  icon="pi pi-step-forward"
                  onClick={nextChapter}
                  disabled={!selectedStory.chapters || currentChapter >= selectedStory.chapters.length - 1}
                  className="p-button-text"
                />
              </div>
            </div>
          </Card>

          <div className="story-content">
            {selectedStory.chapters && selectedStory.chapters[currentChapter] ? (
              renderChapter(selectedStory.chapters[currentChapter])
            ) : (
              <Card className="mb-3 shadow-2">
                <div className="text-center p-4">
                  <i className="pi pi-book text-4xl text-gray-400 mb-3"></i>
                  <h3>Story chapters not loaded</h3>
                  <p className="text-gray-600 mb-3">
                    This story has {selectedStory.chapter_count || 0} chapters, but they need to be loaded.
                  </p>
                  <Button 
                    label="Load Full Story" 
                    icon="pi pi-download"
                    onClick={() => loadFullStory(selectedStory.id)}
                    className="p-button-primary"
                  />
                </div>
              </Card>
            )}
          </div>

          {selectedStory.chapters && (
            <div className="story-navigation mt-3">
              <div className="chapter-thumbnails flex gap-2 overflow-x-auto">
                {selectedStory.chapters.map((chapter, index) => (
                  <Button
                    key={chapter.id}
                    label={`${index + 1}`}
                    onClick={() => setCurrentChapter(index)}
                    className={`p-button-sm ${index === currentChapter ? 'p-button-primary' : 'p-button-outlined'}`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {stories.length > 1 && (
        <div className="story-library mt-4">
          <Divider />
          <h3>Your Stories</h3>
          <div className="grid">
            {stories.map((story, index) => (
              <div key={story.id} className="col-12 md:col-6 lg:col-4">
                <Card 
                  title={story.title}
                  subTitle={`${story.chapters?.length || story.chapter_count || 0} chapters`}
                  className="cursor-pointer hover:shadow-3"
                  onClick={() => {
                    setSelectedStory(story);
                    setCurrentChapter(0);
                  }}
                >
                  <p className="text-sm text-gray-600">
                    {story.narrative_mode} • {new Date(story.created_at || story.generated_at).toLocaleDateString()}
                  </p>
                </Card>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryInterface;