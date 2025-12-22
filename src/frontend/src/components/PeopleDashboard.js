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
import { Image } from 'primereact/image';
import { Chip } from 'primereact/chip';
import { Timeline } from 'primereact/timeline';
import { Dialog } from 'primereact/dialog';
import { InputText } from 'primereact/inputtext';
import { Dropdown } from 'primereact/dropdown';
import { Chart } from 'primereact/chart';
import { config } from '../Constants';

const PeopleDashboard = ({ onPersonSelect, onCreateStory }) => {
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [showPersonDialog, setShowPersonDialog] = useState(false);
  const [interactionData, setInteractionData] = useState({});
  const [relationshipEvolution, setRelationshipEvolution] = useState([]);
  const [bestOfUsCompilation, setBestOfUsCompilation] = useState(null);
  const [personControls, setPersonControls] = useState({});

  useEffect(() => {
    loadPeople();
  }, []);

  const loadPeople = async () => {
    try {
      const response = await fetch(`${config.API_URL}/api/people`);
      const data = await response.json();
      setPeople(data.people || []);
    } catch (error) {
      console.error('Error loading people:', error);
    }
  };

  const loadPersonDetails = async (personId) => {
    try {
      const [profileResponse, interactionResponse, evolutionResponse] = await Promise.all([
        fetch(`${config.API_URL}/api/people/${personId}/profile`),
        fetch(`${config.API_URL}/api/people/${personId}/interactions`),
        fetch(`${config.API_URL}/api/people/${personId}/evolution`)
      ]);

      const profile = await profileResponse.json();
      const interactions = await interactionResponse.json();
      const evolution = await evolutionResponse.json();

      setSelectedPerson(profile);
      setInteractionData(interactions);
      setRelationshipEvolution(evolution.phases || []);
    } catch (error) {
      console.error('Error loading person details:', error);
    }
  };

  const generateBestOfUs = async (personId) => {
    try {
      const response = await fetch(`${config.API_URL}/api/people/${personId}/best-of-us`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const compilation = await response.json();
      setBestOfUsCompilation(compilation);
    } catch (error) {
      console.error('Error generating best of us compilation:', error);
    }
  };

  const updatePersonControls = async (personId, controls) => {
    try {
      const response = await fetch(`${config.API_URL}/api/people/${personId}/controls`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(controls)
      });
      
      const updatedControls = await response.json();
      setPersonControls(prev => ({
        ...prev,
        [personId]: updatedControls
      }));
    } catch (error) {
      console.error('Error updating person controls:', error);
    }
  };

  const renderPersonCard = (person) => {
    const representativePhoto = person.representative_photos?.[0];
    const interactionCount = person.interaction_count || 0;
    const lastSeen = person.last_appearance ? new Date(person.last_appearance).toLocaleDateString() : 'Unknown';
    
    return (
      <Card 
        key={person.id}
        className="person-card cursor-pointer hover:shadow-3 mb-3"
        onClick={() => {
          loadPersonDetails(person.id);
          setShowPersonDialog(true);
          if (onPersonSelect) {
            onPersonSelect(person);
          }
        }}
      >
        <div className="person-preview flex align-items-center">
          <div className="person-photo mr-3">
            {representativePhoto ? (
              <Image
                src={representativePhoto}
                alt={person.name}
                width="80"
                height="80"
                className="border-circle"
                style={{ objectFit: 'cover' }}
              />
            ) : (
              <div 
                className="person-avatar border-circle flex align-items-center justify-content-center"
                style={{ 
                  width: '80px', 
                  height: '80px', 
                  backgroundColor: '#e3f2fd',
                  fontSize: '2rem',
                  color: '#1976d2'
                }}
              >
                {person.name.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          
          <div className="person-info flex-1">
            <h4 className="mb-2">{person.name}</h4>
            
            <div className="person-stats mb-2">
              <Chip 
                label={`${interactionCount} interactions`} 
                className="mr-2 mb-1"
              />
              <Chip 
                label={`Last seen: ${lastSeen}`} 
                className="p-chip-outlined mb-1"
              />
            </div>
            
            {person.shared_contexts && (
              <div className="shared-contexts">
                <span className="text-sm text-gray-600">
                  Often together: {person.shared_contexts.slice(0, 3).join(', ')}
                </span>
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  };

  const renderInteractionChart = () => {
    if (!interactionData.timeline) return null;
    
    const chartData = {
      labels: interactionData.timeline.map(point => point.period),
      datasets: [{
        label: 'Interactions',
        data: interactionData.timeline.map(point => point.count),
        borderColor: '#42A5F5',
        backgroundColor: 'rgba(66, 165, 245, 0.2)',
        tension: 0.4
      }]
    };

    const chartOptions = {
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    };

    return (
      <div className="interaction-chart mb-4">
        <h5>Interaction Timeline</h5>
        <Chart type="line" data={chartData} options={chartOptions} />
      </div>
    );
  };

  const renderRelationshipEvolution = () => {
    if (!relationshipEvolution.length) return null;
    
    const events = relationshipEvolution.map(phase => ({
      status: phase.phase_name,
      date: new Date(phase.start_date).toLocaleDateString(),
      icon: 'pi pi-circle',
      color: phase.emotional_tone === 'positive' ? '#4CAF50' : 
             phase.emotional_tone === 'negative' ? '#F44336' : '#FF9800',
      description: phase.description
    }));

    return (
      <div className="relationship-evolution mb-4">
        <h5>Relationship Evolution</h5>
        <Timeline 
          value={events} 
          align="alternate" 
          className="customized-timeline"
          content={(item) => (
            <Card className="mb-2">
              <h6>{item.status}</h6>
              <p className="text-sm text-gray-600 mb-1">{item.date}</p>
              <p className="text-sm">{item.description}</p>
            </Card>
          )}
        />
      </div>
    );
  };

  const renderPersonDialog = () => {
    if (!selectedPerson) return null;
    
    return (
      <Dialog
        header={selectedPerson.name}
        visible={showPersonDialog}
        onHide={() => setShowPersonDialog(false)}
        style={{ width: '80vw', maxWidth: '1000px' }}
        maximizable
      >
        <div className="person-detail">
          <div className="person-header flex align-items-center mb-4">
            {selectedPerson.representative_photos?.[0] && (
              <Image
                src={selectedPerson.representative_photos[0]}
                alt={selectedPerson.name}
                width="120"
                height="120"
                className="border-circle mr-4"
                style={{ objectFit: 'cover' }}
              />
            )}
            
            <div className="person-summary">
              <h3>{selectedPerson.name}</h3>
              <div className="person-dates mb-2">
                <p className="text-sm text-gray-600">
                  First appeared: {new Date(selectedPerson.first_appearance).toLocaleDateString()}
                </p>
                <p className="text-sm text-gray-600">
                  Last seen: {new Date(selectedPerson.last_appearance).toLocaleDateString()}
                </p>
              </div>
              
              <div className="person-actions">
                <Button
                  label="Generate 'Best of Us'"
                  icon="pi pi-heart"
                  onClick={() => generateBestOfUs(selectedPerson.id)}
                  className="p-button-primary mr-2"
                />
                <Button
                  label="Create Story"
                  icon="pi pi-book"
                  onClick={() => {
                    if (onCreateStory) {
                      onCreateStory({ person: selectedPerson });
                    }
                  }}
                  className="p-button-outlined"
                />
              </div>
            </div>
          </div>
          
          {renderInteractionChart()}
          {renderRelationshipEvolution()}
          
          {bestOfUsCompilation && (
            <div className="best-of-us mb-4">
              <h5>Best of Us Compilation</h5>
              <Card>
                <p>{bestOfUsCompilation.summary}</p>
                <div className="compilation-photos grid mt-3">
                  {bestOfUsCompilation.photos?.map((photo, index) => (
                    <div key={index} className="col-6 md:col-4 lg:col-3">
                      <Image
                        src={photo.url}
                        alt={photo.caption}
                        width="100%"
                        height="150"
                        className="compilation-photo"
                        preview
                      />
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
          
          <div className="person-controls">
            <h5>Privacy Controls</h5>
            <Card>
              <div className="control-options">
                <div className="field">
                  <label htmlFor="display-name">Display Name</label>
                  <InputText
                    id="display-name"
                    value={selectedPerson.name}
                    onChange={(e) => {
                      setSelectedPerson(prev => ({
                        ...prev,
                        name: e.target.value
                      }));
                    }}
                    className="w-full"
                  />
                </div>
                
                <div className="field">
                  <label htmlFor="visibility">Visibility</label>
                  <Dropdown
                    id="visibility"
                    value={personControls[selectedPerson.id]?.visibility || 'visible'}
                    options={[
                      { label: 'Visible', value: 'visible' },
                      { label: 'Hidden', value: 'hidden' },
                      { label: 'Excluded', value: 'excluded' }
                    ]}
                    onChange={(e) => {
                      updatePersonControls(selectedPerson.id, {
                        ...personControls[selectedPerson.id],
                        visibility: e.value
                      });
                    }}
                    className="w-full"
                  />
                </div>
                
                <Button
                  label="Save Changes"
                  icon="pi pi-save"
                  onClick={() => {
                    updatePersonControls(selectedPerson.id, {
                      name: selectedPerson.name,
                      visibility: personControls[selectedPerson.id]?.visibility || 'visible'
                    });
                  }}
                  className="p-button-primary mt-2"
                />
              </div>
            </Card>
          </div>
        </div>
      </Dialog>
    );
  };

  return (
    <div className="people-dashboard">
      <div className="dashboard-header mb-4">
        <h2>People in Your Life</h2>
        <p className="text-gray-600">
          Explore the relationships and shared experiences with people who matter to you
        </p>
      </div>

      <div className="people-grid">
        <div className="grid">
          {people.map(person => (
            <div key={person.id} className="col-12 md:col-6 lg:col-4">
              {renderPersonCard(person)}
            </div>
          ))}
        </div>
        
        {people.length === 0 && (
          <Card className="text-center p-4">
            <i className="pi pi-users text-6xl text-gray-400 mb-3"></i>
            <h4>No people profiles yet</h4>
            <p className="text-gray-600">
              People profiles will be automatically generated from your personal data
            </p>
          </Card>
        )}
      </div>

      {renderPersonDialog()}
    </div>
  );
};

export default PeopleDashboard;