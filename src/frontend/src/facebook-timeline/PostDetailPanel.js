import React from 'react';

const PostDetailPanel = ({ date, posts, loading, onMediaClick }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getPostTypeIcon = (post) => {
    if (post.isComment) return '💬';
    if (post.isEmpty) return '⚪';
    if (post.hasMedia) {
      const hasVideo = post.media_files.some(m => 
        m.url && (m.url.includes('.mp4') || m.url.includes('.mov')));
      return hasVideo ? '🎥' : '📷';
    }
    
    switch (post.post_type) {
      case 'photo': return '📷';
      case 'video': return '🎥';
      case 'link': return '🔗';
      case 'status': return '📝';
      default: return '📝';
    }
  };

  const getPostTypeLabel = (post) => {
    if (post.isComment) return 'Comment';
    if (post.isEmpty) return 'Empty Post';
    return post.post_type || 'Post';
  };

  const handleMediaClick = (mediaFile, allMediaFiles) => {
    if (onMediaClick) {
      onMediaClick(mediaFile, allMediaFiles);
    }
  };

  // Group posts by type for better organization
  const groupedPosts = posts.reduce((groups, post) => {
    const type = post.isComment ? 'comments' : 
                 post.isEmpty ? 'empty' : 
                 post.hasMedia ? 'media' : 'text';
    if (!groups[type]) groups[type] = [];
    groups[type].push(post);
    return groups;
  }, {});

  if (loading) {
    return (
      <div className="post-detail-panel loading">
        <div className="loading-spinner"></div>
        <p>Loading posts...</p>
      </div>
    );
  }

  if (!posts || posts.length === 0) {
    return (
      <div className="post-detail-panel empty">
        <h3>No posts found for {formatDate(date)}</h3>
        <p>Try adjusting your filters or selecting a different date.</p>
      </div>
    );
  }

  return (
    <div className="post-detail-panel">
      <div className="panel-header">
        <h3>Posts for {formatDate(date)}</h3>
        <div className="post-summary">
          <span className="post-count">{posts.length} total</span>
          {groupedPosts.media && <span className="media-count">📷 {groupedPosts.media.length}</span>}
          {groupedPosts.text && <span className="text-count">📝 {groupedPosts.text.length}</span>}
          {groupedPosts.comments && <span className="comment-count">💬 {groupedPosts.comments.length}</span>}
          {groupedPosts.empty && <span className="empty-count">⚪ {groupedPosts.empty.length}</span>}
        </div>
      </div>

      <div className="posts-list">
        {posts.map((post) => (
          <div key={post.id} className={`post-item ${post.isComment ? 'comment' : ''} ${post.isEmpty ? 'empty' : ''}`}>
            <div className="post-header">
              <span className="post-type-icon">{getPostTypeIcon(post)}</span>
              <span className="post-time">{formatTime(post.timestamp)}</span>
              <span className="post-type-label">{getPostTypeLabel(post)}</span>
              {post.isEmpty && <span className="empty-badge">Empty</span>}
              {post.isComment && <span className="comment-badge">Comment</span>}
            </div>

            {post.content && post.content.trim() && (
              <div className="post-content">
                <p>{post.content}</p>
              </div>
            )}

            {!post.content && !post.hasMedia && (
              <div className="post-content empty-content">
                <p className="empty-message">
                  {post.isComment ? 'Comment content not available' : 'Empty post - content may have been deleted or is not accessible'}
                </p>
              </div>
            )}

            {post.media_files && post.media_files.length > 0 && (
              <div className="post-media">
                <div className="media-thumbnails">
                  {post.media_files.slice(0, 4).map((mediaFile, index) => {
                    const mediaUrl = mediaFile.url || mediaFile.uri || mediaFile.path || mediaFile;
                    const isVideo = typeof mediaUrl === 'string' && 
                      (mediaUrl.includes('.mp4') || mediaUrl.includes('.mov') || mediaUrl.includes('video'));
                    
                    return (
                      <div
                        key={index}
                        className="media-thumbnail"
                        onClick={() => handleMediaClick(mediaFile, post.media_files)}
                      >
                        {isVideo ? (
                          <div className="video-thumbnail">
                            <span className="video-icon">🎥</span>
                            <span className="video-label">Video</span>
                          </div>
                        ) : (
                          <>
                            <img
                              src={mediaUrl}
                              alt="Post media"
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                              }}
                            />
                            <div className="media-placeholder" style={{ display: 'none' }}>
                              <span>📷</span>
                              <span>Image not available</span>
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                  {post.media_files.length > 4 && (
                    <div className="media-count-badge">
                      +{post.media_files.length - 4} more
                    </div>
                  )}
                </div>
              </div>
            )}

            {post.location && (
              <div className="post-location">
                <span className="location-icon">📍</span>
                <span>{post.location}</span>
              </div>
            )}

            {post.tagged_people && post.tagged_people.length > 0 && (
              <div className="post-tags">
                <span className="tags-icon">👥</span>
                <span>with {post.tagged_people.join(', ')}</span>
              </div>
            )}

            <div className="post-stats">
              {post.reactions && Object.keys(post.reactions).length > 0 && (
                <div className="reactions">
                  {Object.entries(post.reactions).map(([reaction, count]) => (
                    <span key={reaction} className="reaction">
                      {reaction}: {count}
                    </span>
                  ))}
                </div>
              )}
              {post.comments_count > 0 && (
                <div className="comments">
                  <span>💬 {post.comments_count} comment{post.comments_count !== 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PostDetailPanel;