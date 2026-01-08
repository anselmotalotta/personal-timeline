# 🚀 AI Personal Archive - Deployment Guide

## Quick Start (5 minutes)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd personal-timeline
chmod +x start_app.sh
```

### 2. Configure API Tokens (Optional but Recommended)

**Copy the environment template:**
```bash
cp .env.example .env
```

**Add your API keys to `.env`:**
```bash
# At minimum, add ONE of these for AI functionality:
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here  
# OR
GOOGLE_API_KEY=your-google-ai-key-here

# Optional: Configure provider preference (default: openai,anthropic,google)
AI_PROVIDER_HIERARCHY=openai,anthropic,google
```

**Get API Keys:**
- **OpenAI**: https://platform.openai.com/api-keys (Recommended - best vision support)
- **Anthropic**: https://console.anthropic.com/ (Good for text analysis)
- **Google AI**: https://makersuite.google.com/app/apikey (Free tier available)

### 3. Start the Application
```bash
./start_app.sh
```

**Access your archive:**
- **Main App**: http://localhost:52692 - Your personal timeline with AI features
- **AI Chat**: http://localhost:57485 - Conversational memory exploration
- **Health Status**: http://localhost:8086/health - System status and API availability

---

## 🔑 API Token Configuration

### Why API Tokens?
The AI Personal Archive runs **100% locally** but uses cloud AI APIs for machine learning tasks like:
- 📖 Story generation from your memories
- 👥 Face detection and people recognition  
- 🎨 Smart gallery curation
- 🧠 Semantic memory search

**Your personal data never leaves your machine** - only ML processing requests are sent to APIs.

### Token Setup Options

#### Option 1: Full AI Experience (Recommended)
Add at least one API key for full functionality:

```bash
# .env file
OPENAI_API_KEY=sk-your-key-here        # Best overall, ~$5-10/month typical usage
ANTHROPIC_API_KEY=sk-ant-your-key-here # Good for text analysis
GOOGLE_API_KEY=your-google-key-here    # Free tier available
```

#### Option 2: No API Keys (Limited Mode)
The system works without API keys but with reduced functionality:
- ✅ Timeline visualization
- ✅ Data import and organization
- ✅ Basic search and filtering
- ❌ AI story generation
- ❌ Smart galleries
- ❌ People intelligence
- ❌ Semantic memory search

---

## 🚦 System Status & Health Monitoring

### Check System Health
Visit http://localhost:8086/health to see:

```json
{
  \"overall_status\": \"healthy\",
  \"api_status\": {
    \"openai\": {
      \"has_credentials\": true,
      \"is_available\": true,
      \"status\": \"active\"
    },
    \"anthropic\": {
      \"has_credentials\": false,
      \"is_available\": false,
      \"status\": \"no_credentials\"
    }
  },
  \"services\": {
    \"ai_providers\": {\"healthy\": true},
    \"data_processing\": {\"healthy\": true},
    \"local_storage\": {\"healthy\": true}
  }
}
```

### Status Indicators

**🟢 Fully Operational**
- All API keys configured
- All AI features available
- System status: \"healthy\"

**🟡 Partially Operational** 
- Some API keys missing
- Core features work, some AI features limited
- System status: \"degraded\"

**🔴 Limited Mode**
- No API keys configured
- Only basic timeline features available
- System status: \"limited\"

### In-App Feature Gating

The application **disables AI features** when API keys are missing and shows clear explanations:

**Main App (http://localhost:52692):**
- 🟢 Green badge: \"AI Features Active\" - all features enabled
- 🟡 Yellow badge: \"Limited AI Features\" - some features disabled
- 🔴 Red badge: \"AI Features Unavailable\" - all AI features disabled

**Disabled Feature Behavior:**
- **AI Search**: Replaced with setup instructions and API key links
- **Story Generation Button**: Disabled with tooltip explaining requirements
- **People Intelligence Button**: Disabled with specific provider requirements
- **Smart Galleries Button**: Disabled with setup guidance
- **Feature Cards**: Show \"AI Features Disabled\" card with setup button

**User Guidance:**
- Clear tooltips on disabled buttons explaining what's needed
- Setup instructions with direct links to API key pages
- Visual indicators showing which features require which providers
- Immediate feedback when API keys are added (after restart)

---

## 💰 Cost Management

### Usage Tracking
The system tracks all API usage locally:

```bash
# View usage summary
curl http://localhost:8086/usage/summary

