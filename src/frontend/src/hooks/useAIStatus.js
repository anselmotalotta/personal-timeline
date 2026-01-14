import { useState, useEffect } from 'react';

const useAIStatus = () => {
  const [aiStatus, setAiStatus] = useState({
    ai_status: 'loading',
    ai_message: 'Checking AI services...',
    status_color: 'gray',
    available_providers: [],
    features: {
      story_generation: false,
      people_intelligence: false,
      smart_galleries: false,
      semantic_search: false
    },
    loading: true
  });

  const checkAIStatus = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_AI_SERVICES_URL || 'http://localhost:8086'}/status`);
      if (response.ok) {
        const statusData = await response.json();
        setAiStatus({
          ...statusData,
          loading: false
        });
      } else {
        setAiStatus({
          ai_status: 'error',
          ai_message: 'AI services unavailable',
          status_color: 'red',
          available_providers: [],
          features: {
            story_generation: false,
            people_intelligence: false,
            smart_galleries: false,
            semantic_search: false
          },
          loading: false
        });
      }
    } catch (error) {
      console.warn('AI status check failed:', error);
      setAiStatus({
        ai_status: 'unavailable',
        ai_message: 'Cannot connect to AI services - features disabled',
        status_color: 'red',
        available_providers: [],
        features: {
          story_generation: false,
          people_intelligence: false,
          smart_galleries: false,
          semantic_search: false
        },
        loading: false
      });
    }
  };

  useEffect(() => {
    checkAIStatus();
    // Check status every 30 seconds
    const interval = setInterval(checkAIStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    ...aiStatus,
    refreshStatus: checkAIStatus,
    isAIAvailable: aiStatus.ai_status === 'full' || aiStatus.ai_status === 'partial',
    hasSemanticSearch: aiStatus.features.semantic_search,
    hasStoryGeneration: aiStatus.features.story_generation,
    hasPeopleIntelligence: aiStatus.features.people_intelligence,
    hasSmartGalleries: aiStatus.features.smart_galleries
  };
};

export default useAIStatus;