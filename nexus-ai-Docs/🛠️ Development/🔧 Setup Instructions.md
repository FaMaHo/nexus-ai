## Development Environment Setup

### Prerequisites

Before starting development, ensure you have:

- **Python 3.9+** (Check: `python --version`)
- **Git** (Check: `git --version`)
- **Google Account** (for Calendar API access)
- **Terminal/Command Line** access
- **Code Editor** (VS Code recommended)

### 1. Repository Setup

#### Clone and Initialize

```bash
# Clone the repository
git clone https://github.com/FaMaHo/nexus-ai.git
cd nexus-ai

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize development database
python scripts/setup.py --init-db
```

#### Project Structure Verification

After setup, your directory should look like:

```
nexus-ai/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   ├── cli/
│   ├── integrations/
│   └── utils/
├── tests/
├── data/
├── docs/
└── scripts/
```

### 2. Environment Configuration

#### Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your specific values
nano .env  # or your preferred editor
```

#### Environment Variables

```bash
# .env file content
DATABASE_PATH=./data/nexus.db
LOG_LEVEL=INFO
DEVELOPMENT_MODE=true

# Google Calendar API (setup in step 3)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/callback
GOOGLE_CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/calendar.events.readonly

# Optional: Reclaim.ai integration
RECLAIM_API_TOKEN=your_token_here

# Development settings
DEBUG=true
TESTING=false
```

### 3. Google Calendar API Setup

#### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "Nexus AI Personal Assistant"
3. Enable Google Calendar API:
    - APIs & Services → Library
    - Search "Google Calendar API"
    - Click "Enable"

#### Create OAuth 2.0 Credentials

1. APIs & Services → Credentials
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Configure OAuth consent screen (if first time):
    - User Type: External
    - App name: "Nexus AI"
    - User support email: your email
    - Scopes: Add Google Calendar API scopes
4. Create OAuth 2.0 Client ID:
    - Application type: Desktop application
    - Name: "Nexus AI CLI"
5. Download credentials JSON file
6. Place in `src/integrations/google_credentials.json`

#### Test Calendar Connection

```bash
# Test Google Calendar integration
python src/integrations/google_calendar.py --test-connection
```

### 4. Database Initialization

#### Create Database Schema

```bash
# Initialize database with schema
python -c "
from src.core.database import initialize_database
initialize_database()
print('Database initialized successfully')
"
```

#### Verify Database Setup

```bash
# Check database tables
sqlite3 data/nexus.db ".tables"

# Should show: goals, tasks, calendar_events, daily_logs, etc.
```

#### Load Sample Data (Optional)

```bash
# Load sample data for testing
python scripts/load_sample_data.py
```

### 5. CLI Installation

#### Install CLI Tool

```bash
# Install in development mode
pip install -e .

# Verify installation
nexus --version
nexus --help
```

#### Test Basic Commands

```bash
# Test basic CLI functionality (note: using singular command forms)
nexus goal list
nexus task list
nexus schedule today
nexus --help
```

### 6. Development Tools Setup

#### VS Code Configuration

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### Git Hooks Setup

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Test hooks
pre-commit run --all-files
```

### 7. Testing Setup

#### Run Test Suite

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/

# Run specific test file
pytest tests/test_goals.py -v
```

#### Test Database Setup

```bash
# Create test database
python -c "
from src.core.database import initialize_database
initialize_database('test_nexus.db')
print('Test database ready')
"
```

## Production Setup

### 1. System Requirements

#### Minimum Requirements

- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python**: 3.9+
- **RAM**: 512MB available
- **Storage**: 100MB free space
- **Network**: Internet connection for calendar sync

#### Recommended Specifications

- **RAM**: 1GB+ available
- **Storage**: 1GB+ free space
- **Python**: 3.11+ for best performance

### 2. Production Installation

#### Quick Installation Script

```bash
#!/bin/bash
# install_nexus.sh

# Download and install
curl -sSL https://raw.githubusercontent.com/yourusername/nexus-ai/main/install.sh | bash

# Or manual installation:
git clone https://github.com/yourusername/nexus-ai.git
cd nexus-ai
pip install .
```

#### System-wide Installation

```bash
# Install globally
sudo pip install nexus-ai

