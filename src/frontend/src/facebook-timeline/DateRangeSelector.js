import React from 'react';

const DateRangeSelector = ({ dateRange, onDateRangeChange, granularity, onGranularityChange }) => {
  const handleStartDateChange = (e) => {
    onDateRangeChange({
      ...dateRange,
      start: e.target.value || null
    });
  };

  const handleEndDateChange = (e) => {
    onDateRangeChange({
      ...dateRange,
      end: e.target.value || null
    });
  };

  const handleGranularityChange = (e) => {
    onGranularityChange(e.target.value);
  };

  const clearDateRange = () => {
    onDateRangeChange({ start: null, end: null });
  };

  const setPresetRange = (preset) => {
    const end = new Date();
    const start = new Date();
    
    switch (preset) {
      case 'last7days':
        start.setDate(end.getDate() - 7);
        break;
      case 'last30days':
        start.setDate(end.getDate() - 30);
        break;
      case 'last90days':
        start.setDate(end.getDate() - 90);
        break;
      case 'lastyear':
        start.setFullYear(end.getFullYear() - 1);
        break;
      default:
        return;
    }
    
    onDateRangeChange({
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    });
  };

  return (
    <div className="date-range-selector">
      <div className="date-inputs">
        <div className="date-input-group">
          <label htmlFor="start-date">Start Date:</label>
          <input
            id="start-date"
            type="date"
            value={dateRange.start || ''}
            onChange={handleStartDateChange}
            className="date-input"
          />
        </div>
        
        <div className="date-input-group">
          <label htmlFor="end-date">End Date:</label>
          <input
            id="end-date"
            type="date"
            value={dateRange.end || ''}
            onChange={handleEndDateChange}
            className="date-input"
          />
        </div>
        
        <button onClick={clearDateRange} className="clear-button">
          Clear
        </button>
      </div>

      <div className="preset-buttons">
        <span className="preset-label">Quick Select:</span>
        <button onClick={() => setPresetRange('last7days')} className="preset-button">
          Last 7 Days
        </button>
        <button onClick={() => setPresetRange('last30days')} className="preset-button">
          Last 30 Days
        </button>
        <button onClick={() => setPresetRange('last90days')} className="preset-button">
          Last 90 Days
        </button>
        <button onClick={() => setPresetRange('lastyear')} className="preset-button">
          Last Year
        </button>
      </div>

      <div className="granularity-selector">
        <label htmlFor="granularity">View by:</label>
        <select
          id="granularity"
          value={granularity}
          onChange={handleGranularityChange}
          className="granularity-select"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
      </div>
    </div>
  );
};

export default DateRangeSelector;