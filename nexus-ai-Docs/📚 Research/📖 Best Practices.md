## Development Best Practices

### Code Organization

#### Module Structure

```python
# Good: Clear module organization
src/
├── core/           # Business logic, no external dependencies
├── cli/           # User interface layer
├── integrations/  # External system connections
└── utils/         # Pure utility functions

# Bad: Everything in one file or unclear separation
```

#### Dependency Management

```python
# Good: Clear dependency hierarchy
# CLI -> Core -> Database
# Integrations -> Core -> Database
# Utils has no dependencies on other modules

# Bad: Circular dependencies
# Core -> CLI -> Core (creates import cycles)
```

### Database Best Practices

#### Transaction Safety

```python
# Good: Proper transaction handling
def create_goal_with_tasks(goal_data, task_list):
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            
            # Insert goal
            goal_id = cursor.execute(
                "INSERT INTO goals (...) VALUES (...)", 
                goal_data
            ).lastrowid
            
            # Insert related tasks
            for task_data in task_list:
                task_data['goal_id'] = goal_id
                cursor.execute(
                    "INSERT INTO tasks (...) VALUES (...)", 
                    task_data
                )
            
            conn.commit()
            return goal_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create goal with tasks: {e}")
            raise GoalCreationError(f"Database error: {e}")

# Bad: No transaction safety
def create_goal_with_tasks_bad(goal_data, task_list):
    goal_id = create_goal(goal_data)  # Commits immediately
    for task in task_list:
        create_task(task)  # If this fails, goal is orphaned
```

#### Data Validation

```python
# Good: Validate at database boundary
@dataclass
class Goal:
    title: str
    deadline: Optional[datetime]
    priority: int
    
    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("Goal title cannot be empty")
        
        if self.deadline and self.deadline < datetime.now():
            raise ValueError("Goal deadline cannot be in the past")
        
        if not (1 <= self.priority <= 5):
            raise ValueError("Priority must be between 1 and 5")

# Bad: No validation, corrupt data possible
```

#### Query Optimization

```python
# Good: Use indexes and efficient queries
def get_goals_with_progress():
    query = """
    SELECT 
        g.*,
        COUNT(t.id) as total_tasks,
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
    FROM goals g
    LEFT JOIN tasks t ON g.id = t.goal_id
    WHERE g.status = 'active'
    GROUP BY g.id
    ORDER BY g.priority DESC, g.deadline ASC
    """
    return execute_query(query)

# Bad: N+1 queries
def get_goals_with_progress_bad():
    goals = get_all_goals()
    for goal in goals:
        goal.progress = calculate_progress(goal.id)  # Separate query each time
```

### CLI Design Best Practices

#### User Experience Principles

```python
# Good: Clear, helpful CLI design
@click.command()
@click.argument('title')
@click.option('--deadline', '-d', type=click.DateTime(['%Y-%m-%d']), 
              help='Goal deadline in YYYY-MM-DD format')
@click.option('--priority', '-p', type=click.IntRange(1, 5), default=3,
              help='Priority level (1-5, default: 3)')
def add_goal(title, deadline, priority):
    """Add a new goal with optional deadline and priority.
    
    Examples:
        nexus goal add "Learn React"
        nexus goal add "Learn React" --deadline 2025-08-31 --priority 5
    """
    try:
        goal = create_goal(title, deadline, priority)
        click.echo(f"✅ Created goal: {goal.title} (ID: {goal.id})")
        
        if deadline:
            days_until = (deadline - datetime.now()).days
            click.echo(f"📅 Due in {days_until} days")
            
    except GoalCreationError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

# Bad: Unclear, unhelpful interface
def add_goal_bad(t, d, p):  # Unclear parameter names
    create_goal(t, d, p)     # No feedback to user
    # No error handling
```

#### Error Handling

```python
# Good: Graceful error handling with helpful messages
def handle_database_error(func):
    """Decorator for graceful database error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                click.echo("❌ Database is busy. Please try again in a moment.", err=True)
            else:
                click.echo(f"❌ Database error: {e}", err=True)
            raise click.Abort()
        except Exception as e:
            logger.exception("Unexpected error in CLI command")
            click.echo(f"❌ Unexpected error: {e}", err=True)
            raise click.Abort()
    return wrapper

# Bad: No error handling or unclear errors
def bad_error_handling():
    result = some_database_operation()  # Crashes on any error
    print(result)  # Generic error messages
```

### Integration Best Practices

#### API Integration Patterns

