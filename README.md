# Micro-Polling Capstone Project

A web-based micro-polling application that lets communities submit and view opinion polls organized by zip code, city, and California school district. Built with Flask and SQLite.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
- [Running the App](#running-the-app)
- [Admin Usage](#admin-usage)
- [User Workflow](#user-workflow)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Utility Scripts](#utility-scripts)
- [Known Issues](#known-issues)
- [Default Credentials](#default-credentials)

---

## Features

- **Multiple poll types**: Single choice, multiple choice, rating scale, and ranked choice
- **Geographic targeting**: Associate polls with zip codes, cities, or California school districts
- **Admin dashboard**: Create, edit, delete, activate/deactivate polls, and export results to CSV
- **Autocomplete search**: Live suggestions for zip codes, city names, and school district names
- **School district integration**: Import California school directory data and link polls directly to districts
- **Vote results**: Results are shown to users immediately after voting
- **CSV export**: Download full poll results from the admin panel

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3, Flask                     |
| ORM        | SQLAlchemy                          |
| Database   | SQLite                              |
| Frontend   | HTML, CSS, JavaScript, Jinja2       |
| Data tools | pandas (Excel import)               |

---

## Project Structure

```
Micro-polling-capstone-project/
├── project/                      # Main application directory
│   ├── app.py                    # Flask application entry point
│   ├── model.py                  # SQLAlchemy models (Poll, Vote, Admin, ZipCode, School)
│   │
│   ├── reset.py                  # Wipe and recreate the database
│   ├── create_admin.py           # Create an admin account interactively
│   ├── import_schools.py         # Import California school/district data from Excel
│   ├── migrate.py                # Add poll_districts table to an existing database
│   ├── fix.py                    # Sync school zip codes into the zipcodes table
│   ├── check.py                  # Diagnostic script for district search
│   │
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── index.html            # Home / search page
│   │   ├── poll_v2.html          # Voting page
│   │   ├── results_v2.html       # Results display
│   │   └── admin/
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── create_poll_v2.html
│   │       ├── edit_poll_v2.html
│   │       └── poll_results.html
│   │
│   └── polling_v2.db             # SQLite database (git-ignored)
│
├── capstone/                     # Python virtual environment (git-ignored)
└── CDESchoolDirectoryExport.xlsx # California school directory source data
```

---

## Setup Guide

### Prerequisites

- Python 3.7 or higher
- pip

### Step 1 — Create and activate a virtual environment

```bash
python -m venv capstone

# Windows
./capstone/Scripts/activate

# macOS / Linux
source capstone/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install Flask SQLAlchemy pandas openpyxl
```

### Step 3 — Navigate to the project directory

```bash
cd project
```

### Step 4 — Initialize the database

```bash
# Create a fresh database with all tables
python reset.py

# Import California school and district data
python import_schools.py

# Sync school zip codes into the zipcodes table (enables zip/city search)
python fix.py

# Create the admin account
python create_admin.py
```

> **Default credentials:** username `admin`, password `12345678`.
> You will be prompted to enter your own credentials when running `create_admin.py`.
> Change the default password before deploying to any shared or public environment.

---

## Running the App

```bash
python app.py
```

The app starts at:

```
http://localhost:5000
```

Admin login page:

```
http://localhost:5000/admin/login
```

---

## Admin Usage

Log in at `/admin/login` with your admin credentials.

### Dashboard

Lists all polls with their status (active/inactive), vote count, and associated zip codes or districts.

### Create a Poll

Go to **Create Poll** in the dashboard and fill in:

| Field | Description |
|-------|-------------|
| Title | Short name for the poll |
| Question | The main question shown to voters |
| Poll Type | Single choice, multiple choice, rating scale, or ranked choice |
| Options | Answer choices (for single / multiple / ranked choice) |
| Rating Range | Min, max, and optional labels (for rating scale) |
| Zip Codes | Zip codes this poll appears under |
| Districts | School districts this poll is linked to |
| Active | Whether the poll is immediately visible to users |

### Manage Polls

From the dashboard you can:

- **View results** — vote counts and percentages per option
- **Edit** — update question, options, or geographic targeting
- **Toggle active/inactive** — show or hide the poll from users
- **Delete** — permanently remove the poll and all its votes
- **Export CSV** — download full vote records and summary statistics

---

## User Workflow

1. Go to `http://localhost:5000`
2. Type a **zip code**, **city name**, or **school district name** into the search box. Autocomplete will suggest matches as you type.
3. Select a location to see available polls.
4. Open a poll, make your selection, and submit your vote.
5. Results are displayed immediately after voting.

---

## API Endpoints

### Public Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page and search |
| GET | `/poll/<poll_id>` | View poll and voting form |
| POST | `/poll/<poll_id>/vote` | Submit a vote |
| GET | `/poll/<poll_id>/results` | View results |
| GET | `/api/autocomplete` | Autocomplete for zip codes and cities |
| GET | `/api/search-cities` | Search cities by name |
| GET | `/api/search-schools` | Search school districts by name |
| GET | `/api/get-district-zipcodes` | Get zip codes belonging to a district |

### Admin Routes (login required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/admin/login` | Admin login |
| GET | `/admin/logout` | Admin logout |
| GET | `/admin` | Admin dashboard |
| GET/POST | `/admin/poll/create` | Create a new poll |
| GET | `/admin/poll/<poll_id>` | Poll detail |
| GET/POST | `/admin/poll/<poll_id>/edit` | Edit a poll |
| POST | `/admin/poll/<poll_id>/delete` | Delete a poll |
| POST | `/admin/poll/<poll_id>/toggle` | Toggle active/inactive |
| GET | `/admin/poll/<poll_id>/export` | Export results as CSV |

---

## Database Schema

| Table | Description |
|-------|-------------|
| `polls` | Poll definitions: title, question, type, options, active status |
| `votes` | Individual vote records linked to a poll |
| `admins` | Admin users with hashed passwords |
| `zipcodes` | Zip code directory with city and state (populated by `fix.py`) |
| `schools` | California school and district directory |
| `poll_zipcodes` | Many-to-many: polls linked to zip codes |
| `poll_districts` | Many-to-many: polls linked to school districts |

> **Note:** The `zipcodes` table is populated from school data (California only).
> Run `fix.py` after `import_schools.py` to enable zip code and city search.

---

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `reset.py` | Wipe and reinitialize the database |
| `create_admin.py` | Create an admin account interactively |
| `import_schools.py` | Load `CDESchoolDirectoryExport.xlsx` into the `schools` table |
| `fix.py` | Extract zip codes from the `schools` table and sync them to `zipcodes` |
| `migrate.py` | Add the `poll_districts` table to an existing database |
| `check.py` | Interactive diagnostic: trace district → zip codes → polls |

---

## Known Issues

- **Mobile scaling**: UI layout does not scale correctly on small screens
- **No vote deduplication**: There is no mechanism to prevent a single user from voting multiple times
- **Geographic verification**: The system does not verify that a user is actually located in the zip code or district they search for
- **California only**: Zip code and city search is limited to California school zip codes

---

## Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `12345678` |

> Change the default password before deploying to any shared or public environment.
