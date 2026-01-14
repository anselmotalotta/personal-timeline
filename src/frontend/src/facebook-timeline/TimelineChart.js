import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const TimelineChart = ({ data, onDateClick, selectedDate, loading, granularity, onGranularityChange }) => {
  const chartRef = useRef();

  // Auto-adjust granularity based on data density
  useEffect(() => {
    if (data && data.length > 0 && onGranularityChange) {
      const dateRange = new Date(data[data.length - 1].date) - new Date(data[0].date);
      const daysDiff = dateRange / (1000 * 60 * 60 * 24);
      
      // Auto-adjust granularity for better visualization
      if (daysDiff > 730 && granularity === 'daily') { // > 2 years
        onGranularityChange('monthly');
      } else if (daysDiff > 180 && granularity === 'daily') { // > 6 months
        onGranularityChange('weekly');
      }
    }
  }, [data, granularity, onGranularityChange]);

  // Aggregate data based on granularity
  const aggregateData = (rawData, granularity) => {
    if (!rawData || rawData.length === 0) return [];
    
    const aggregated = {};
    
    rawData.forEach(item => {
      const date = new Date(item.date);
      let key;
      
      switch (granularity) {
        case 'monthly':
          key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          break;
        case 'weekly':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = weekStart.toISOString().split('T')[0];
          break;
        case 'daily':
        default:
          key = item.date;
          break;
      }
      
      if (!aggregated[key]) {
        aggregated[key] = {
          date: key,
          post_count: 0,
          has_media_count: 0,
          original_dates: []
        };
      }
      
      aggregated[key].post_count += item.post_count;
      aggregated[key].has_media_count += item.has_media_count;
      aggregated[key].original_dates.push(item.date);
    });
    
    return Object.values(aggregated).sort((a, b) => new Date(a.date) - new Date(b.date));
  };

  const processedData = aggregateData(data, granularity);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    switch (granularity) {
      case 'monthly':
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
      case 'weekly':
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        return `Week of ${weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
      case 'daily':
      default:
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
  };

  const chartData = {
    labels: processedData.map(item => formatDate(item.date)),
    datasets: [
      {
        label: 'Posts',
        data: processedData.map(item => item.post_count),
        backgroundColor: processedData.map(item => 
          item.date === selectedDate ? '#4267B2' : '#8b9dc3'
        ),
        borderColor: processedData.map(item => 
          item.date === selectedDate ? '#365899' : '#6b7c95'
        ),
        borderWidth: 1,
        hoverBackgroundColor: '#4267B2',
        hoverBorderColor: '#365899',
      },
      {
        label: 'Posts with Media',
        data: processedData.map(item => item.has_media_count),
        backgroundColor: processedData.map(item => 
          item.date === selectedDate ? '#42b883' : '#95d5b2'
        ),
        borderColor: processedData.map(item => 
          item.date === selectedDate ? '#369870' : '#74c69d'
        ),
        borderWidth: 1,
        hoverBackgroundColor: '#42b883',
        hoverBorderColor: '#369870',
      }
    ],
  };

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `Facebook Posts Over Time (${granularity})`,
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const dataIndex = context[0].dataIndex;
            const originalDate = processedData[dataIndex]?.date;
            if (originalDate) {
              return new Date(originalDate).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              });
            }
            return context[0].label;
          },
          afterBody: (context) => {
            const dataIndex = context[0].dataIndex;
            const item = processedData[dataIndex];
            if (item) {
              const info = [
                `Total Posts: ${item.post_count}`,
                `Posts with Media: ${item.has_media_count}`,
              ];
              
              if (granularity !== 'daily' && item.original_dates) {
                info.push(`Covers ${item.original_dates.length} day(s)`);
              }
              
              info.push('Click to view posts');
              return info;
            }
            return [];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Posts'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const dataIndex = elements[0].index;
        const clickedItem = processedData[dataIndex];
        if (clickedItem && onDateClick) {
          // For aggregated data, use the first original date or the aggregated date
          const dateToUse = clickedItem.original_dates && clickedItem.original_dates.length > 0 
            ? clickedItem.original_dates[0] 
            : clickedItem.date;
          onDateClick(dateToUse, clickedItem);
        }
      }
    },
    onHover: (event, elements) => {
      event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
    }
  };

  // Add zoom plugin configuration if available
  // Temporarily disabled zoom functionality
  const options = baseOptions;

  const resetZoom = () => {
    // Zoom functionality temporarily disabled
    console.log('Reset zoom clicked');
  };

  if (loading) {
    return (
      <div className="timeline-chart-loading">
        <div className="loading-spinner"></div>
        <p>Loading timeline data...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="timeline-chart-empty">
        <p>No timeline data available for the selected date range</p>
        <p>Try expanding your date range or processing your Facebook data</p>
      </div>
    );
  }

  return (
    <div className="timeline-chart">
      <div className="chart-controls">
        <button onClick={resetZoom} className="reset-zoom-btn" style={{display: 'none'}}>
          Reset Zoom
        </button>
        <span className="chart-info">
          Showing {processedData.length} {granularity} periods | Click bars to view posts
        </span>
      </div>
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        <Bar ref={chartRef} data={chartData} options={options} />
      </div>
      <div className="chart-instructions">
        <p>Click on any bar to view posts</p>
      </div>
    </div>
  );
};

export default TimelineChart;