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

import './App.css';

import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'primereact/terminal';
import { TerminalService } from 'primereact/terminalservice';
import { ProgressBar } from 'primereact/progressbar';
import { TabView, TabPanel } from 'primereact/tabview';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { Divider } from 'primereact/divider';
import { Toolbar } from 'primereact/toolbar';
import { Badge } from 'primereact/badge';
import { Chip } from 'primereact/chip';
import { ToggleButton } from 'primereact/togglebutton';

// Enhanced AI Components
import StoryInterface from './components/StoryInterface';
import GalleryBrowser from './components/GalleryBrowser';
import PeopleDashboard from './components/PeopleDashboard';
import EnhancedMapComponent from './components/EnhancedMapComponent';
import AIStatusBadge from './components/AIStatusBadge';
import DisabledFeature from './components/DisabledFeature';
import useAIStatus from './hooks/useAIStatus';
import FacebookTimeline from './facebook-timeline/FacebookTimeline';

// Legacy components for fallback
import GoogleMapComponent from './map/GoogleMapComponent';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coy } from 'react-syntax-highlighter/dist/esm/styles/prism';

import importDigitalData from './service/DigitalDataImportor';
import { config } from './Constants';

function EnhancedApp() {
  // AI Status Hook
  const aiStatus = useAIStatus();

  // Core state
  const [tracks, setTracks] = useState([]);
  const [memories, setMemories] = useState([]);
  const [activeView, setActiveView] = useState('stories');
  const [isInitialized, setIsInitialized] = useState(false);
  const [selectedDateRange, setSelectedDateRange] = useState(null);
  
  // AI Services state
  const [aiServices, setAiServices] = useState({
    enhanced_memory: false,
    people_intelligence: false,
    gallery_curation: false,
    story_generation: false,
    place_exploration: false
  });
  
  // Enhanced Q&A state
  const [answer, setAnswer] = useState("Welcome to your AI-Augmented Personal Archive");
  const [running, setRunning] = useState(false);
  const [conversationContext, setConversationContext] = useState(null);
  
  // Selected content state
  const [selectedStory, setSelectedStory] = useState(null);
  const [selectedGallery, setSelectedGallery] = useState(null);
  const [selectedPerson, setSelectedPerson] = useState(null);
  
  // Enhanced state for Facebook Timeline integration
  const [facebookStats, setFacebookStats] = useState(null);
  
  // Toast for notifications
  const toast = useRef(null);

  // Load Facebook Timeline stats
  useEffect(() => {
    const loadFacebookStats = async () => {
      try {
        const response = await fetch(`${config.API_URL}/facebook/stats`);
        if (response.ok) {
          const data = await response.json();
          setFacebookStats(data.statistics);
        }
      } catch (error) {
        console.warn('Could not load Facebook stats:', error);
      }
    };
    
    loadFacebookStats();
  }, []);

  /**
   * Initialize AI services on startup
   */
  useEffect(() => {
    console.log('🚀 EnhancedApp: Starting initialization...');
    console.log('🔧 Toast ref status:', toast.current ? 'initialized' : 'null');
    console.log('🤖 AI Status:', aiStatus);
    console.log('🔍 AI Available:', aiStatus.isAIAvailable);
    console.log('🔍 AI Loading:', aiStatus.loading);
    
    // Wait for AI status to be loaded before initializing services
    if (!aiStatus.loading) {
      console.log('✅ AI status loaded, initializing services...');
      initializeAIServices();
    } else {
      console.log('⏳ Waiting for AI status to load...');
    }
    
    // Ensure toast is available before calling importDigitalData
    if (toast.current) {
      console.log('📊 Starting data import...');
      importDigitalData(tracks, setTracks, setSelectedDateRange, toast);
    } else {
      console.warn('⚠️ Toast not ready, delaying data import...');
      setTimeout(() => {
        console.log('🔄 Retrying data import...');
        importDigitalData(tracks, setTracks, setSelectedDateRange, toast);
      }, 500);
    }
  }, [aiStatus.loading]);

  /**
   * Convert tracks to memories format for AI components
   */
  useEffect(() => {
    const convertedMemories = [];
    tracks.forEach(track => {
      track.elements.forEach(element => {
        convertedMemories.push({
          id: element.id,
          title: element.title,
          date: element.start,
          content: element.data,
          type: track.title,
          image: element.data.img_url,
          location: element.lat && element.long ? {
            lat: element.lat,
            lng: element.long
          } : null
        });
      });
    });
    setMemories(convertedMemories);
  }, [tracks]);

  const initializeAIServices = async () => {
    console.log('🤖 Checking AI service availability...');
    
    // Use the AI status from the hook instead of trying to initialize services
    // that don't have API keys
    if (!aiStatus.isAIAvailable) {
      console.log('❌ No AI providers available - services disabled');
      setAiServices({
        enhanced_memory: false,
        people_intelligence: false,
        gallery_curation: false,
        story_generation: false,
        place_exploration: false
      });
      setIsInitialized(true);
      
      if (toast.current) {
        toast.current.show({
          severity: 'warn',
          summary: 'AI Features Disabled',
          detail: 'Add API keys to enable AI features',
          life: 5000
        });
      }
      return;
    }

    // Only try to initialize services if AI providers are available
    const services = [
      { name: 'enhanced_memory', endpoint: '/enhanced/launch', requires: 'semantic_search' },
      { name: 'people_intelligence', endpoint: '/people/launch', requires: 'people_intelligence' },
      { name: 'gallery_curation', endpoint: '/galleries/launch', requires: 'smart_galleries' },
      { name: 'story_generation', endpoint: '/stories/launch', requires: 'story_generation' },
      { name: 'place_exploration', endpoint: '/places/launch', requires: 'semantic_search' }
    ];

    const serviceStatus = {};
    
    for (const service of services) {
      // Check if the required AI feature is available
      const featureAvailable = aiStatus.features[service.requires];
      
      if (!featureAvailable) {
        console.log(`⚠️ ${service.name} disabled - missing required AI capability`);
        serviceStatus[service.name] = false;
        continue;
      }

      try {
        console.log(`🔄 Initializing ${service.name}...`);
        const response = await fetch(`${config.QA_URL}${service.endpoint}`);
        const result = await response.json();
        serviceStatus[service.name] = response.ok && !result.error;
        
        if (serviceStatus[service.name]) {
          console.log(`✅ ${service.name} initialized successfully`);
        } else {
          console.warn(`⚠️ ${service.name} failed to initialize:`, result.error);
        }
      } catch (error) {
        console.error(`❌ ${service.name} initialization error:`, error);
        serviceStatus[service.name] = false;
      }
    }
    
    setAiServices(serviceStatus);
    setIsInitialized(true);
    
    // Show initialization status
    const successCount = Object.values(serviceStatus).filter(Boolean).length;
    console.log(`🎯 AI Services initialized: ${successCount}/5 services ready`);
    
    if (toast.current) {
      const severity = successCount === 0 ? 'error' : successCount > 3 ? 'success' : 'warn';
      const summary = successCount === 0 ? 'AI Features Disabled' : 'AI Services Initialized';
      const detail = successCount === 0 ? 'Add API keys to enable AI features' : `${successCount}/5 services ready`;
      
      toast.current.show({
        severity,
        summary,
        detail,
        life: 3000
      });
    }
  };

  /**
   * Enhanced Q&A handler with conversational context
   */
  const handleEnhancedQuery = async (query) => {
    if (!aiServices.enhanced_memory) {
      toast.current?.show({
        severity: 'error',
        summary: 'Service Unavailable',
        detail: 'Enhanced memory retrieval is not available',
        life: 3000
      });
      return;
    }

    setRunning(true);
    try {
      const response = await fetch(`${config.QA_URL}/enhanced/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          session_id: 'main_session'
        })
      });
      
      const result = await response.json();
      setAnswer(result);
      setConversationContext(result);
      
      // Switch to appropriate view based on query result
      if (result.composite_memories?.length > 0) {
        setActiveView('enhanced_qa');
      }
      
    } catch (error) {
      console.error('Enhanced query error:', error);
      setAnswer({ error: 'Failed to process query' });
    } finally {
      setRunning(false);
    }
  };

  /**
   * Terminal command handler
   */
  const commandHandler = (text) => {
    let argsIndex = text.indexOf(' ');
    let command = argsIndex !== -1 ? text.substring(0, argsIndex) : text;

    switch (command) {
      case 'clear':
        TerminalService.emit('clear');
        break;
      case 'help':
        TerminalService.emit('response', 
          'Available commands:\n' +
          '• Ask any question about your memories\n' +
          '• "stories" - Switch to story generation\n' +
          '• "galleries" - Browse intelligent galleries\n' +
          '• "people" - Explore people in your life\n' +
          '• "map" - View narrative-enhanced map\n' +
          '• "facebook" - View Facebook posts timeline\n' +
          '• "clear" - Clear terminal\n'
        );
        break;
      case 'stories':
        setActiveView('stories');
        TerminalService.emit('response', 'Switched to story generation view');
        break;
      case 'galleries':
        setActiveView('galleries');
        TerminalService.emit('response', 'Switched to gallery browser');
        break;
      case 'people':
        setActiveView('people');
        TerminalService.emit('response', 'Switched to people dashboard');
        break;
      case 'map':
        setActiveView('map');
        TerminalService.emit('response', 'Switched to narrative map view');
        break;
      case 'facebook':
        setActiveView('facebook');
        TerminalService.emit('response', 'Switched to Facebook posts timeline');
        break;
      default:
        TerminalService.emit('response', 'Processing your query...');
        handleEnhancedQuery(text);
        break;
    }
  };

  useEffect(() => {
    TerminalService.on('command', commandHandler);
    return () => {
      TerminalService.off('command', commandHandler);
    };
  }, [aiServices]);

  /**
   * Render AI service status indicators
   */
  const renderServiceStatus = () => {
    const serviceLabels = {
      enhanced_memory: 'Memory',
      people_intelligence: 'People',
      gallery_curation: 'Galleries',
      story_generation: 'Stories',
      place_exploration: 'Places'
    };

    return (
      <div className="service-status flex gap-2 align-items-center">
        <span className="text-sm text-gray-600 mr-2">AI Services:</span>
        {Object.entries(aiServices).map(([service, status]) => (
          <Chip
            key={service}
            label={serviceLabels[service]}
            className={status ? 'p-chip-success' : 'p-chip-danger'}
            icon={status ? 'pi pi-check' : 'pi pi-times'}
          />
        ))}
      </div>
    );
  };

  /**
   * Render enhanced Q&A results
   */
  const renderEnhancedQAResults = () => {
    if (!answer || typeof answer === 'string') {
      return <p>{answer}</p>;
    }

    return (
      <div className="enhanced-qa-results">
        {answer.narrative_answer && (
          <Card title="Response" className="mb-3">
            <p>{answer.narrative_answer}</p>
            {answer.confidence_score && (
              <div className="mt-2">
                <small className="text-gray-600">
                  Confidence: {Math.round(answer.confidence_score * 100)}%
                </small>
              </div>
            )}
          </Card>
        )}

        {answer.composite_memories?.length > 0 && (
          <Card title="Related Memories" className="mb-3">
            <div className="composite-memories">
              {answer.composite_memories.map((memory, index) => (
                <div key={index} className="memory-cluster mb-3 p-3 border-1 border-gray-200 border-round">
                  <h5>{memory.theme || `Memory Cluster ${index + 1}`}</h5>
                  <p className="text-sm text-gray-600 mb-2">
                    {memory.memory_count} memories • {memory.time_span}
                  </p>
                  {memory.representative_content && (
                    <p className="text-sm">{memory.representative_content}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {answer.related_themes?.length > 0 && (
          <Card title="Related Themes" className="mb-3">
            <div className="flex flex-wrap gap-2">
              {answer.related_themes.map((theme, index) => (
                <Chip key={index} label={theme} className="p-chip-outlined" />
              ))}
            </div>
          </Card>
        )}

        {answer.source_memories?.length > 0 && (
          <Card title="Source Evidence" className="mb-3">
            <div className="source-memories">
              {answer.source_memories.slice(0, 5).map((source, index) => (
                <div key={index} className="source-memory mb-2 p-2 bg-gray-50 border-round">
                  <div className="flex justify-content-between align-items-start">
                    <div>
                      <strong>{source.title}</strong>
                      <p className="text-sm text-gray-600 mt-1">{source.summary}</p>
                    </div>
                    <small className="text-gray-500">
                      {new Date(source.date).toLocaleDateString()}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  };

  /**
   * Handle story creation from various sources
   */
  const handleStoryCreation = (source) => {
    setSelectedStory(source);
    setActiveView('stories');
    toast.current?.show({
      severity: 'info',
      summary: 'Story Creation',
      detail: 'Generating story from selected content...',
      life: 3000
    });
  };

  /**
   * Handle gallery selection
   */
  const handleGallerySelection = (gallery) => {
    setSelectedGallery(gallery);
    toast.current?.show({
      severity: 'info',
      summary: 'Gallery Selected',
      detail: `Viewing "${gallery.title}"`,
      life: 3000
    });
  };

  /**
   * Handle person selection
   */
  const handlePersonSelection = (person) => {
    setSelectedPerson(person);
    toast.current?.show({
      severity: 'info',
      summary: 'Person Selected',
      detail: `Exploring relationship with ${person.name}`,
      life: 3000
    });
  };

  if (!isInitialized) {
    console.log('⏳ App initializing...');
    return (
      <div className="App flex align-items-center justify-content-center" style={{ height: '100vh' }}>
        <Card className="text-center">
          <i className="pi pi-spin pi-spinner text-4xl text-primary mb-3"></i>
          <h3>Initializing AI-Augmented Personal Archive</h3>
          <p className="text-gray-600">Setting up your intelligent memory system...</p>
          <ProgressBar mode="indeterminate" className="mt-3" />
        </Card>
      </div>
    );
  }

  console.log('🎯 App fully initialized, rendering main interface...');

  return (
    <div className="App">
      <Toast ref={toast} />

      {/* Enhanced Header */}
      <div className="app-header mb-4">
        <div className="flex justify-content-between align-items-center">
          <div>
            <h1 className="my-0 title">AI-Augmented Personal Archive</h1>
            <h3 className="font-light text-gray-600">Intelligent exploration of your digital memories</h3>
          </div>
          {renderServiceStatus()}
        </div>
        <Divider className="my-3" />
      </div>

      {/* Enhanced Navigation */}
      <Toolbar 
        start={
          <div className="navigation-buttons flex gap-2">
            {aiStatus.hasStoryGeneration ? (
              <Button
                label="Stories"
                icon="pi pi-book"
                onClick={() => setActiveView('stories')}
                className={activeView === 'stories' ? 'p-button-primary' : 'p-button-outlined'}
              />
            ) : (
              <Button
                label="Stories"
                icon="pi pi-book"
                disabled
                className="p-button-outlined"
                tooltip="Add OpenAI or Anthropic API key to enable story generation"
                tooltipOptions={{ position: 'bottom' }}
              />
            )}
            
            {aiStatus.hasSmartGalleries ? (
              <Button
                label="Galleries"
                icon="pi pi-images"
                onClick={() => setActiveView('galleries')}
                className={activeView === 'galleries' ? 'p-button-primary' : 'p-button-outlined'}
              />
            ) : (
              <Button
                label="Galleries"
                icon="pi pi-images"
                disabled
                className="p-button-outlined"
                tooltip="Add any AI provider key to enable smart galleries"
                tooltipOptions={{ position: 'bottom' }}
              />
            )}
            
            {aiStatus.hasPeopleIntelligence ? (
              <Button
                label="People"
                icon="pi pi-users"
                onClick={() => setActiveView('people')}
                className={activeView === 'people' ? 'p-button-primary' : 'p-button-outlined'}
              />
            ) : (
              <Button
                label="People"
                icon="pi pi-users"
                disabled
                className="p-button-outlined"
                tooltip="Add OpenAI or Google AI key to enable people intelligence"
                tooltipOptions={{ position: 'bottom' }}
              />
            )}
            
            <Button
              label="Places"
              icon="pi pi-map"
              onClick={() => setActiveView('map')}
              className={activeView === 'map' ? 'p-button-primary' : 'p-button-outlined'}
            />
            
            <Button
              label="Facebook Timeline"
              icon="pi pi-chart-bar"
              onClick={() => setActiveView('facebook')}
              className={activeView === 'facebook' ? 'p-button-primary' : 'p-button-outlined'}
            />
            
            {aiStatus.hasSemanticSearch ? (
              <Button
                label="Q&A"
                icon="pi pi-comments"
                onClick={() => setActiveView('enhanced_qa')}
                className={activeView === 'enhanced_qa' ? 'p-button-primary' : 'p-button-outlined'}
              />
            ) : (
              <Button
                label="Q&A"
                icon="pi pi-comments"
                disabled
                className="p-button-outlined"
                tooltip="Add any AI provider key to enable enhanced Q&A"
                tooltipOptions={{ position: 'bottom' }}
              />
            )}
          </div>
        }
        end={
          <div className="memory-stats">
            <Badge value={facebookStats?.total_posts || memories.length} className="mr-2" />
            <span className="text-sm text-gray-600">
              {facebookStats?.total_posts ? 'Facebook posts' : 'memories loaded'}
            </span>
          </div>
        }
        className="mb-4"
      />

      {/* Enhanced Q&A Section */}
      <div className="enhanced-qa-section mb-4">
        <Card>
          {!aiStatus.hasSemanticSearch ? (
            <DisabledFeature
              featureName="AI-Powered Memory Search"
              description="Use natural language to explore your personal history with AI-powered understanding and contextual memory retrieval."
              requiredProvider="OpenAI, Anthropic, or Google AI"
              icon="🧠"
              aiStatus={aiStatus}
            >
              <div style={{ height: '300px', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center', color: '#6c757d' }}>
                  <i className="pi pi-comments" style={{ fontSize: '48px', marginBottom: '16px' }}></i>
                  <p>AI Memory Search Interface</p>
                </div>
              </div>
            </DisabledFeature>
          ) : (
            <div className="grid">
              <div className="col-12 lg:col-8">
                <h3>Ask About Your Memories</h3>
                <p className="text-gray-600 mb-3">
                  Use natural language to explore your personal history with AI-powered understanding
                </p>
                
                <div className="sample-queries mb-3">
                  <span className="text-sm text-gray-600 mr-2">Try asking:</span>
                  {[
                    "Tell me about my creative periods",
                    "Who are the most important people in my life?",
                    "What were my happiest moments?",
                    "Show me times when I was learning something new"
                  ].map((query, index) => (
                    <Button
                      key={index}
                      label={query}
                      onClick={() => {
                        TerminalService.emit('command', query);
                      }}
                      className="p-button-text p-button-sm mr-2 mb-1"
                    />
                  ))}
                </div>
                
                <Terminal
                  className="text-lg line-height-3"
                  style={{ height: '300px' }}
                  welcomeMessage="Welcome to your AI-Augmented Personal Archive. Ask me anything about your memories, or type 'help' for commands."
                  prompt="Archive AI $ "
                />
                
                {running && (
                  <ProgressBar mode="indeterminate" className="mt-2" />
                )}
              </div>
              
              <div className="col-12 lg:col-4">
                <div className="quick-insights">
                  <h4>Quick Insights</h4>
                  <div className="insights-grid">
                    <Card className="text-center mb-2">
                      <i className="pi pi-calendar text-2xl text-primary mb-2"></i>
                      <h5>{facebookStats?.total_posts || memories.length}</h5>
                      <p className="text-sm text-gray-600">
                        {facebookStats?.total_posts ? 'Facebook Posts' : 'Total Memories'}
                      </p>
                    </Card>
                    
                    <Card className="text-center mb-2">
                      <i className="pi pi-users text-2xl text-primary mb-2"></i>
                      <h5>Auto-Detected</h5>
                      <p className="text-sm text-gray-600">People Profiles</p>
                    </Card>
                    
                    <Card className="text-center">
                      <i className="pi pi-map text-2xl text-primary mb-2"></i>
                      <h5>Geo-Located</h5>
                      <p className="text-sm text-gray-600">Places Visited</p>
                    </Card>
                  </div>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Main Content Views */}
      <div className="main-content">
        {activeView === 'stories' && (
          aiStatus.hasStoryGeneration ? (
            <StoryInterface
              memories={memories}
              selectedStory={selectedStory}
              onStoryGenerated={handleStoryCreation}
            />
          ) : (
            <DisabledFeature
              featureName="AI Story Generation"
              description="Transform your memories into beautiful narrative stories with multiple modes: chronological, thematic, people-centered, and place-centered storytelling."
              requiredProvider="OpenAI or Anthropic"
              icon="📖"
              aiStatus={aiStatus}
            >
              <div style={{ height: '400px', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center', color: '#6c757d' }}>
                  <i className="pi pi-book" style={{ fontSize: '48px', marginBottom: '16px' }}></i>
                  <p>Story Generation Interface</p>
                </div>
              </div>
            </DisabledFeature>
          )
        )}

        {activeView === 'galleries' && (
          aiStatus.hasSmartGalleries ? (
            <GalleryBrowser
              onGallerySelect={handleGallerySelection}
              onCreateStory={handleStoryCreation}
            />
          ) : (
            <DisabledFeature
              featureName="Smart Galleries"
              description="Create AI-curated photo collections using natural language. Ask for 'creative moments', 'travel adventures', or any theme and watch AI organize your memories."
              requiredProvider="Any AI provider (OpenAI, Anthropic, or Google AI)"
              icon="🎨"
              aiStatus={aiStatus}
            >
              <div style={{ height: '400px', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center', color: '#6c757d' }}>
                  <i className="pi pi-images" style={{ fontSize: '48px', marginBottom: '16px' }}></i>
                  <p>Smart Gallery Browser</p>
                </div>
              </div>
            </DisabledFeature>
          )
        )}

        {activeView === 'people' && (
          aiStatus.hasPeopleIntelligence ? (
            <PeopleDashboard
              onPersonSelect={handlePersonSelection}
              onCreateStory={handleStoryCreation}
            />
          ) : (
            <DisabledFeature
              featureName="People Intelligence"
              description="Automatically detect people in your photos, analyze relationships, track interaction evolution over time, and generate 'best of us' compilations."
              requiredProvider="OpenAI or Google AI (for vision capabilities)"
              icon="👥"
              aiStatus={aiStatus}
            >
              <div style={{ height: '400px', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center', color: '#6c757d' }}>
                  <i className="pi pi-users" style={{ fontSize: '48px', marginBottom: '16px' }}></i>
                  <p>People Intelligence Dashboard</p>
                </div>
              </div>
            </DisabledFeature>
          )
        )}

        {activeView === 'map' && (
          <div className="map-view">
            <Card title="Narrative-Enhanced Places" className="mb-3">
              <p className="text-gray-600 mb-3">
                Explore the places in your life with rich narrative context and emotional connections
              </p>
              {memories.filter(m => m.location).length > 0 ? (
                <EnhancedMapComponent
                  memories={memories.filter(m => m.location)}
                  onLocationSelect={(location) => {
                    console.log('Location selected:', location);
                  }}
                />
              ) : (
                <GoogleMapComponent
                  geo={memories.filter(m => m.location)}
                  height="60vh"
                  width="100%"
                />
              )}
            </Card>
          </div>
        )}

        {activeView === 'enhanced_qa' && (
          aiStatus.hasSemanticSearch ? (
            <Card title="Enhanced Q&A Results" className="mb-3">
              {renderEnhancedQAResults()}
            </Card>
          ) : (
            <DisabledFeature
              featureName="Enhanced Q&A Results"
              description="View detailed AI-powered analysis of your queries with narrative answers, related memories, and contextual insights."
              requiredProvider="Any AI provider"
              icon="💬"
              aiStatus={aiStatus}
            >
              <div style={{ height: '300px', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center', color: '#6c757d' }}>
                  <i className="pi pi-comments" style={{ fontSize: '48px', marginBottom: '16px' }}></i>
                  <p>Enhanced Q&A Results</p>
                </div>
              </div>
            </DisabledFeature>
          )
        )}

        {activeView === 'facebook' && (
          <div className="facebook-timeline-view">
            <Card title="Facebook Posts Timeline" className="mb-3">
              <p className="text-gray-600 mb-3">
                Visualize your Facebook posting activity over time with an interactive timeline chart
              </p>
              <FacebookTimeline />
            </Card>
          </div>
        )}
      </div>

      {/* Footer with AI Status */}
      <Divider className="my-4" />
      <div className="app-footer text-center">
        <p className="text-sm text-gray-600">
          AI-Augmented Personal Archive • Privacy-First • Locally Processed
        </p>
        <div className="flex justify-content-center gap-2 mt-2">
          {Object.entries(aiServices).map(([service, status]) => (
            <i
              key={service}
              className={`pi ${status ? 'pi-check-circle text-green-500' : 'pi-times-circle text-red-500'}`}
              title={`${service}: ${status ? 'Active' : 'Inactive'}`}
            />
          ))}
        </div>
      </div>
      
      {/* AI Status Badge */}
      <AIStatusBadge aiStatus={aiStatus} />
    </div>
  );
}

export default EnhancedApp;