# Crypto Jobs Database

A personal SQLite database to track crypto/web3 job postings, with a focus on jobs that require or prefer SQL skills. This is both a practical tool for job searching and a portfolio project demonstrating database design skills.

## How It Works

```
+------------------+     +-------------------+     +------------------+
|                  |     |                   |     |                  |
|   PERPLEXITY     |     |    DISCOVERED     |     |   MAIN JOBS      |
|      API         |     |      JOBS         |     |     TABLE        |
|                  |     |    (staging)      |     |                  |
+--------+---------+     +--------+----------+     +--------+---------+
         |                        |                         |
         | search                 | review                  | track
         v                        v                         v
+--------+---------+     +--------+----------+     +--------+---------+
|                  |     |                   |     |                  |
|  discover run    +---->+  discover review  +---->+   job list       |
|                  |     |  discover promote |     |   job view       |
|  "Find crypto    |     |  discover dismiss |     |   job tag        |
|   SQL jobs..."   |     |                   |     |                  |
+------------------+     +-------------------+     +--------+---------+
                                                            |
                                                            | apply
                                                            v
+------------------+     +-------------------+     +--------+---------+
|                  |     |                   |     |                  |
|    REPORTS       |<----+   INTERVIEWS      |<----+  APPLICATIONS    |
|                  |     |                   |     |                  |
|  report summary  |     |  interview add    |     |  application add |
|  report pipeline |     |  interview list   |     |  application list|
|  report skills   |     |  interview outcome|     |  application     |
|  report unapplied|     |                   |     |    update        |
+------------------+     +-------------------+     +------------------+


                         DATA FLOW DIAGRAM

    +-------------+          +-----------+          +-------------+
    |             |   1:N    |           |   N:M    |             |
    |  COMPANIES  +--------->+   JOBS    +<-------->+   SKILLS    |
    |             |          |           |          |             |
    +-------------+          +-----+-----+          +-------------+
                                   |
                                   | 1:N
                                   v
                            +------+------+
                            |             |
                            | APPLICATIONS|
                            |             |
                            +------+------+
                                   |
                                   | 1:N
                                   v
                            +------+------+
                            |             |
                            | INTERVIEWS  |
                            |             |
                            +-------------+
```

## Features

### Phase 1 (Complete)
- **Company Management**: Add, view, edit, and list crypto/web3 companies
- **Job Tracking**: Track job postings linked to companies with skill tagging
- **Application Tracking**: Log applications with flexible status workflow
- **Interview Logging**: Track interviews per application with outcomes
- **Reports**: Analyze your job pipeline, skills demand, and unapplied jobs

### Phase 2 (Complete)
- **Automated Job Discovery**: Use Perplexity API to find SQL-focused crypto jobs
- **Review Workflow**: Stage, review, promote, or dismiss discovered jobs
- **Deduplication**: Automatically skip jobs already in the database

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | SQLite | Simple, portable, no server, great for learning |
| Language | Python 3.9+ | Readable, good libraries |
| CLI Framework | Click | Mature, well-documented |
| API | Perplexity sonar | Online search with current job listings |

## Project Structure

```
crypto-jobs-tracker/
├── README.md
├── requirements.txt
├── .env                        # API key (gitignored)
├── .env.example
├── .gitignore
├── crypto_jobs.db              # SQLite database (gitignored)
├── src/
│   ├── db/
│   │   ├── schema.sql          # Table definitions
│   │   ├── seed.sql            # Initial skills data
│   │   ├── connection.py       # DB connection helper
│   │   ├── models.py           # Dataclasses
│   │   └── queries.py          # CRUD functions
│   ├── cli/
│   │   ├── main.py             # CLI entry point
│   │   ├── company.py          # Company commands
│   │   ├── job.py              # Job commands
│   │   ├── application.py      # Application commands
│   │   ├── interview.py        # Interview commands
│   │   ├── reports.py          # Report commands
│   │   └── discover.py         # Discovery commands
│   └── discovery/
│       ├── perplexity.py       # API client
│       └── parser.py           # Response parser
├── scripts/
│   └── init_db.py              # Database initialization
└── tests/
```

## Database Schema

7 tables with proper relationships:

- **companies**: Company info (name, website, sector, chain_focus, size)
- **jobs**: Job postings linked to companies
- **skills**: Skill catalog (pre-seeded with SQL-related skills)
- **job_skills**: Many-to-many junction (required vs nice-to-have)
- **applications**: Your applications with flexible status workflow
- **interviews**: Interview records per application
- **discovered_jobs**: Staging table for API-discovered jobs

## Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python scripts/init_db.py
   ```
4. (Optional) Set up Perplexity API for job discovery:
   ```bash
   cp .env.example .env
   # Edit .env and add your PERPLEXITY_API_KEY
   ```

## Usage

### Quick Start

```bash
# Show all commands
python -m src.cli.main --help

# See your dashboard
python -m src.cli.main report summary
```

### Company Commands

```bash
python -m src.cli.main company add          # Add new company (interactive)
python -m src.cli.main company list         # List all companies
python -m src.cli.main company view 1       # View company details
python -m src.cli.main company edit 1       # Edit company
```

### Job Commands

```bash
python -m src.cli.main job add              # Add new job (interactive)
python -m src.cli.main job list             # List all jobs
python -m src.cli.main job list --sql       # List jobs requiring SQL
python -m src.cli.main job list --status open
python -m src.cli.main job view 1           # View job details
python -m src.cli.main job tag 1            # Manage skills for a job
```

### Application Commands

```bash
python -m src.cli.main application add      # Log new application
python -m src.cli.main application list     # List all applications
python -m src.cli.main application list --status applied
python -m src.cli.main application view 1   # View application details
python -m src.cli.main application update 1 # Update status
```

### Interview Commands

```bash
python -m src.cli.main interview add        # Log new interview
python -m src.cli.main interview list       # List all interviews
python -m src.cli.main interview view 1     # View interview details
python -m src.cli.main interview outcome 1  # Record outcome
```

### Report Commands

```bash
python -m src.cli.main report summary       # Overall dashboard
python -m src.cli.main report pipeline      # Application status breakdown
python -m src.cli.main report skills        # Most in-demand skills
python -m src.cli.main report unapplied     # Jobs you haven't applied to
python -m src.cli.main report sql-matches   # Jobs requiring SQL
```

### Discovery Commands (Perplexity API)

```bash
python -m src.cli.main discover run         # Search for new jobs
python -m src.cli.main discover run -q "custom search query"
python -m src.cli.main discover list        # List all discovered jobs
python -m src.cli.main discover review      # Review pending jobs
python -m src.cli.main discover view 1      # View discovered job
python -m src.cli.main discover promote 1   # Add to main jobs table
python -m src.cli.main discover dismiss 1   # Mark as not interested
```

## Example Workflow

### Manual Job Tracking

```bash
# 1. Add a company you found
python -m src.cli.main company add
# Enter: Uniswap, https://uniswap.org, DeFi, Ethereum, startup

# 2. Add a job posting
python -m src.cli.main job add
# Select company, enter job details

# 3. Tag the job with required skills
python -m src.cli.main job tag 1
# Add: SQL (required), Python (nice-to-have)

# 4. Log your application
python -m src.cli.main application add
# Select job, enter resume version

# 5. Update when you hear back
python -m src.cli.main application update 1
# Change status to: screening, interview, offer, rejected...

# 6. Log interviews
python -m src.cli.main interview add
# Select application, set type and date

# 7. Check your pipeline
python -m src.cli.main report summary
```

### Automated Job Discovery

```bash
# 1. Run a search (requires API key in .env)
python -m src.cli.main discover run
# Output: "New jobs found: 10"

# 2. Review what was found
python -m src.cli.main discover review

# 3. View a job that looks interesting
python -m src.cli.main discover view 5

# 4. Promote it to your main tracking
python -m src.cli.main discover promote 5
# Creates company if needed, adds to jobs table

# 5. Dismiss jobs you're not interested in
python -m src.cli.main discover dismiss 3
```

## Application Status Workflow

```
applied --> screening --> interview --> offer
                |             |           |
                +------+------+           |
                       |                  |
                       v                  v
                   rejected           accepted
                       |
                       v
                   ghosted / withdrawn
```

Statuses are flexible - you can move between any status (real job hunting is messy).

## Key Design Decisions

1. **SQLite**: Perfect for single-user, local, portable database
2. **Flexible status workflow**: Any status to any status transitions allowed
3. **Free text for chain_focus**: Simpler than normalized chains table
4. **Interactive prompts**: Better UX for data entry
5. **URL as dedupe key**: Prevents duplicate job entries
6. **Store raw API response**: Helps debug parsing issues
7. **Staging table for discovered jobs**: Review before adding to main table

## Environment Variables

Create a `.env` file in the project root:

```bash
# Required for job discovery feature
PERPLEXITY_API_KEY=pplx-your-api-key-here
```

Get your API key from [Perplexity AI](https://www.perplexity.ai/).

## License

Personal project for learning purposes.
