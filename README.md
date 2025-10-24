# Kixie Powerlist RCA Dashboard

A production-ready Flask dashboard for tracking Kixie Powerlist RCA (Root Cause Analysis) metrics. This application ingests CSV data from Kixie call history, Telesign validations, and Powerlist contacts to compute weekly KPIs and provide comprehensive analytics.

## Features

- **Baseline Metrics**: Pre-change performance tracking including connect rates, answer event percentages, and cooldown analysis
- **Pilot Metrics**: NAICS Powerlist performance with configurable settings and success criteria
- **Weekly Trends**: Time series analysis with interactive charts showing call volume and disposition trends
- **Powerlist Analytics**: Detailed analysis of specific powerlists with attempt distribution and cooldown management
- **Validation Cross-Reference**: Cross-reference between validated numbers and dialed contacts with carrier performance
- **Admin Interface**: Configuration management, file uploads, and data refresh capabilities
- **Export Options**: CSV and PDF export functionality for reporting

## Tech Stack

- **Backend**: Python 3.11, Flask 2.3.3
- **Data Processing**: Pandas 2.1.1
- **Frontend**: Bootstrap 5, Chart.js
- **PDF Generation**: WeasyPrint
- **Containerization**: Docker, Docker Compose
- **Testing**: Python unittest

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Local Development

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd cc-dashboard
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements-simple.txt
   ```
   
   **Alternative quick start**:
   ```bash
   ./start.sh
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your data file paths
   ```

4. **Run the application**:
   ```bash
   flask --app app run --debug
   ```

5. **Access the dashboard**:
   Open http://localhost:5001 in your browser

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the dashboard**:
   Open http://localhost:5001 in your browser

## Data Format

The application expects CSV files with specific column structures:

### Kixie Call History
- **File**: `data/kixie_call_history.csv`
- **Columns**: Date, Time, Agent First Name, Agent Last Name, Status, Disposition, Duration, Source, To Number

### Telesign Validations
- **Files**: `data/telesign_with_live.csv`, `data/telesign_without_live.csv`
- **Columns**: phone_e164, is_reachable, risk_level, carrier, validation_type

### Powerlist Contacts
- **File**: `data/powerlist_contacts.csv`
- **Columns**: Phone Number, Connected, Attempt Count, List Name

## Configuration

Key configuration options in `.env`:

```env
# Data file paths
DATA_KIXIE=./data/kixie_call_history.csv
DATA_TELESIGN_WITH=./data/telesign_with_live.csv
DATA_TELESIGN_WITHOUT=./data/telesign_without_live.csv
DATA_POWERLIST=./data/powerlist_contacts.csv

# Operational settings
DEFAULT_DIAL_AT_A_TIME=4
DEFAULT_MAX_ATTEMPTS=10
DEFAULT_ATTEMPTS_PER_DAY=2
COOLDOWN_DAYS=14

# Pilot configuration
PILOT_LIST_NAME=NAICS
TARGET_CONNECT_UPLIFT_PCT=30
SUCCESS_CRITERIA_CONNECT_UPLIFT_PCT=25
SUCCESS_CRITERIA_VOICEMAIL_UPLIFT_PCT=15

# Display settings
TIMEZONE=Asia/Manila
```

## Metrics Explained

### Baseline Metrics
- **Connect Rate**: Percentage of calls that result in "Connected" or "Left voicemail" dispositions
- **Answer Event %**: Approximated visibility based on dial-at-a-time setting
- **Avg Attempts Lost-Race**: Average attempts for contacts not reaching connected dispositions
- **Cooldown / Day**: Number of contacts reaching max attempts threshold per day

### Pilot Metrics
- **Sample Size**: Number of unique contacts in the pilot powerlist
- **Target Connect Rate**: Expected connect rate with +30% uplift vs baseline
- **Success Criteria**: Minimum thresholds for pilot success (25% connect rate, 15% voicemail uplift)

### Data Hygiene
- **Total Validated**: Number of phone numbers validated by Telesign
- **Reachable/Invalid**: Breakdown of validation results
- **Validated & Dialed**: Percentage of validated numbers actually dialed

## API Endpoints

- `GET /` - Main dashboard
- `GET /trends` - Weekly trends analysis
- `GET /powerlist` - Powerlist analytics
- `GET /validation` - Validation cross-reference
- `GET /admin` - Admin settings
- `GET /api/baseline` - Baseline metrics API
- `GET /api/pilot` - Pilot metrics API
- `GET /api/weekly` - Weekly trends API
- `GET /api/attempts` - Attempt distribution API
- `GET /api/cooldown` - Cooldown feed API

## Testing

Run the test suite:

```bash
python -m pytest tests/
# or
python -m unittest discover tests/
```

## Project Structure

```
cc-dashboard/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes/
│   │   ├── dashboard.py
│   │   ├── trends.py
│   │   ├── powerlist.py
│   │   ├── validation.py
│   │   └── admin.py
│   ├── services/
│   │   ├── data_loader.py
│   │   ├── metrics.py
│   │   ├── validation_merge.py
│   │   └── cooldown.py
│   ├── adapters/
│   │   └── cache.py
│   └── templates/
│       ├── layouts/
│       └── dashboard/
├── data/
│   ├── kixie_call_history.csv
│   ├── telesign_with_live.csv
│   ├── telesign_without_live.csv
│   └── powerlist_contacts.csv
├── tests/
│   ├── test_metrics.py
│   └── test_validation_merge.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── env.example
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please create an issue in the repository or contact the development team.

