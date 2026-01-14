# Facebook Posts Timeline

An interactive timeline visualization for Facebook posts data, built with React and Chart.js.

## Features

- **Interactive Timeline Chart**: Bar chart showing post volume over time with clickable dates
- **Post Detail Panel**: View posts for selected dates with content, media, and metadata
- **Date Range Filtering**: Filter timeline by custom date ranges or quick presets
- **Media Gallery**: Full-screen media viewer with navigation
- **Statistics Display**: Overview of posting activity and engagement metrics
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Components

### FacebookTimeline
Main container component that orchestrates all timeline functionality.

### TimelineChart
Chart.js-powered bar chart showing post counts over time with interactive date selection.

### PostDetailPanel
Displays posts for a selected date with content, media thumbnails, reactions, and metadata.

### DateRangeSelector
Date range picker with preset options (last 7 days, 30 days, etc.) and granularity controls.

### MediaGallery
Full-screen media viewer with keyboard navigation and thumbnail gallery.

## API Integration

The components integrate with the Facebook Posts Timeline API endpoints:

- `GET /facebook/timeline` - Timeline data with date filtering
- `GET /facebook/posts` - Posts for specific dates
- `POST /facebook/process` - Process Facebook export data
- `GET /facebook/stats` - Timeline statistics

## Usage

```jsx
import FacebookTimeline from './facebook-timeline/FacebookTimeline';

function App() {
  return (
    <div>
      <FacebookTimeline />
    </div>
  );
}
```

## Dependencies

- React 18+
- Chart.js 4+
- react-chartjs-2 5+

## Data Processing

The timeline processes Facebook export data from `posts.json` files, extracting:

- Post content and timestamps
- Media attachments (photos/videos)
- Reactions and engagement metrics
- Location and tagged people data
- Post type classification (status, photo, video, link)

## Styling

The components use CSS modules with a Facebook-inspired design system featuring:

- Facebook blue color scheme (#4267B2)
- Clean, modern interface
- Responsive grid layouts
- Smooth animations and transitions