# Create system service (Linux/macOS)
sudo cp scripts/nexus.service /etc/systemd/system/
sudo systemctl enable nexus
sudo systemctl start nexus
```

### 3. Configuration Management

#### User Configuration Directory

```bash
# Create user config directory
mkdir -p ~/.config/nexus-ai
cp config/default_config.yaml ~/.config/nexus-ai/config.yaml

# Edit configuration
nano ~/.config/nexus-ai/config.yaml
```

#### Production Configuration

```yaml
# ~/.config/nexus-ai/config.yaml
database:
  path: "~/.local/share/nexus-ai/nexus.db"
  backup_enabled: true
  backup_frequency: "daily"

logging:
  level: "INFO"
  file: "~/.local/share/nexus-ai/nexus.log"
  max_size: "10MB"
  backup_count: 5

integrations:
  google_calendar:
    enabled: true
    sync_frequency: "hourly"
  
  reclaim_ai:
    enabled: false

security:
  encrypt_sensitive_data: true
  auto_logout_minutes: 60

performance:
  cache_size: "50MB"
  background_sync: true
```

## Troubleshooting

### Common Setup Issues

#### Python Version Issues

```bash
# Check Python version
python --version

# If Python 3.9+ not available, install via pyenv
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0
```

#### Virtual Environment Issues

```bash
# If venv creation fails
python -m pip install --upgrade pip
python -m pip install virtualenv
virtualenv venv

# Activate troubleshooting
which python  # Should point to venv/bin/python when activated
pip list       # Should show project dependencies
```

#### Database Issues

```bash
# If database creation fails
rm -f data/nexus.db  # Remove corrupted database
python scripts/setup.py --init-db --force

# Check database permissions
ls -la data/
chmod 644 data/nexus.db
```

#### Google Calendar API Issues

```bash
# Clear OAuth cache
rm -f ~/.config/nexus-ai/google_token.json

# Re-authenticate
nexus calendar setup --reauth

# Check API quotas in Google Cloud Console
```

### Performance Optimization

#### Speed Up Database Queries

```sql
-- Add indexes if missing
CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON calendar_events(start_datetime);

-- Vacuum database periodically
VACUUM;
```

#### Reduce Memory Usage

```bash
# Set memory limits in config
export NEXUS_MAX_MEMORY=256MB

# Use lightweight sync mode
nexus config set sync.mode lightweight
```

### Backup and Recovery

#### Automatic Backups

```bash
# Enable automatic backups
nexus config set backup.enabled true
nexus config set backup.frequency daily

# Manual backup
nexus backup create --compress
```

#### Recovery from Backup

```bash
# List available backups
nexus backup list

# Restore from backup
nexus backup restore backup-2025-01-15.tar.gz
```

## Development Workflow

### Daily Development Routine

#### Morning Setup

```bash
# Activate environment
source venv/bin/activate

# Pull latest changes
git pull origin main

# Update dependencies if needed
pip install -r requirements.txt

# Run tests to ensure everything works
pytest tests/ --tb=short
```

#### Before Committing

```bash
# Run linting
black src/ tests/
flake8 src/ tests/

# Run full test suite
pytest tests/ --cov=src/

# Update documentation if needed
# Commit with descriptive message
git add .
git commit -m "feat: implement goal decomposition algorithm"
```

### Code Quality Gates

#### Pre-commit Checklist

- [ ] All tests pass
- [ ] Code coverage >80%
- [ ] No linting errors
- [ ] Documentation updated
- [ ] [[Bug Tracker]] checked for related issues

#### Release Checklist

- [ ] All features implemented per [[Development Timeline]]
- [ ] No critical bugs in [[Bug Tracker]]
- [ ] Performance tests pass
- [ ] Documentation complete
- [ ] Backup/restore tested

## Related Notes

- [[Development Timeline]] - What to build and when
- [[Code Standards]] - Coding conventions and practices
- [[Testing Strategy]] - How to test the system
- [[Deployment Plan]] - How to deploy and distribute
- [[Bug Tracker]] - Known issues and solutions

---

_Created: {{date}} | Last Updated: {{date}}_ _Tags: #setup #installation #configuration #development_