# Task 3.4_IntegrationsAndAPI.3: Webhook_System

**Epic**: 3.4_IntegrationsAndAPI IntegrationsAndAPI  
**Phase**: 3 - Advanced Features and Optimization  
**Duration**: 2-3 days  
**Assignee**: Development Team  
**Priority**: Medium-High  

---

## Task Overview

Build a secure, scalable webhook platform that notifies external apps of events (memory.created/updated, tag.added, event.detected, import.completed). Include subscription APIs, signature verification, retries with backoff, dead-letter queues, and delivery dashboards.

## Objectives
- Reliable at-least-once delivery with idempotency
- Tenant/app isolation and rate limiting
- Simple subscription management and test tools

## Dependencies
- Public API (Task 3.4.2)
- Observability/metrics (Phase4.3)

## Sub-tasks
1. **Event Model** (Effort: 5 pts)
   - Canonical event types and payload schema
   - Correlation IDs, versioning

2. **Subscription Service** (Effort: 6 pts)
   - CRUD APIs: endpoints, event filters, secrets
   - Delivery preferences (batch vs. single)

3. **Delivery Engine** (Effort: 8 pts)
   - Queue-based workers, exponential backoff, jitter
   - Idempotency keys, dedup window
   - DLQ after N failures

4. **Security** (Effort: 4 pts)
   - HMAC signatures (SHA-256) with shared secrets
   - IP allowlist/denylist, TLS enforcement

5. **Developer UX** (Effort: 5 pts)
   - Redelivery, replay by time window
   - Test event generator, webhook.site integration
   - Delivery logs and dashboards

## Acceptance Criteria
- [ ] Subscriptions CRUD with scoped keys
- [ ] HMAC signature documented and validated server-side
- [ ] Retries with backoff and DLQ in place
- [ ] P95 delivery latency < 2s under normal load
- [ ] Redelivery and replay work as expected
- [ ] Dashboards for success rate, latency, failure reasons

## Technical Implementation
### API Examples
- POST /api/v1/webhooks/subscriptions
- GET /api/v1/webhooks/deliveries?status=failed

### Signing
- X-PT-Signature: t=timestamp,v1=hex(hmac_sha256(secret, timestamp + body))
- Reject if clock skew > 5 min or mismatch

### Storage
- subscriptions(id, url, events, secret, status)
- deliveries(id, sub_id, event_id, status, attempts, last_error)

### Worker
- Celery/RQ workers with concurrency
- Backoff schedule: 5s, 30s, 2m, 10m, 1h

## Testing Strategy
- Integration tests with a mock receiver
- Replay tests, signature verification cases
- Load tests with 1k events/sec across tenants

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Receiver downtime | High | Medium | Retries + DLQ + alerting |
| Signature misuse | Low | High | Clear docs + sample code + rotation |
| Runaway retries | Medium | Medium | Caps + circuit breakers |

## Timeline & Effort
**Total Effort**: 28 story points  
**Breakdown**: Engine 12pts, API/UX 10pts, Security/QA 6pts  
**Duration**: 2 weeks  
**Milestones**:
- W1: Subscriptions + signing + worker
- W2: Dashboard + replay + hardening

**Success Metrics**:
- >99% successful deliveries within 24h
- <0.1% signature failures (non-malicious)

---

**Change Log**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-18 | OpenHands | Initial draft |
| 2.0 | 2025-12-19 | OpenHands | Webhook system design
