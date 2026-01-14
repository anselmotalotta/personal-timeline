import React, { useState, useEffect } from 'react';

const MediaGallery = ({ mediaItem, gallery, onClose }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (mediaItem && gallery) {
      const index = gallery.findIndex(item => item === mediaItem);
      setCurrentIndex(index >= 0 ? index : 0);
    }
  }, [mediaItem, gallery]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          goToPrevious();
          break;
        case 'ArrowRight':
          goToNext();
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, gallery]);

  const goToNext = () => {
    if (gallery && currentIndex < gallery.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const goToPrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const goToIndex = (index) => {
    setCurrentIndex(index);
  };

  if (!gallery || gallery.length === 0) {
    return null;
  }

  const currentMedia = gallery[currentIndex];
  
  // Extract URL from media object or use as string
  const getMediaUrl = (media) => {
    if (!media) return '';
    if (typeof media === 'string') return media;
    return media.url || media.uri || media.path || '';
  };
  
  const currentMediaUrl = getMediaUrl(currentMedia);
  const isVideo = currentMediaUrl && (
    currentMediaUrl.toLowerCase().includes('.mp4') ||
    currentMediaUrl.toLowerCase().includes('.mov') ||
    currentMediaUrl.toLowerCase().includes('.avi')
  );

  return (
    <div className="media-gallery-overlay" onClick={onClose}>
      <div className="media-gallery" onClick={(e) => e.stopPropagation()}>
        <button className="gallery-close" onClick={onClose}>
          ✕
        </button>

        <div className="gallery-content">
          {gallery.length > 1 && (
            <button
              className="gallery-nav gallery-prev"
              onClick={goToPrevious}
              disabled={currentIndex === 0}
            >
              ‹
            </button>
          )}

          <div className="gallery-media">
            {isVideo ? (
              <video
                src={currentMediaUrl}
                controls
                autoPlay
                className="gallery-video"
                onError={(e) => {
                  console.error('Video failed to load:', currentMediaUrl);
                }}
              >
                Your browser does not support the video tag.
              </video>
            ) : (
              <img
                src={currentMediaUrl}
                alt={`Media ${currentIndex + 1}`}
                className="gallery-image"
                onError={(e) => {
                  console.error('Image failed to load:', currentMediaUrl);
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
            )}
            <div className="media-error" style={{ display: 'none' }}>
              <span>Failed to load media</span>
            </div>
          </div>

          {gallery.length > 1 && (
            <button
              className="gallery-nav gallery-next"
              onClick={goToNext}
              disabled={currentIndex === gallery.length - 1}
            >
              ›
            </button>
          )}
        </div>

        {gallery.length > 1 && (
          <div className="gallery-footer">
            <div className="gallery-counter">
              {currentIndex + 1} of {gallery.length}
            </div>
            
            <div className="gallery-thumbnails">
              {gallery.map((item, index) => {
                const itemUrl = getMediaUrl(item);
                const isVideoThumb = itemUrl && (
                  itemUrl.toLowerCase().includes('.mp4') || 
                  itemUrl.toLowerCase().includes('.mov')
                );
                
                return (
                  <div
                    key={index}
                    className={`gallery-thumbnail ${index === currentIndex ? 'active' : ''}`}
                    onClick={() => goToIndex(index)}
                  >
                    {isVideoThumb ? (
                      <div className="thumbnail-video">🎥</div>
                    ) : (
                      <img src={itemUrl} alt={`Thumbnail ${index + 1}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MediaGallery;