```python
# Good: Robust API integration
class GoogleCalendarClient:
    def __init__(self, credentials_path):
        self.credentials = self._load_credentials(credentials_path)
        self.service = None
        self._rate_limiter = RateLimiter(requests_per_minute=100)
    
    def get_events(self, start_date, end_date, max_retries=3):
        """Get calendar events with proper error handling and retries"""
        for attempt in range(max_retries):
            try:
                self._rate_limiter.wait_if_needed()
                
                if not self.service:
                    self.service = self._build_service()
                
                events = self.service.events().list(
                    calendarId='primary',
                    timeMin=start_date.isoformat(),
                    timeMax=end_date.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                return self._parse_events(events.get('items', []))
                
            except HttpError as e:
                if e.resp.status == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                elif e.resp.status == 401:  # Auth expired
                    self._refresh_credentials()
                    continue
                else:
                    logger.error(f"Calendar API error: {e}")
                    raise CalendarIntegrationError(f"Failed to fetch events: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected calendar error: {e}")
                if attempt == max_retries - 1:
                    raise CalendarIntegrationError(f"Calendar sync failed: {e}")
        
        raise CalendarIntegrationError("Max retries exceeded")

# Bad: No error handling, fragile integration
def get_events_bad(start, end):
    service = build('calendar', 'v3', credentials=creds)
    events = service.events().list(calendarId='primary').execute()
    return events['items']  # Crashes if no items or API fails
```

#### Rate Limiting and Caching

```python
# Good: Intelligent caching and rate limiting
class CachedCalendarClient:
    def __init__(self, cache_ttl_minutes=30):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.last_request_time = {}
        self.min_request_interval = timedelta(seconds=1)
    
    def get_events_cached(self, date_range):
        cache_key = f"events_{date_range[0]}_{date_range[1]}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                logger.debug(f"Using cached calendar data")
                return cached_data
        
        # Respect rate limits
        self._wait_for_rate_limit()
        
        # Fetch fresh data
        events = self._fetch_events_from_api(date_range)
        
        # Cache results
        self.cache[cache_key] = (events, datetime.now())
        
        return events

# Bad: No caching, excessive API calls
def get_events_no_cache():
    # Makes API call every time, even for same data
    return fetch_from_google_calendar()
```

### Learning and AI Best Practices

#### Data Collection Ethics

```python
# Good: Privacy-conscious data collection
class PrivacyAwareLearning:
    def __init__(self, user_consent_level='basic'):
        self.consent_level = user_consent_level
        self.data_retention_days = 365
        self.anonymization_enabled = True
    
    def collect_usage_pattern(self, event_data):
        """Collect learning data respecting privacy preferences"""
        if self.consent_level == 'none':
            return  # No data collection
        
        # Remove or hash sensitive information
        sanitized_data = self._sanitize_data(event_data)
        
        # Only collect what's needed for learning
        learning_signal = {
            'task_type': sanitized_data.get('task_type'),
            'duration': sanitized_data.get('duration'),
            'completion_quality': sanitized_data.get('satisfaction_score'),
            'context_hash': self._hash_context(sanitized_data.get('context')),
            'timestamp': datetime.now()
        }
        
        self._store_learning_signal(learning_signal)
    
    def cleanup_old_data(self):
        """Automatically remove old learning data"""
        cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
        self._delete_data_before(cutoff_date)

# Bad: Invasive data collection
def collect_everything(user_data):
    # Stores everything including sensitive personal information
    database.store(user_data)  # No privacy consideration
```

#### Model Training Best Practices

```python
# Good: Robust model training with validation
class PersonalLearningModel:
    def __init__(self, min_samples=50):
        self.min_samples = min_samples
        self.model = None
        self.confidence_threshold = 0.7
        self.validation_split = 0.2
    
    def train_duration_prediction_model(self, training_data):
        """Train duration prediction with proper validation"""
        if len(training_data) < self.min_samples:
            logger.warning(f"Insufficient data for training: {len(training_data)} < {self.min_samples}")
            return False
        
        # Split data for validation
        train_data, val_data = self._split_data(training_data, self.validation_split)
        
        # Train model
        model = self._train_model(train_data)
        
        # Validate performance
        validation_accuracy = self._validate_model(model, val_data)
        
        if validation_accuracy > self.confidence_threshold:
            self.model = model
            logger.info(f"Model trained successfully, accuracy: {validation_accuracy:.2f}")
            return True
        else:
            logger.warning(f"Model accuracy too low: {validation_accuracy:.2f}")
            return False
    
    def predict_with_confidence(self, task_features):
        """Make predictions with confidence scores"""
        if not self.model:
            return None, 0.0
        
        prediction = self.model.predict(task_features)
        confidence = self.model.predict_confidence(task_features)
        
        if confidence < self.confidence_threshold:
            logger.debug(f"Low confidence prediction: {confidence:.2f}")
        
        return prediction, confidence

# Bad: Unreliable model training
def train_model_bad(data):
    model = SomeMLModel()
    model.fit(data)  # No validation, no confidence checking
    return model     # Might be completely inaccurate
```

