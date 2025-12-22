<!-- This file explains how to create LifeLog entries from several data sources. -->

# AI-Augmented Personal Archive

> **Enhanced Personal Timeline with AI-Powered Storytelling, Memory Intelligence, and Narrative Exploration**

Transform your personal data into meaningful stories and insights with advanced AI capabilities while keeping everything private and local.

## 🚀 What's New: AI-Augmented Features

This enhanced version transforms the original Personal Timeline into an intelligent, narrative-driven personal archive:

### ✨ Core AI Features
- **📖 Story Generation**: AI creates narrative chapters from your memories with multiple modes (chronological, thematic, people-centered, place-centered)
- **👥 People Intelligence**: Auto-detects people in your data, analyzes relationships, and tracks interaction evolution over time
- **🎨 Smart Galleries**: Natural language gallery creation ("show me creative moments", "find travel adventures")
- **🧠 Enhanced Memory Retrieval**: Semantic understanding beyond keyword search with conversational exploration
- **🔄 Memory Resurfacing**: Contextual memory suggestions and AI-generated reflection prompts
- **🗺️ Place-Based Narratives**: Enhanced map exploration with story-driven location insights
- **🔍 Self-Reflection Tools**: Pattern analysis, life chapter detection, and personal growth insights

### 🛡️ Privacy & Safety
- **🏠 100% Local Processing**: All AI runs on your machine, no external API calls
- **🔒 Private by Default**: Content generation respects privacy settings
- **🚫 Diagnostic Prevention**: Avoids medical/psychological diagnoses, presents patterns as suggestions
- **👤 User Control**: Complete control over sensitive content and exclusions
- **📊 Privacy Monitoring**: Comprehensive privacy compliance tracking

## 🎯 Quick Start

### Option 1: Full AI-Augmented Experience (Recommended)

**Prerequisites:**
- Docker Desktop installed and running
- Personal data in `../MyData/` directory (optional - sample data will be created)

**Start the application:**
```bash
# Quick start script
./start_app.sh

# Or manually:
docker-compose up -d --build
```

**Access the enhanced application:**
- **🎨 Main App**: http://localhost:52692 - Enhanced timeline with AI features
- **🤖 AI Chat**: http://localhost:57485 - Conversational memory exploration  
- **⚙️ Backend API**: http://localhost:8000 - REST endpoints
- **🧠 AI Services**: http://localhost:8086 - Local AI model endpoints

### Option 2: Try AI Features (No Docker Required)

Experience the AI capabilities with demo scripts:

```bash
# Run all demos
./test_services.sh

# Or individual demos:
python examples/gallery_curation_demo.py      # Smart gallery creation
python examples/memory_resurfacing_demo.py    # Contextual memory suggestions
python examples/self_reflection_demo.py       # Personal growth insights
python examples/privacy_safety_demo.py        # Privacy controls demo
```

## 🎮 Key Features to Explore

