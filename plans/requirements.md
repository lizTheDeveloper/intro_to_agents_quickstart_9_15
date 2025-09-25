# First Mate Autonomous Agent - Requirements

## Core Dependencies

### LLM Integration
- `openai>=1.0.0` - Primary LLM client for LM Studio integration
- `litellm[proxy]>=1.77.1` - Already in project, provides additional LLM flexibility

### Database & Storage
- `sqlalchemy>=2.0.0` - ORM for structured data storage
- `alembic>=1.12.0` - Database migrations
- `sqlite3` - Built-in Python module for local database
- `redis>=5.0.0` - For caching and session management
- `pickle` - Built-in Python module for object serialization

### Memory & Context Management
- `chromadb>=0.4.0` - Vector database for semantic memory storage
- `sentence-transformers>=2.2.0` - Text embeddings for memory retrieval
- `numpy>=1.24.0` - Numerical operations for embeddings
- `faiss-cpu>=1.7.0` - Alternative vector search (CPU version)

### Communication & Notifications
- `smtplib` - Built-in Python module for email
- `email` - Built-in Python module for email handling
- `matrix-nio>=0.21.0` - Matrix protocol client
- `slack-sdk>=3.23.0` - Slack integration
- `twilio>=8.10.0` - SMS and phone call capabilities
- `requests>=2.31.0` - HTTP requests for webhooks

### Scheduling & Task Management
- `schedule>=1.2.0` - Task scheduling
- `apscheduler>=3.10.0` - Advanced Python scheduler
- `croniter>=1.4.0` - Cron expression parsing
- `pytz>=2023.3` - Timezone handling

### Web Interface & APIs
- `fastapi>=0.104.0` - Web framework for API endpoints
- `uvicorn>=0.24.0` - ASGI server
- `websockets>=12.0` - WebSocket support for real-time communication
- `jinja2>=3.1.0` - Template engine for web UI
- `python-multipart>=0.0.6` - File upload support

### News & Information Feeds
- `feedparser>=6.0.10` - RSS/Atom feed parsing
- `newspaper3k>=0.2.8` - Article extraction
- `beautifulsoup4>=4.12.0` - HTML parsing
- `arxiv>=2.1.0` - ArXiv API for research papers
- `praw>=7.7.0` - Reddit API wrapper

### Data Processing & Analysis
- `pandas>=2.1.0` - Data manipulation
- `python-dateutil>=2.8.0` - Date parsing utilities
- `pytz>=2023.3` - Timezone support
- `regex>=2023.10.0` - Advanced regex operations

### Configuration & Environment
- `pydantic>=2.5.0` - Data validation and settings
- `python-dotenv>=1.0.0` - Environment variable management
- `pyyaml>=6.0.1` - YAML configuration files
- `toml>=0.10.0` - TOML configuration support

### Logging & Monitoring
- `loguru>=0.7.0` - Advanced logging
- `structlog>=23.2.0` - Structured logging
- `prometheus-client>=0.19.0` - Metrics collection
- `psutil>=5.9.0` - System monitoring

### Security & Authentication
- `cryptography>=41.0.0` - Encryption and security
- `passlib>=1.7.4` - Password hashing
- `python-jose>=3.3.0` - JWT token handling
- `bcrypt>=4.1.0` - Password hashing

### Async & Concurrency
- `asyncio` - Built-in Python module for async programming
- `aiohttp>=3.9.0` - Async HTTP client/server
- `aioredis>=2.0.0` - Async Redis client
- `asyncpg>=0.29.0` - Async PostgreSQL driver

### Testing & Development
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async testing support
- `pytest-mock>=3.12.0` - Mocking utilities
- `black>=23.0.0` - Code formatting
- `flake8>=6.1.0` - Linting
- `mypy>=1.7.0` - Type checking

### Utility Libraries
- `click>=8.1.0` - Command line interface
- `rich>=13.7.0` - Rich text and beautiful formatting
- `tqdm>=4.66.0` - Progress bars
- `humanize>=4.8.0` - Human-readable formatting
- `fuzzywuzzy>=0.18.0` - Fuzzy string matching
- `python-levenshtein>=0.23.0` - String similarity

## System Requirements

### Operating System
- macOS (Darwin 24.6.0) - Current system
- Python 3.13+ - As specified in pyproject.toml

### Hardware
- MacBook Pro M3 with 64GB RAM - As specified in user rules
- Sufficient storage for vector databases and logs

### External Services (Optional)
- LM Studio running on localhost:1234 - Current setup
- Email server (SMTP) for notifications
- Matrix server for messaging
- Slack workspace for notifications
- Twilio account for SMS/phone calls

## Installation Commands

```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Or using uv (if preferred)
uv pip install -r requirements.txt
```

## Configuration Files Needed

1. `.env` - Environment variables
2. `config.yaml` - Main configuration
3. `database.ini` - Database connection settings
4. `logging.yaml` - Logging configuration
5. `memory_config.json` - Memory system settings

## Key Features Implementation

### Context Management
- User profile storage in SQLite/PostgreSQL
- Time awareness using pytz and APScheduler
- Importance scoring for notifications

### Memory System
- ChromaDB for semantic memory
- SQLAlchemy for structured data
- Redis for session caching

### Communication Channels
- Email via SMTP
- Matrix messaging
- Slack integration
- Phone calls via Twilio

### Task Management
- APScheduler for scheduling
- FastAPI for web interface
- WebSocket for real-time updates

### News Monitoring
- RSS feed parsing
- ArXiv paper monitoring
- Web scraping capabilities

## Development Notes

- All logging should be centralized and robust
- Use Python virtual environment (never Conda)
- Implement integration tests over unit tests
- Maintain existing functionality while adding new features
- Use Context7 for SQLAlchemy documentation
- Prefer raw SQL over SQLAlchemy except for model definition