## Project Management Best Practices

### Documentation Practices

#### Code Documentation

```python
# Good: Comprehensive docstrings
def optimize_schedule(tasks: List[Task], constraints: ScheduleConstraints, 
                     optimization_strategy: str = 'energy_first') -> OptimizedSchedule:
    """
    Optimize task scheduling considering multiple constraints and preferences.
    
    This function implements a multi-objective optimization algorithm that balances
    energy efficiency, deadline pressure, and goal progress to create an optimal
    daily schedule.
    
    Args:
        tasks: List of tasks to be scheduled
        constraints: Time, energy, and resource constraints
        optimization_strategy: Strategy to use ('energy_first', 'deadline_first', 'balanced')
    
    Returns:
        OptimizedSchedule containing scheduled tasks with timing and rationale
    
    Raises:
        SchedulingError: If no feasible schedule can be created
        ValidationError: If input constraints are invalid
    
    Example:
        >>> tasks = [Task("Study React", duration=120, energy="high")]
        >>> constraints = ScheduleConstraints(available_hours=8)
        >>> schedule = optimize_schedule(tasks, constraints)
        >>> print(f"Schedule efficiency: {schedule.efficiency_score}")
    
    Note:
        This function may take several seconds for large task lists (>50 tasks).
        Consider using the 'quick' strategy for real-time scheduling needs.
    """
    # Implementation...

# Bad: No documentation
def opt_sched(t, c, s='ef'):  # Unclear what this does
    # Implementation with no explanation
```

#### Decision Documentation

```markdown
# Good: Document major decisions in ADR (Architecture Decision Records)

## ADR-001: Use SQLite for Local Data Storage

### Status
Accepted

### Context
Need to choose local database for storing goals, tasks, and learning data.
Options considered: SQLite, JSON files, PostgreSQL, MongoDB

### Decision
Use SQLite for local data storage

### Consequences
**Positive:**
- Zero configuration setup
- ACID transactions
- SQL query capabilities
- Python stdlib support
- Small footprint

**Negative:**
- Limited concurrent access
- No built-in replication
- Single file can be corrupted

### Implementation Notes
- Use WAL mode for better concurrency
- Implement regular backups
- Use foreign key constraints
```

### Version Control Best Practices

#### Commit Message Convention

```bash
# Good: Clear, descriptive commits
feat: implement goal decomposition algorithm with dependency tracking
fix: resolve calendar sync timeout issues during heavy load
docs: update setup instructions with troubleshooting section
test: add integration tests for goal-task relationships
refactor: extract scheduling logic into separate modules

# Bad: Unclear commits
git commit -m "fixed stuff"
git commit -m "updates"
git commit -m "wip"
```

#### Branch Strategy

```bash
# Good: Feature branch workflow
main                    # Production-ready code
├── develop            # Integration branch
├── feature/goal-mgmt  # Feature development
├── feature/calendar   # Feature development
└── hotfix/bug-123     # Critical bug fixes

# Branch naming convention
feature/short-description
bugfix/issue-number-description
hotfix/critical-issue
```

### Testing Best Practices

#### Test Organization

```python
# Good: Comprehensive test structure
tests/
├── unit/              # Fast, isolated tests
│   ├── test_goals.py
│   ├── test_tasks.py
│   └── test_scheduling.py
├── integration/       # Component interaction tests
│   ├── test_goal_task_flow.py
│   └── test_calendar_sync.py
├── end_to_end/       # Full system tests
│   └── test_daily_workflow.py
├── fixtures/         # Test data
└── conftest.py      # Shared test configuration

# Test naming convention
def test_goal_creation_with_valid_data_should_succeed():
def test_goal_creation_with_empty_title_should_raise_error():
def test_schedule_optimization_with_energy_constraints_should_respect_limits():
```

#### Test Data Management

```python
# Good: Reusable test fixtures
@pytest.fixture
def sample_goals():
    """Provide realistic test goals for various scenarios"""
    return [
        Goal(
            title="Learn React Development",
            deadline=datetime.now() + timedelta(days=60),
            priority=4,
            category="education"
        ),
        Goal(
            title="Complete Project Proposal",
            deadline=datetime.now() + timedelta(days=7),
            priority=5,
            category="work"
        )
    ]

@pytest.fixture
def mock_calendar_client():
    """Provide mock calendar client to avoid API calls in tests"""
    client = Mock(spec=GoogleCalendarClient)
    client.get_events.return_value = [
        CalendarEvent(
            title="Team Meeting",
            start_time=datetime.now() + timedelta(hours=2),
            duration=60
        )
    ]
    return client

# Bad: Hardcoded test data in each test
```

