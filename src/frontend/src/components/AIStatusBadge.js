import React, { useState, useEffect } from 'react';
import './AIStatusBadge.css';

const AIStatusBadge = ({ aiStatus: externalAiStatus }) => {
  const [status, setStatus] = useState({
    ai_status: 'loading',
    ai_message: 'Checking AI services...',
    status_color: 'gray',
    available_providers: [],
    features: {}
  });
  const [showDetails, setShowDetails] = useState(false);
  const [lastCheck, setLastCheck] = useState(null);

  // Use external AI status if provided, otherwise fetch our own
  useEffect(() => {
    if (externalAiStatus && !externalAiStatus.loading) {
      setStatus(externalAiStatus);
      setLastCheck(new Date());
    } else if (!externalAiStatus) {
      checkAIStatus();
      const interval = setInterval(checkAIStatus, 30000);
      return () => clearInterval(interval);
    }
  }, [externalAiStatus]);

  const checkAIStatus = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_AI_SERVICES_URL || 'http://localhost:8086'}/status`);
      if (response.ok) {
        const statusData = await response.json();
        setStatus(statusData);
        setLastCheck(new Date());
      } else {
        setStatus({
          ai_status: 'error',
          ai_message: 'AI services unavailable',
          status_color: 'red',
          available_providers: [],
          features: {}
        });
      }
    } catch (error) {
      console.warn('AI status check failed:', error);
      setStatus({
        ai_status: 'error',
        ai_message: 'Cannot connect to AI services',
        status_color: 'red',
        available_providers: [],
        features: {}
      });
    }
  };

  useEffect(() => {
    if (externalAiStatus && !externalAiStatus.loading) {
      setStatus(externalAiStatus);
      setLastCheck(new Date());
    } else if (!externalAiStatus) {
      checkAIStatus();
      const interval = setInterval(checkAIStatus, 30000);
      return () => clearInterval(interval);
    }
  }, [externalAiStatus]);

  const getStatusIcon = () => {
    switch (status.ai_status) {
      case 'full':
        return '🟢';
      case 'partial':
        return '🟡';
      case 'unavailable':
        return '🔴';
      case 'error':
        return '⚠️';
      default:
        return '⏳';
    }
  };

  const getStatusText = () => {
    switch (status.ai_status) {
      case 'full':
        return 'AI Features Active';
      case 'partial':
        return 'Limited AI Features';
      case 'unavailable':
        return 'AI Features Unavailable';
      case 'error':
        return 'AI Services Error';
      default:
        return 'Checking AI Status...';
    }
  };

  const getSetupInstructions = () => {
    if (status.ai_status === 'unavailable' || status.ai_status === 'error') {
      return (
        <div className="setup-instructions">
          <h4>🔧 AI Service Status</h4>
          
          {status.detailed_message && (
            <div className="status-details">
              <strong>Details:</strong> {status.detailed_message}
            </div>
          )}
          
          {status.provider_details && (
            <div className="provider-status">
              <strong>Provider Status:</strong>
              {Object.entries(status.provider_details).map(([name, details]) => (
                <div key={name} className="provider-item">
                  <span className="provider-name">{name.toUpperCase()}:</span>
                  <span className={`provider-status ${details.status}`}>
                    {details.has_key ? (
                      details.status === 'working' ? '✅ Working' :
                      details.status === 'failing' ? '❌ Failing' :
                      details.status === 'error' ? `⚠️ Error: ${details.error}` :
                      '🔧 Configured'
                    ) : '❌ No API Key'}
                  </span>
                </div>
              ))}
            </div>
          )}
          
          {status.recommendations && status.recommendations.length > 0 && (
            <div className="recommendations">
              <strong>Recommendations:</strong>
              <ul>
                {status.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="api-links">
            <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">
              Get OpenAI Key
            </a>
            <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer">
              Get Anthropic Key
            </a>
            <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer">
              Get Google Key
            </a>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`ai-status-badge ${status.status_color}`}>
      <div 
        className="status-header"
        onClick={() => setShowDetails(!showDetails)}
        style={{ cursor: 'pointer' }}
      >
        <span className="status-icon">{getStatusIcon()}</span>
        <span className="status-text">{getStatusText()}</span>
        <span className="toggle-icon">{showDetails ? '▼' : '▶'}</span>
      </div>
      
      {showDetails && (
        <div className="status-details">
          <div className="status-message">{status.ai_message}</div>
          
          {status.available_providers.length > 0 && (
            <div className="providers-section">
              <strong>Active Providers:</strong>
              <div className="provider-list">
                {status.available_providers.map(provider => (
                  <span key={provider} className="provider-tag">
                    {provider.charAt(0).toUpperCase() + provider.slice(1)}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className="features-section">
            <strong>AI Features:</strong>
            <div className="feature-list">
              <div className={`feature ${status.features.story_generation ? 'enabled' : 'disabled'}`}>
                📖 Story Generation {status.features.story_generation ? '✓' : '✗'}
              </div>
              <div className={`feature ${status.features.people_intelligence ? 'enabled' : 'disabled'}`}>
                👥 People Intelligence {status.features.people_intelligence ? '✓' : '✗'}
              </div>
              <div className={`feature ${status.features.smart_galleries ? 'enabled' : 'disabled'}`}>
                🎨 Smart Galleries {status.features.smart_galleries ? '✓' : '✗'}
              </div>
              <div className={`feature ${status.features.semantic_search ? 'enabled' : 'disabled'}`}>
                🔍 Semantic Search {status.features.semantic_search ? '✓' : '✗'}
              </div>
            </div>
          </div>
          
          {getSetupInstructions()}
          
          {lastCheck && (
            <div className="last-check">
              Last checked: {lastCheck.toLocaleTimeString()}
            </div>
          )}
          
          <div className="status-actions">
            <button onClick={checkAIStatus} className="refresh-btn">
              🔄 Refresh Status
            </button>
            <a 
              href={`${process.env.REACT_APP_AI_SERVICES_URL || 'http://localhost:8086'}/health`}
              target="_blank" 
              rel="noopener noreferrer"
              className="health-link"
            >
              📊 Detailed Health
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIStatusBadge;