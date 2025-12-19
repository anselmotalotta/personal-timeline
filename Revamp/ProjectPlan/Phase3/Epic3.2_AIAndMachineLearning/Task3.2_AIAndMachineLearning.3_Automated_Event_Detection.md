# Task 3.2_AIAndMachineLearning.3: Automated_Event_Detection

**Epic**: 3.2_AIAndMachineLearning AIAndMachineLearning  
**Phase**: 3 - Advanced Features and Optimization  
**Duration**: 2-3 days  
**Assignee**: Development Team  
**Priority**: Medium-High  

---

## Task Overview

Automatically detect significant events and milestones from multimodal data: trips, moves, job changes, relationships, celebrations, and periods of change. Use temporal clustering, semantic analysis, and user confirmation flows. Events become first-class entities with properties and links to memories.

## Objectives
- Detect 8+ event types with high precision
- Provide editable event summaries and timelines
- Link events to relevant memories/people/places
- Allow user feedback to improve detection

## Dependencies
- AI Content Analysis (Task 3.2.1)
- Timeline & memory data model (Phase2)

## Sub-tasks
1. **Event Schema & Storage** (Effort: 5 pts)
   - Event types: move, trip, job, relationship, celebration, health, project
   - Fields: title, type, start/end, confidence, participants, places
   - Relations: event↔memories, event↔people, event↔places

2. **Temporal Clustering** (Effort: 6 pts)
   - Detect bursts of activity in time series
   - Merge/split based on gaps and continuity
   - Seasonality adjustments

3. **Semantic Classification** (Effort: 7 pts)
   - LLM prompts on clustered content
   - Rule assist: keywords (“new job”, “moved to”, “we’re engaged”)
   - Confidence scoring + reason codes

4. **People/Place Attribution** (Effort: 4 pts)
   - Co-occurrence graphs to identify participants
   - Geospatial inference for move/travel

5. **Event Summaries** (Effort: 5 pts)
   - 2–3 sentence narrative + highlight images
   - Timeline cards and detail pages

6. **Review & Feedback** (Effort: 4 pts)
   - “Confirm/merge/split/ignore” UI
   - Feedback loop updates thresholds/rules

## Acceptance Criteria
- [ ] Precision >85% and recall >70% across event types (test set)
- [ ] Events stored as entities and surfaced on timeline
- [ ] Summaries grounded with linked memories
- [ ] Edit/merge/split supported with full undo
- [ ] Confidence <70% routed to review queue
- [ ] Performance: 1k memories processed in <2 minutes
- [ ] Privacy: No external calls without consent

## Technical Implementation
### Detection Pipeline
- Time series clustering (DBSCAN/HDBSCAN)
- LLM classification with few-shot prompts
- Rules for high-precision anchors (e.g., “new job at”)

### Data Model
```sql
CREATE TABLE events (
  id UUID PRIMARY KEY,
  type TEXT,
  title TEXT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  confidence NUMERIC,
  metadata JSONB
);
CREATE TABLE event_memories (
  event_id UUID REFERENCES events(id),
  memory_id UUID REFERENCES memories(id)
);
```

### Frontend
- Event cards in timeline and a dedicated Events view
- Event details with narrative and related people/places

## Testing Strategy
- Labeled test corpus by event type
- Inter-annotator agreement checks
- A/B test user engagement with events

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Ambiguous events | Medium | Medium | Human review + edit tools |
| Over-clustering | Medium | Medium | Split UI + penalties |
| Under-clustering | Medium | Medium | Merge UI + thresholds |

## Timeline & Effort
**Total Effort**: 31 story points  
**Breakdown**: Backend/AI 20pts, Frontend 7pts, Testing 4pts  
**Duration**: 2 weeks  
**Milestones**:
- W1: Schema + detection
- W2: Summaries + review + polish

**Success Metrics**:
- 2x increase in meaningful rediscovery via events
- 75%+ confirmed event accuracy

---

**Change Log**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-18 | OpenHands | Initial draft |
| 2.0 | 2025-12-19 | OpenHands | Full event detection design