# Response:
{
  \"total_cost_7_days\": 2.45,
  \"total_calls_7_days\": 156,
  \"providers\": {
    \"openai\": {\"cost\": 2.45, \"calls\": 156}
  }
}
```

### Typical Costs (Monthly)
- **Light usage** (few stories, basic search): $2-5
- **Regular usage** (daily stories, people detection): $5-15  
- **Heavy usage** (extensive AI features): $15-30

### Cost Control Settings
```bash
# .env file
MAX_CONCURRENT_API_CALLS=3          # Limit parallel requests
API_TIMEOUT_SECONDS=30              # Prevent long-running requests
LOCAL_CACHE_TTL_HOURS=24           # Cache results to reduce API calls
```

---

## 🔧 Advanced Configuration

### Provider Hierarchy
Configure which AI providers to try first:

```bash
# .env file
AI_PROVIDER_HIERARCHY=openai,anthropic,google  # Try OpenAI first, then Anthropic, then Google
```

### Model Selection
Choose specific models for each provider:

```bash
# .env file
DEFAULT_MODEL_OPENAI=gpt-4                    # Best quality
DEFAULT_MODEL_ANTHROPIC=claude-3-sonnet-20240229
DEFAULT_MODEL_GOOGLE=gemini-pro
```

### Privacy Settings
```bash
# .env file
ENABLE_USAGE_ANALYTICS=true        # Track usage locally (recommended)
ENABLE_ERROR_REPORTING=false       # Don't send error reports (privacy)
KEEP_API_LOGS_DAYS=7              # How long to keep usage logs
DEBUG_LOGGING=false               # Disable debug logs in production
```

---

## 🛠️ Troubleshooting

### \"AI Features Unavailable\"
1. Check `.env` file exists and has valid API keys
2. Restart the application: `./start_app.sh`
3. Check health status: http://localhost:8086/health
4. Verify API key format (should start with `sk-` for OpenAI)

### \"API Rate Limited\"
1. System automatically retries with exponential backoff
2. Check usage at http://localhost:8086/usage/summary
3. Consider reducing `MAX_CONCURRENT_API_CALLS` in `.env`

### \"Service Degraded\"
1. Check health status for specific service issues
2. Verify data directory permissions: `chmod 700 ./MyData`
3. Ensure sufficient disk space (>1GB free)

### API Key Validation
```bash
# Test OpenAI key
curl -H \"Authorization: Bearer $OPENAI_API_KEY\" https://api.openai.com/v1/models

# Test Anthropic key  
curl -H \"x-api-key: $ANTHROPIC_API_KEY\" https://api.anthropic.com/v1/messages

# Test Google key
curl \"https://generativelanguage.googleapis.com/v1/models?key=$GOOGLE_API_KEY\"
```

---

## 🔒 Security Best Practices

### API Key Security
```bash
# Set secure file permissions
chmod 600 .env

# Never commit .env to version control
echo \".env\" >> .gitignore

# Rotate keys regularly (every 3-6 months)
```

### Data Privacy
- All personal data stays on your machine
- Only ML processing requests sent to APIs
- No personal information in API requests
- Local usage tracking only
- Secure file permissions enforced

### Network Security
- All services run on localhost only
- No external network access required except for API calls
- Docker containers isolated from host network
- API keys encrypted in transit (HTTPS)

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Automated health check
curl http://localhost:8086/health

# Service metrics
curl http://localhost:8086/metrics

# Usage summary
curl http://localhost:8086/usage/summary
```

### Log Monitoring
```bash
# View service logs
docker-compose logs -f ai-services

# View specific service
docker-compose logs -f backend
```

### Data Backup
```bash
# Backup your personal data
cp -r ./MyData ./MyData.backup.$(date +%Y%m%d)

# Backup configuration
cp .env .env.backup
```

---

## 🚀 Production Deployment

### Environment Setup
```bash
# Production environment variables
NODE_ENV=production
FLASK_ENV=production
DEBUG_LOGGING=false
ENABLE_ERROR_REPORTING=false
```

### Resource Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended  
- **Storage**: 10GB+ for personal data
- **Network**: Outbound HTTPS for API calls

### Scaling Considerations
- Increase `MAX_CONCURRENT_API_CALLS` for faster processing
- Add multiple API keys for higher rate limits
- Monitor usage costs with built-in tracking
- Consider local AI models for complete offline operation

---

## 📞 Support

### Getting Help
1. Check health status: http://localhost:8086/health
2. Review logs: `docker-compose logs`
3. Consult troubleshooting section above
4. Check GitHub issues for known problems

### Reporting Issues
Include in your report:
- Health status output
- Relevant log excerpts (with API keys redacted)
- Steps to reproduce
- Expected vs actual behavior

---

**Ready to explore your AI-augmented personal archive!** 🎉

Visit http://localhost:52692 to get started.