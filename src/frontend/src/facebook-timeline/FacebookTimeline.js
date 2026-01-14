import React, { useState, useEffect } from 'react';
import TimelineChart from './TimelineChart';
import PostDetailPanel from './PostDetailPanel';
import DateRangeSelector from './DateRangeSelector';
import MediaGallery from './MediaGallery';
import { config } from '../Constants';
import './FacebookTimeline.css';

const FacebookTimeline = () => {
  const [timelineData, setTimelineData] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedPosts, setSelectedPosts] = useState([]);
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [granularity, setGranularity] = useState('daily');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({
    showWithMedia: true,
    showWithoutMedia: true,
    showComments: true,
    showPosts: true,
    showEmptyPosts: false
  });

  // Load timeline data on component mount and when filters change
  useEffect(() => {
    loadTimelineData();
  }, [dateRange, granularity]);

  // Set intelligent default date range
  useEffect(() => {
    if (timelineData.length > 0 && !dateRange.start && !dateRange.end) {
      const dates = timelineData.map(item => new Date(item.date));
      const minDate = new Date(Math.min(...dates));
      const maxDate = new Date(Math.max(...dates));
      
      // For large date ranges, default to last 2 years
      const twoYearsAgo = new Date();
      twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
      
      const startDate = minDate > twoYearsAgo ? minDate : twoYearsAgo;
      
      setDateRange({
        start: startDate.toISOString().split('T')[0],
        end: maxDate.toISOString().split('T')[0]
      });
    }
  }, [timelineData]);

  const loadTimelineData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);
      
      const response = await fetch(`${config.API_URL}/facebook/timeline?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setTimelineData(data.timeline || []);
      
      // Load stats
      const statsResponse = await fetch(`${config.API_URL}/facebook/stats`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData.statistics);
      }
    } catch (err) {
      console.error('Failed to load timeline data:', err);
      setError('Failed to load timeline data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDateClick = async (date, aggregatedItem = null) => {
    setSelectedDate(date);
    setLoading(true);
    
    try {
      let allPosts = [];
      
      // If this is an aggregated item, get posts for all dates in the aggregation
      if (aggregatedItem && aggregatedItem.original_dates) {
        for (const originalDate of aggregatedItem.original_dates) {
          const response = await fetch(`${config.API_URL}/facebook/posts?date=${originalDate}`);
          if (response.ok) {
            const data = await response.json();
            allPosts = allPosts.concat(data.posts || []);
          }
        }
      } else {
        const response = await fetch(`${config.API_URL}/facebook/posts?date=${date}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        allPosts = data.posts || [];
      }
      
      // Apply filters and enhancements
      const filteredPosts = allPosts.filter(post => {
        // Filter empty posts
        if (!filters.showEmptyPosts && (!post.content || post.content.trim() === '')) {
          return false;
        }
        
        // Filter by media presence
        const hasMedia = post.media_files && post.media_files.length > 0;
        if (hasMedia && !filters.showWithMedia) return false;
        if (!hasMedia && !filters.showWithoutMedia) return false;
        
        // Filter by post type (comments vs posts)
        const isComment = post.post_type === 'comment' || 
                         (post.content && post.content.includes('commented on'));
        if (isComment && !filters.showComments) return false;
        if (!isComment && !filters.showPosts) return false;
        
        return true;
      }).map(post => ({
        ...post,
        // Enhance post classification
        isComment: post.post_type === 'comment' || 
                  (post.content && post.content.includes('commented on')),
        isEmpty: !post.content || post.content.trim() === '',
        hasMedia: post.media_files && post.media_files.length > 0,
        // Fix media paths
        media_files: (post.media_files || []).map(media => ({
          ...media,
          // Ensure media paths are accessible
          url: media.url || media.uri || media.path
        }))
      }));
      
      setSelectedPosts(filteredPosts);
    } catch (err) {
      console.error('Failed to load posts for date:', err);
      setError('Failed to load posts for selected date.');
      setSelectedPosts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDateRangeChange = (newRange) => {
    setDateRange(newRange);
    setSelectedDate(null);
    setSelectedPosts([]);
  };

  const handleGranularityChange = (newGranularity) => {
    setGranularity(newGranularity);
    setSelectedDate(null);
    setSelectedPosts([]);
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
    
    // Re-apply filters to currently selected posts if any
    if (selectedPosts.length > 0) {
      handleDateClick(selectedDate);
    }
  };

  const handleMediaClick = (mediaItem, allMedia) => {
    setSelectedMedia({ item: mediaItem, gallery: allMedia });
  };

  const handleCloseMedia = () => {
    setSelectedMedia(null);
  };

  const processData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${config.API_URL}/facebook/process`, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.status === 'success') {
        // Reload timeline data after processing
        await loadTimelineData();
        alert(`Processing completed! Processed ${result.processing_result.processed_posts} posts.`);
      } else {
        throw new Error('Processing failed');
      }
    } catch (err) {
      console.error('Failed to process Facebook data:', err);
      setError('Failed to process Facebook data. Please check your export files.');
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="facebook-timeline-error">
        <h2>Facebook Posts Timeline</h2>
        <div className="error-message">
          <p>{error}</p>
          <button onClick={loadTimelineData} className="retry-button">
            Retry
          </button>
          <button onClick={processData} className="process-button">
            Process Facebook Data
          </button>
        </div>
      </div>
    );
  }

  if (timelineData.length === 0 && !loading) {
    return (
      <div className="facebook-timeline-empty">
        <h2>Facebook Posts Timeline</h2>
        <div className="empty-state">
          <p>No Facebook posts found. Process your Facebook export data to get started.</p>
          <button onClick={processData} className="process-button">
            Process Facebook Data
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="facebook-timeline">
      <div className="timeline-header">
        <h2>Facebook Posts Timeline</h2>
        {stats && (
          <div className="timeline-stats">
            <span>Total Posts: {stats.total_posts || stats.post_count || 'N/A'}</span>
            <span>Posts with Media: {stats.media_count || 'N/A'}</span>
            <span>Total Reactions: {stats.reaction_count || 'N/A'}</span>
          </div>
        )}
      </div>

      <div className="timeline-controls">
        <DateRangeSelector
          dateRange={dateRange}
          onDateRangeChange={handleDateRangeChange}
          granularity={granularity}
          onGranularityChange={handleGranularityChange}
        />
        
        <div className="post-filters">
          <h4>Filters:</h4>
          <div className="filter-group">
            <label>
              <input
                type="checkbox"
                checked={filters.showWithMedia}
                onChange={(e) => handleFilterChange('showWithMedia', e.target.checked)}
              />
              Posts with Media
            </label>
            <label>
              <input
                type="checkbox"
                checked={filters.showWithoutMedia}
                onChange={(e) => handleFilterChange('showWithoutMedia', e.target.checked)}
              />
              Text-only Posts
            </label>
            <label>
              <input
                type="checkbox"
                checked={filters.showComments}
                onChange={(e) => handleFilterChange('showComments', e.target.checked)}
              />
              Comments
            </label>
            <label>
              <input
                type="checkbox"
                checked={filters.showPosts}
                onChange={(e) => handleFilterChange('showPosts', e.target.checked)}
              />
              Original Posts
            </label>
            <label>
              <input
                type="checkbox"
                checked={filters.showEmptyPosts}
                onChange={(e) => handleFilterChange('showEmptyPosts', e.target.checked)}
              />
              Empty Posts
            </label>
          </div>
        </div>
      </div>

      <div className="timeline-content">
        <div className="timeline-chart-container">
          <TimelineChart
            data={timelineData}
            onDateClick={handleDateClick}
            selectedDate={selectedDate}
            loading={loading}
            granularity={granularity}
            onGranularityChange={handleGranularityChange}
          />
        </div>

        {selectedDate && (
          <PostDetailPanel
            date={selectedDate}
            posts={selectedPosts}
            loading={loading}
            onMediaClick={handleMediaClick}
          />
        )}
      </div>

      {selectedMedia && (
        <MediaGallery
          mediaItem={selectedMedia.item}
          gallery={selectedMedia.gallery}
          onClose={handleCloseMedia}
        />
      )}
    </div>
  );
};

export default FacebookTimeline;