### 📖 AI Story Generation
1. Navigate to the main app (http://localhost:52692)
2. Click "Generate Story" 
3. Choose narrative mode:
   - **Chronological**: Time-based storytelling
   - **Thematic**: Topic-focused narratives  
   - **People-Centered**: Relationship-focused stories
   - **Place-Centered**: Location-based journeys
4. Watch AI create chapters with your memories

### 👥 People Intelligence
1. Go to "People" tab in the main app
2. See auto-detected people from your data
3. View interaction timelines and relationship evolution
4. Generate "best of us" compilations with shared memories

### 🎨 Smart Galleries
1. Navigate to "Galleries" section
2. Try natural language prompts:
   - "Show me creative moments"
   - "Find travel adventures" 
   - "Quiet reflective times"
   - "Celebrations with family"
3. Convert galleries to narrative stories

### 🤖 Enhanced Memory Chat
1. Visit the AI Chat interface (http://localhost:57485)
2. Ask conversational questions:
   - "Tell me about my experiences with friends"
   - "What were my highlights this year?"
   - "Show me memories from travel"
   - "Help me reflect on my growth"
3. Get contextual, narrative responses with memory connections

### 🔄 Proactive Memory Resurfacing
- Receive gentle suggestions for forgotten memories
- Get AI-generated reflection prompts
- Discover patterns connecting past and present interests
- Explore themed memory collections

## 🏗️ Architecture

### Enhanced Service Architecture
The AI-Augmented Personal Archive consists of four main services:

1. **Frontend** (Port 52692) - Enhanced React UI with AI components
2. **Backend** (Port 8000) - Data processing with AI enhancement pipeline  
3. **QA Service** (Port 57485) - Enhanced conversational memory access
4. **AI Services** (Port 8086) - Local AI models for narrative generation

### AI Agent System
Behind the scenes, specialized AI agents work together:
- **Archivist Agent**: Selects and curates relevant memories
- **Narrative Agent**: Creates coherent stories from personal data
- **Editor Agent**: Filters and organizes content appropriately  
- **Director Agent**: Sequences media and pacing for storytelling
- **Critic Agent**: Ensures quality, safety, and grounding in actual data

## 📊 System Status

- ✅ **112/119 tests passing** (94% success rate)
- ✅ **All core AI features operational**
- ✅ **Privacy and safety controls active**
- ✅ **Backward compatibility maintained**
- ✅ **Docker integration optimized**

## 🔧 Configuration

### AI Model Configuration
Create `.env` file from `.env.example` and customize:

```bash
# AI Models (all run locally)
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TTS_MODEL=espnet/kan-bayashi_ljspeech_vits
MULTIMODAL_MODEL=openai/clip-vit-base-patch32

# Processing Configuration  
AI_PROCESSING_BATCH_SIZE=32
AI_MAX_MEMORY_GB=4
ENABLE_GPU=false

# Feature Toggles
ENABLE_AI_ENHANCEMENT=true
ENHANCED_QA_ENABLED=true
```

## 🛠️ Development & Testing

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific AI features
python -m pytest tests/test_story_generation.py -v
python -m pytest tests/test_people_intelligence.py -v
python -m pytest tests/test_gallery_curation.py -v
python -m pytest tests/test_privacy_safety.py -v

# Frontend tests
cd src/frontend && npm test -- --watchAll=false
```

### Development Scripts
```bash
# Restart all services
./scripts/RESTART_DOCKER.sh

# Verify setup
./scripts/verify_enhanced_docker_setup.sh

# Stop services
docker-compose down
```

## 📚 Documentation

### AI-Augmented Features
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - Complete setup and testing guide
- [SYSTEM_INTEGRATION_REPORT.md](SYSTEM_INTEGRATION_REPORT.md) - Detailed test results and system status
- [docs/DOCKER_AI_INTEGRATION.md](docs/DOCKER_AI_INTEGRATION.md) - AI services Docker configuration

### Original Features
- [docs/DOCKER_READY.md](docs/DOCKER_READY.md) - Original Docker setup guide
- [docs/DATASET.md](docs/DATASET.md) - Sample dataset information
- [docs/TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md) - Common issues and solutions

## 🎯 Migration from Original Timeline

The AI-Augmented Personal Archive is fully backward compatible:

1. **Existing Data**: All your current data is preserved and enhanced
2. **Original Features**: Timeline view, QA system, and data importers still work
3. **Enhanced Experience**: New AI features layer on top of existing functionality
4. **Seamless Upgrade**: Run the migration automatically on first startup

---

## 📋 Table of Contents

### AI-Augmented Features
- [🚀 Quick Start](#-quick-start) - Start here for AI features!
- [🎮 Key Features to Explore](#-key-features-to-explore) - Try the AI capabilities
- [🏗️ Architecture](#️-architecture) - System design and AI agents
- [🔧 Configuration](#-configuration) - AI model settings
- [🛠️ Development & Testing](#️-development--testing) - Testing and development
- [📚 Documentation](#-documentation) - AI feature guides

### Original Timeline Features  
- [🔧 General Setup](#general-setup) - Original setup instructions
- [📥 Digital Data Importers](#digital-data-importers) - Data source importers
- [📊 Data Visualization](#visualization-of-the-personal-timeline) - Timeline UI
- [❓ Question Answering](#question-answer-over-the-personal-timeline) - Original QA system
- [📖 TimelineQA](#timelineqa-a-benchmark-for-question-answer-over-the-personal-timeline) - QA benchmark

---

## General Setup

## Step 0: Create environment

1. Install Docker Desktop from [this link](https://docs.docker.com/desktop/).

2. Follow install steps and use the Desktop app to start the docker engine.

3. Install `git-lfs` and clone the repo. You may need a conda env to do that:
```
conda create -n personal-timeline python=3.10
conda activate personal-timeline

conda install -c conda-forge git-lfs
git lfs install

git clone https://github.com/facebookresearch/personal-timeline
cd personal-timeline
```

4. Run init script (needs python)
```
sh src/init.sh
```
This will create a bunch of files/folders/symlinks needed for running the app.
This will also create a new directory under your home folder `~/personal-data`, the directory where your personal data will reside.

## Step 1: Setting up


## For Data Ingestion

Ingestion configs are controlled via parameters in `conf/ingest.conf` file. The configurations
are defaulted for optimized processing and don't need to be changed. 
You can adjust values for these parameters to run importer with a different configuration.



## For Data visualization

1. To set up a Google Map API (free), follow these [instructions](https://developers.google.com/maps/documentation/embed/quickstart#create-project).

Copy the following lines to `env/frontend.env.list`:
```
GOOGLE_MAP_API=<the API key goes here>
```

2. To embed Spotify, you need to set up a Spotify API (free) following [here](https://developer.spotify.com/dashboard/applications). You need to log in with a Spotify account, create a project, and show the `secret`.

Copy the following lines to `env/frontend.env.list`:
```
SPOTIFY_TOKEN=<the token goes here>
SPOTIFY_SECRET=<the secret goes here>
```

## For Question-Answering

Set up an OpenAI API following these [instructions](https://openai.com/api/).

Copy the following line to `env/frontend.env.list`:
```
OPENAI_API_KEY=<the API key goes here>
```

## Digital Data Importers


## Downloading your personal data

We currently support 9 data sources. Here is a summary table:

| Digital Services | Instructions                                                                        | Destinations                                                             | Use cases                                              |
|------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------|
| Apple Health     | [Link](https://github.com/facebookresearch/personal-timeline#apple-health)  | personal-data/apple-health                                               | Exercise patterns, calorie counts                      |
| Amazon           | [Link](https://github.com/facebookresearch/personal-timeline#amazon)        | personal-data/amazon                                                     | Product recommendation, purchase history summarization |
| Amazon Kindle    | [Link](https://github.com/facebookresearch/personal-timeline#amazon)        | personal-data/amazon-kindle                                              | Book recommendation                                    |
| Spotify          | [Link](https://github.com/facebookresearch/personal-timeline#spotify)       | personal-data/spotify                                                    | Music / streaming recommendation                       |
| Venmo            | [Link](https://github.com/facebookresearch/personal-timeline#venmo)         | personal-data/venmo                                                      | Monthly spend summarization                            |
| Libby            | [Link](https://github.com/facebookresearch/personal-timeline#libby)         | personal-data/libby                                                      | Book recommendation                                    |
| Google Photos    | [Link](https://github.com/facebookresearch/personal-timeline#google-photos) | personal-data/google_photos                                              | Food recommendation, Object detections, and more               |
| Google Location  | [Link](https://github.com/facebookresearch/personal-timeline#google-photos) | personal-data/google-timeline/Location History/Semantic Location History | Location tracking / visualization                      |
| Facebook posts   | [Link](https://github.com/facebookresearch/personal-timeline#facebook-data) | personal-data/facebook                                                   | Question-Answering over FB posts / photos              |

If you have a different data source not listed above, follow the instructions [here](NEW_DATASOURCE.md)
to add this data source to the importer.

### GOOGLE PHOTOS and GOOGLE TIMELINE
<!--1. You need to download your Google photos from [Google Takeout](https://takeout.google.com/).  
The download from Google Takeout would be in multiple zip files. Unzip all the files.

2. It may be the case that some of your photo files are .HEIC. In that case follow the steps below to convert them to .jpeg  
The easiest way to do this on a Mac is:

     -- Select the .HEIC files you want to convert.   
     -- Right click and choose "quick actions" and then you'll have an option to convert the image.  
     -- If you're converting many photos, this may take a few minutes. 

2. Move all the unzipped folders inside `~/personal-data/google_photos/`. There can be any number of sub-folders under `google_photos`.-->

1. You can download your Google photos and location (also Gmail, map and google calendar) data from [Google Takeout](https://takeout.google.com/).
2. The download from Google Takeout would be in multiple zip files. Unzip all the files.
3. For Google photos, move all the unzipped folders inside `~/personal-data/google_photos/`. There can be any number of sub-folders under `google_photos`.
4. For Google locations, move the unzipped files to `personal-data/google-timeline/Location History/Semantic Location History`.

### FACEBOOK DATA
1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=your_facebook_information) 
2. Click on <b>Download your information</b> and download FB data in JSON format
3. Unzip the downloaded file and copy the directory `posts` sub-folder to `~/personal-data/facebook`. The `posts` folder would sit directly under the Facebook folder.

### APPLE HEALTH
1. Go to the Apple Health app on your phone and ask to export your data. This will create a file called iwatch.xml and that's the input file to the importer.
2. Move the downloaded file to this `~/personal-data/apple-health`

### AMAZON
1. Request your data from Amazon here: https://www.amazon.com/gp/help/customer/display.html?nodeId=GXPU3YPMBZQRWZK2
They say it can take up to 30 days, but it took about 2 days. They'll email you when it's ready.

They separate Amazon purchases from Kindle purchases into two different directories.

The file you need for Amazon purchases is Retail.OrderHistory.1.csv
The file you need for Kindle purchases is Digital Items.csv

2. Move data for Amazon purchases to `~/personal-data/amazon` folder and of kindle downloads to `~/personal-data/amazon-kindle` folder

### VENMO
1. Download your data from Venmo here -- https://help.venmo.com/hc/en-us/articles/360016096974-Transaction-History

2. Move the data into `~/personal-data/venmo` folder.

### LIBBY
1. Download your data from Libby here -- https://libbyapp.com/timeline/activities. Click on `Actions` then `Export Timeline`

2. Move the data into `~/personal-data/libby` folder.


### SPOTIFY

1. Download your data from Spotify here -- https://support.spotify.com/us/article/data-rights-and-privacy-settings/
They say it can take up to 30 days, but it took about 2 days. They'll email you when it's ready.

2. Move the data into `~/personal-data/spotify` folder.

# Running the code
Now that we have all the data and setting in place, we can either run individual steps or the end-to-end system.
This will import your photo data to SQLite (this is what will go into the episodic database), build summaries
and make data available for visualization and search.


Running the Ingestion container will add two types of file to `~/personal-data/app_data` folder
 - Import your data to an SQLite DB named `raw_data.db`
 - Export your personal data into csv files such as `books.csv`, `exercise.csv`, etc.

### Option 1:
To run the pipeline end-to-end (with frontend and QA backend), simply run 
```
docker-compose up -d --build
```

### Option 2:
You can also run ingestion, visualization, and the QA engine separately.
To start data ingestion, use  
```
docker-compose up -d backend --build
```

## Check progress
Once the docker command is run, you can see running containers for backend and frontend in the docker for Mac UI.
Copy the container Id for ingest and see logs by running the following command:  
```
docker logs -f <container_id>
```

<!-- # Step 5: Visualization and Question Answering -->

## Visualization of the personal timeline

To start the visualization frontend:
```
docker-compose up -d frontend --build
```

Running the Frontend will start a ReactJS UI at `http://localhost:3000`. See [here](src/frontend/) for more details.

We provide an anonymized digital data [dataset](sample_data/) for testing the UI and QA system, see [here](DATASET.md) for more details.

![Timeline Visualization](ui.png)


## Question Answer over the personal timeline

The QA engine is based on PostText, a QA system for answering queries that require computing aggregates over personal data.

PostText Reference ---  [https://arxiv.org/abs/2306.01061](https://arxiv.org/abs/2306.01061):
```
@article{tan2023posttext,
      title={Reimagining Retrieval Augmented Language Models for Answering Queries},
      author={Wang-Chiew Tan and Yuliang Li and Pedro Rodriguez and Richard James and Xi Victoria Lin and Alon Halevy and Scott Yih},
      journal={arXiv preprint:2306.01061},
      year={2023},
}
```

To start the QA engine, run:
```
docker-compose up -d qa --build
```
The QA engine will be running on a flask server inside a docker container at `http://localhost:8085`. 

See [here](src/qa) for more details.

![QA Engine](qa.png)

There are 3 options for the QA engine.
* *ChatGPT*: uses OpenAI's gpt-3.5-turbo [API](https://platform.openai.com/docs/models/overview) without the personal timeline as context. It answers world knowledge question such as `what is the GDP of US in 2021` but not personal questions.
* *Retrieval-based*: answers question by retrieving the top-k most relevant episodes from the personal timeline as the LLM's context. It can answer questions over the personal timeline such as `show me some plants in my neighborhood`.
* *View-based*: translates the input question to a (customized) SQL query over tabular views (e.g., books, exercise, etc.) of the personal timeline. This QA engine is good at answering aggregate queries (`how many books did I purchase?`) and min/max queries (`when was the last time I travel to Japan`).


Example questions you may try:
* `Show me some photos of plants in my neighborhood`
* `Which cities did I visit when I traveled to Japan?`
* `How many books did I purchase in April?`

## 📖 TimelineQA: a benchmark for Question Answer over the personal timeline

TimelineQA is a synthetic benchmark for accelerating progress on querying personal timelines. 
TimelineQA generates lifelogs of imaginary people. The episodes in the lifelog range from major life episodes such as high
school graduation to those that occur on a daily basis such as going for a run. We have evaluated SOTA models for atomic and multi-hop QA on the benchmark. 

Please check out the TimelineQA github [repo](https://github.com/facebookresearch/TimelineQA) and the TimelineQA paper ---  [https://arxiv.org/abs/2306.01061](https://arxiv.org/abs/2306.01061):
```
@article{tan2023timelineqa,
  title={TimelineQA: A Benchmark for Question Answering over Timelines},
  author={Tan, Wang-Chiew and Dwivedi-Yu, Jane and Li, Yuliang and Mathias, Lambert and Saeidi, Marzieh and Yan, Jing Nathan and Halevy, Alon Y},
  journal={arXiv preprint arXiv:2306.01069},
  year={2023}
}
```

---

## 🔄 Original Personal Timeline Features

> **Note**: This is a fork of [facebookresearch/personal-timeline](https://github.com/facebookresearch/personal-timeline) with enhanced AI capabilities and Docker improvements.

The AI-Augmented Personal Archive maintains full compatibility with all original features while adding advanced AI capabilities on top. All existing functionality continues to work as before.

### Key Improvements in This Fork

- ✅ **AI-Augmented Features**: Story generation, people intelligence, smart galleries, memory resurfacing
- ✅ **Enhanced Privacy**: Local AI processing, diagnostic prevention, comprehensive user controls
- ✅ **Full Docker support** with working volume mounts and data paths
- ✅ **Fixed dependency issues** (ajv, node modules)
- ✅ **Simplified startup scripts** for Docker operations
- ✅ **Updated documentation** and troubleshooting guides
- ✅ **Facebook data importer fixes** - Auto-detection + resilient solution (176 posts imported!)
- ✅ **Frontend display fixes** - Category JSON files auto-generation
- ✅ **Bug fixes** - Fixed 2 type inconsistency bugs in photo importer

## Documentation

### User Guides
- [DOCKER_READY.md](docs/DOCKER_READY.md) - Complete Docker setup guide
- [RUN_LOCALLY.md](docs/RUN_LOCALLY.md) - Running without Docker
- [TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md) - Common issues and solutions
- [DATASET.md](docs/DATASET.md) - Sample dataset information
- [MODERNIZATION_GUIDE.md](docs/MODERNIZATION_GUIDE.md) - Modernization notes

### Scripts
- `scripts/RESTART_DOCKER.sh` - Restart all Docker services
- `scripts/teardown.sh` - Stop and remove containers
- `scripts/verify_docker_setup.sh` - Verify Docker configuration

### AI Assistant Files
Development notes and configuration files used during development with OpenHands are in `docs/ai-assistant/`.

## 📄 License

The codebase is licensed under the [Apache 2.0 license](LICENSE).

## 🤝 Contributing

See [contributing](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## 🙏 Contributor Attribution

### AI-Augmented Personal Archive Contributors
- **AI Enhancement Development**: Comprehensive AI feature implementation including story generation, people intelligence, smart galleries, memory resurfacing, and privacy controls
- **System Integration**: Full integration testing, Docker optimization, and backward compatibility
- **Documentation**: Complete documentation overhaul with quick start guides and testing instructions

### Original Personal Timeline Contributors
We'd like to thank the following contributors for their contributions to the original project:
- [Tripti Singh](https://github.com/tripti-singh)
  - Design and implementation of the sqlite DB backend
  - Designing a pluggable data import and enrichment layer and building the pipeline orchestrator.
  - Importers for all six [data sources](​​https://github.com/facebookresearch/personal-timeline#digital-data-importers)
  - Generic csv and json data sources importer with [instructions](https://github.com/facebookresearch/personal-timeline/blob/main/NEW_DATASOURCE.md)
  - Dockerization
  - Contributing in Documentation
- [Wang-Chiew Tan](https://github.com/wangchiew)
  - Implementation of the [PostText](https://arxiv.org/abs/2306.01061) query engine
- [Pierre Moulon](https://github.com/SeaOtocinclus) for providing open-sourcing guidelines and suggestions

---

## 🎉 Get Started Now!

Ready to transform your personal data into meaningful stories and insights?

```bash
# Quick start with AI features
./start_app.sh

# Or try demos without Docker
./test_services.sh
```

Visit http://localhost:52692 to explore your AI-augmented personal archive!