### Performance Best Practices

#### Database Performance

```python
# Good: Efficient database usage
class GoalRepository:
    def __init__(self):
        self._connection_pool = ConnectionPool(max_connections=5)
    
    def get_goals_with_recent_activity(self, days=7):
        """Efficient query with proper indexing"""
        query = """
        SELECT g.*, COUNT(tc.id) as recent_completions
        FROM goals g
        LEFT JOIN tasks t ON g.id = t.goal_id
        LEFT JOIN task_completions tc ON t.id = tc.task_id 
            AND tc.completed_at > datetime('now', '-{} days')
        WHERE g.status = 'active'
        GROUP BY g.id
        HAVING recent_completions > 0 OR g.updated_at > datetime('now', '-{} days')
        ORDER BY recent_completions DESC, g.priority DESC
        """.format(days, days)
        
        return self._execute_with_connection(query)

# Bad: Inefficient database usage
def get_goals_slow():
    goals = []
    for goal in get_all_goals():  # Load everything
        if goal.status == 'active':
            completions = get_all_completions_for_goal(goal.id)  # N+1 queries
            recent = [c for c in completions if c.date > seven_days_ago]
            if recent:
                goals.append(goal)
    return goals
```

#### Memory Management

```python
# Good: Memory-efficient processing
def process_large_dataset(data_source):
    """Process large datasets without loading everything into memory"""
    for batch in data_source.get_batches(batch_size=1000):
        processed_batch = process_batch(batch)
        yield from processed_batch
        
        # Clear batch from memory
        del batch, processed_batch

# Bad: Load everything into memory
def process_large_dataset_bad(data_source):
    all_data = data_source.get_all_data()  # Might use too much memory
    return [process_item(item) for item in all_data]
```

## Security Best Practices

### API Key Management

```python
# Good: Secure credential handling
import os
from pathlib import Path

def get_google_credentials():
    """Securely load Google API credentials"""
    # Try environment variables first (production)
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret:
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080')
        }
    
    # Fallback to credentials file (development)
    creds_file = Path.home() / '.config' / 'nexus-ai' / 'google_credentials.json'
    if creds_file.exists():
        with open(creds_file) as f:
            return json.load(f)
    
    raise CredentialsError("No Google credentials found")

# Bad: Hardcoded credentials
GOOGLE_CLIENT_ID = "123456789.apps.googleusercontent.com"  # Never do this
GOOGLE_CLIENT_SECRET = "your-secret-here"  # Security risk
```

### Input Validation

```python
# Good: Comprehensive input validation
def validate_goal_input(title: str, deadline: str, priority: str) -> tuple:
    """Validate and sanitize goal input data"""
    errors = []
    
    # Title validation
    if not title or not title.strip():
        errors.append("Goal title cannot be empty")
    elif len(title.strip()) > 200:
        errors.append("Goal title too long (max 200 characters)")
    
    # Deadline validation
    parsed_deadline = None
    if deadline:
        try:
            parsed_deadline = datetime.strptime(deadline, '%Y-%m-%d')
            if parsed_deadline < datetime.now().replace(hour=0, minute=0, second=0):
                errors.append("Deadline cannot be in the past")
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD")
    
    # Priority validation
    parsed_priority = 3  # Default
    if priority:
        try:
            parsed_priority = int(priority)
            if not (1 <= parsed_priority <= 5):
                errors.append("Priority must be between 1 and 5")
        except ValueError:
            errors.append("Priority must be a number")
    
    if errors:
        raise ValidationError(errors)
    
    return title.strip(), parsed_deadline, parsed_priority

# Bad: No validation
def create_goal_no_validation(title, deadline, priority):
    # Directly use user input without validation
    goal = Goal(title=title, deadline=deadline, priority=priority)
    save_goal(goal)  # Might store invalid data
```

## Related Notes

- [[Code Standards]] - Detailed coding conventions
- [[Testing Strategy]] - Comprehensive testing approach
- [[System Design]] - Overall architecture principles
- [[Setup Instructions]] - Implementation of these practices
- [[Bug Tracker]] - Quality assurance processes

---

_Created: {{date}} | Last Updated: {{date}}_ _Tags: #best-practices #development #quality #standards_