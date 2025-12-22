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

import React, { useState, useEffect, useRef } from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Slider } from 'primereact/slider';
import { Dropdown } from 'primereact/dropdown';
import { ToggleButton } from 'primereact/togglebutton';
import { ProgressBar } from 'primereact/progressbar';
import { Image } from 'primereact/image';
import { config } from '../Constants';

const StoryPlayback = ({ story, onChapterChange, onPlaybackComplete }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [autoAdvance, setAutoAdvance] = useState(true);
  const [narratorVoice, setNarratorVoice] = useState('documentary');
  const [showCaptions, setShowCaptions] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [chapterProgress, setChapterProgress] = useState(0);
  const [totalProgress, setTotalProgress] = useState(0);

  const audioRef = useRef(null);
  const intervalRef = useRef(null);
  const chapterTimeoutRef = useRef(null);

  const playbackSpeeds = [
    { label: '0.5x', value: 0.5 },
    { label: '0.75x', value: 0.75 },
    { label: '1x', value: 1.0 },
    { label: '1.25x', value: 1.25 },
    { label: '1.5x', value: 1.5 },
    { label: '2x', value: 2.0 }
  ];

  const narratorVoices = [
    { label: 'Documentary', value: 'documentary' },
    { label: 'Memoir', value: 'memoir' },
    { label: 'Minimalist', value: 'minimalist' }
  ];

  useEffect(() => {
    if (story && onChapterChange) {
      onChapterChange(currentChapter);
    }
  }, [currentChapter, story, onChapterChange]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (chapterTimeoutRef.current) {
        clearTimeout(chapterTimeoutRef.current);
      }
    };
  }, []);

  const generateAudioNarration = async (chapter) => {
    if (!audioEnabled) return null;
    
    try {
      const response = await fetch(`${config.API_URL}/api/stories/narrate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: chapter.narrative_text,
          voice: narratorVoice,
          speed: playbackSpeed
        })
      });
      
      const audioBlob = await response.blob();
      return URL.createObjectURL(audioBlob);
    } catch (error) {
      console.error('Error generating audio narration:', error);
      return null;
    }
  };

  const playChapter = async (chapterIndex) => {
    if (!story || !story.chapters[chapterIndex]) return;
    
    const chapter = story.chapters[chapterIndex];
    setCurrentChapter(chapterIndex);
    setChapterProgress(0);
    
    if (audioEnabled) {
      const audioUrl = await generateAudioNarration(chapter);
      if (audioUrl && audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.playbackRate = playbackSpeed;
        audioRef.current.play();
      }
    }
    
    // Start progress tracking
    const chapterDuration = chapter.duration_seconds || 5000; // Default 5 seconds
    const progressInterval = 100; // Update every 100ms
    const progressIncrement = (progressInterval / chapterDuration) * 100;
    
    intervalRef.current = setInterval(() => {
      setChapterProgress(prev => {
        const newProgress = prev + progressIncrement;
        if (newProgress >= 100) {
          clearInterval(intervalRef.current);
          if (autoAdvance && chapterIndex < story.chapters.length - 1) {
            // Auto-advance to next chapter
            chapterTimeoutRef.current = setTimeout(() => {
              playChapter(chapterIndex + 1);
            }, 500);
          } else if (chapterIndex >= story.chapters.length - 1) {
            // Story complete
            setIsPlaying(false);
            if (onPlaybackComplete) {
              onPlaybackComplete();
            }
          }
          return 100;
        }
        return newProgress;
      });
    }, progressInterval);
  };

  const play = () => {
    setIsPlaying(true);
    playChapter(currentChapter);
  };

  const pause = () => {
    setIsPlaying(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    if (chapterTimeoutRef.current) {
      clearTimeout(chapterTimeoutRef.current);
    }
    if (audioRef.current) {
      audioRef.current.pause();
    }
  };

  const stop = () => {
    pause();
    setCurrentChapter(0);
    setChapterProgress(0);
    setTotalProgress(0);
  };

  const nextChapter = () => {
    if (currentChapter < story.chapters.length - 1) {
      const nextIndex = currentChapter + 1;
      if (isPlaying) {
        pause();
        playChapter(nextIndex);
        setIsPlaying(true);
      } else {
        setCurrentChapter(nextIndex);
      }
    }
  };

  const previousChapter = () => {
    if (currentChapter > 0) {
      const prevIndex = currentChapter - 1;
      if (isPlaying) {
        pause();
        playChapter(prevIndex);
        setIsPlaying(true);
      } else {
        setCurrentChapter(prevIndex);
      }
    }
  };

  const seekToChapter = (chapterIndex) => {
    if (isPlaying) {
      pause();
      playChapter(chapterIndex);
      setIsPlaying(true);
    } else {
      setCurrentChapter(chapterIndex);
    }
  };

  const updateTotalProgress = () => {
    if (!story || !story.chapters.length) return 0;
    
    const completedChapters = currentChapter;
    const currentChapterProgress = chapterProgress / 100;
    const totalChapters = story.chapters.length;
    
    return ((completedChapters + currentChapterProgress) / totalChapters) * 100;
  };

  useEffect(() => {
    setTotalProgress(updateTotalProgress());
  }, [currentChapter, chapterProgress, story]);

  if (!story || !story.chapters.length) {
    return (
      <Card className="story-playback-empty text-center p-4">
        <i className="pi pi-play-circle text-6xl text-gray-400 mb-3"></i>
        <h4>No story selected</h4>
        <p className="text-gray-600">Select a story to begin playback</p>
      </Card>
    );
  }

  const currentChapterData = story.chapters[currentChapter];

  return (
    <div className="story-playback">
      <Card className="playback-controls mb-3">
        <div className="playback-header flex justify-content-between align-items-center mb-3">
          <div className="story-info">
            <h3>{story.title}</h3>
            <p className="text-gray-600">
              Chapter {currentChapter + 1} of {story.chapters.length}
            </p>
          </div>
          
          <div className="playback-settings flex gap-2">
            <Dropdown
              value={playbackSpeed}
              options={playbackSpeeds}
              onChange={(e) => setPlaybackSpeed(e.value)}
              className="w-6rem"
            />
            
            <ToggleButton
              checked={audioEnabled}
              onChange={(e) => setAudioEnabled(e.value)}
              onLabel="Audio On"
              offLabel="Audio Off"
              onIcon="pi pi-volume-up"
              offIcon="pi pi-volume-off"
              className="p-button-sm"
            />
            
            <ToggleButton
              checked={showCaptions}
              onChange={(e) => setShowCaptions(e.value)}
              onLabel="Captions"
              offLabel="Captions"
              onIcon="pi pi-eye"
              offIcon="pi pi-eye-slash"
              className="p-button-sm"
            />
          </div>
        </div>
        
        <div className="progress-section mb-3">
          <div className="progress-labels flex justify-content-between text-sm text-gray-600 mb-1">
            <span>Chapter Progress</span>
            <span>{Math.round(chapterProgress)}%</span>
          </div>
          <ProgressBar value={chapterProgress} className="mb-2" />
          
          <div className="progress-labels flex justify-content-between text-sm text-gray-600 mb-1">
            <span>Story Progress</span>
            <span>{Math.round(totalProgress)}%</span>
          </div>
          <ProgressBar value={totalProgress} />
        </div>
        
        <div className="main-controls flex justify-content-center align-items-center gap-2 mb-3">
          <Button
            icon="pi pi-step-backward"
            onClick={previousChapter}
            disabled={currentChapter === 0}
            className="p-button-rounded p-button-outlined"
          />
          
          <Button
            icon={isPlaying ? "pi pi-pause" : "pi pi-play"}
            onClick={isPlaying ? pause : play}
            className="p-button-rounded p-button-lg p-button-primary"
          />
          
          <Button
            icon="pi pi-stop"
            onClick={stop}
            className="p-button-rounded p-button-outlined"
          />
          
          <Button
            icon="pi pi-step-forward"
            onClick={nextChapter}
            disabled={currentChapter >= story.chapters.length - 1}
            className="p-button-rounded p-button-outlined"
          />
        </div>
        
        <div className="advanced-controls flex justify-content-center align-items-center gap-3">
          <ToggleButton
            checked={autoAdvance}
            onChange={(e) => setAutoAdvance(e.value)}
            onLabel="Auto-advance"
            offLabel="Manual"
            className="p-button-sm"
          />
          
          {audioEnabled && (
            <Dropdown
              value={narratorVoice}
              options={narratorVoices}
              onChange={(e) => setNarratorVoice(e.value)}
              placeholder="Narrator voice"
              className="w-8rem"
            />
          )}
        </div>
      </Card>

      <Card className="chapter-display">
        <div className="chapter-content">
          <h4 className="chapter-title mb-3">{currentChapterData.title}</h4>
          
          {showCaptions && (
            <div className="chapter-text mb-4">
              <p className="text-lg line-height-3">{currentChapterData.narrative_text}</p>
            </div>
          )}
          
          <div className="chapter-media">
            {currentChapterData.media_elements?.map((media, index) => (
              <div key={index} className="media-element mb-3">
                {media.type === 'image' && (
                  <div className="text-center">
                    <Image
                      src={media.url}
                      alt={media.caption || 'Chapter image'}
                      width="400"
                      height="300"
                      className="shadow-2"
                      preview
                    />
                    {media.caption && showCaptions && (
                      <p className="media-caption text-sm text-gray-600 mt-2">
                        {media.caption}
                      </p>
                    )}
                  </div>
                )}
                
                {media.type === 'video' && (
                  <div className="text-center">
                    <video
                      width="400"
                      height="300"
                      controls
                      className="shadow-2"
                    >
                      <source src={media.url} type="video/mp4" />
                    </video>
                    {media.caption && showCaptions && (
                      <p className="media-caption text-sm text-gray-600 mt-2">
                        {media.caption}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </Card>

      <div className="chapter-navigation mt-3">
        <div className="chapter-thumbnails flex gap-2 overflow-x-auto p-2">
          {story.chapters.map((chapter, index) => (
            <Button
              key={chapter.id}
              label={`${index + 1}`}
              onClick={() => seekToChapter(index)}
              className={`p-button-sm chapter-thumb ${
                index === currentChapter ? 'p-button-primary' : 'p-button-outlined'
              } ${index < currentChapter ? 'chapter-completed' : ''}`}
              tooltip={chapter.title}
            />
          ))}
        </div>
      </div>

      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  );
};

export default StoryPlayback;