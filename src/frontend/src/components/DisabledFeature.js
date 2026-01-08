import React, { useState, useRef } from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { OverlayPanel } from 'primereact/overlaypanel';
import './DisabledFeature.css';

const DisabledFeature = ({ 
  featureName, 
  description, 
  requiredProvider = "any AI provider",
  icon = "🤖",
  children,
  aiStatus = null  // Pass AI status for detailed messaging
}) => {
  const [showInstructions, setShowInstructions] = useState(false);
  const instructionsRef = useRef(null);

  const toggleInstructions = (event) => {
    instructionsRef.current.toggle(event);
  };

  const getSpecificMessage = () => {
    if (aiStatus && aiStatus.detailed_message) {
      return aiStatus.detailed_message;
    }
    return `This feature requires ${requiredProvider} to be working properly.`;
  };

  const getRecommendations = () => {
    if (aiStatus && aiStatus.recommendations) {
      return aiStatus.recommendations;
    }
    return [
      "Get an API key from OpenAI, Anthropic, or Google",
      "Add it to your .env file",
      "Restart the application"
    ];
  };

  return (
    <div className="disabled-feature-overlay">
      {children && (
        <div className="disabled-feature-content">
          {children}
        </div>
      )}
      
      <div className="disabled-feature-banner">
        <Card className="disabled-feature-card">
          <div className="disabled-feature-header">
            <span className="feature-icon">{icon}</span>
            <h3>{featureName} Unavailable</h3>
          </div>
          
          <p className="feature-description">
            {description}
          </p>
          
          <div className="feature-requirements">
            <strong>Issue:</strong> {getSpecificMessage()}
          </div>
          
          <div className="feature-actions">
            <Button 
              label="Setup Instructions" 
              icon="pi pi-info-circle"
              className="p-button-primary"
              onClick={toggleInstructions}
            />
          </div>
          
          <OverlayPanel ref={instructionsRef} className="setup-instructions-panel">
            <div className="setup-instructions">
              <h4>🔧 Enable {featureName}</h4>
              
              {aiStatus && aiStatus.provider_details && (
                <div className="provider-status-section">
                  <strong>Current Provider Status:</strong>
                  {Object.entries(aiStatus.provider_details).map(([name, details]) => (
                    <div key={name} className="provider-status-item">
                      <span className="provider-name">{name.toUpperCase()}:</span>
                      <span className={`status ${details.status}`}>
                        {details.has_key ? (
                          details.status === 'working' ? '✅ Working' :
                          details.status === 'failing' ? '❌ Failing' :
                          details.status === 'error' ? `⚠️ ${details.error}` :
                          '🔧 Configured but not working'
                        ) : '❌ No API Key'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="setup-steps">
                <strong>Recommendations:</strong>
                <ul>
                  {getRecommendations().map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
              
              <div className="api-providers">
                <strong>Get API Keys:</strong>
                <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="provider-link">
                  🔗 OpenAI API Keys
                </a>
                <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="provider-link">
                  🔗 Anthropic Console
                </a>
                <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="provider-link">
                  🔗 Google AI Studio
                </a>
              </div>
            </div>
          </OverlayPanel>
          
          <div className="setup-hint">
            💡 Click "Setup Instructions" above for step-by-step guidance
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DisabledFeature;