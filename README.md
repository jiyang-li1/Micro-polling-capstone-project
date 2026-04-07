# Micro-Polling Capstone Project

A web-based micro-polling application that lets communities submit and view opinion polls organized by zip code, city, and school district. Built with Flask and SQLite.

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
- [Database Overview](#database-overview)
- [Utility Scripts](#utility-scripts)
- [Known Issues](#known-issues)

---

## Features

- **Multiple poll types**: Single choice, multiple choice, rating scale, and ranked choice
- **Geographic targeting**: Associate polls with zip codes, cities, or school districts
- **Admin dashboard**: Create, edit, delete, activate/deactivate polls, and export results to CSV
- **Autocomplete search**: Users can search for polls by zip code or city name with live suggestions
- **School district integration**: Import California school district data and link polls directly to districts
- **Vote results**: Results are shown to users immediately after voting
- **CSV export**: Download poll results from the admin panel

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3, Flask                     |
| ORM        | SQLAlchemy                          |
| Database   | SQLite                              |
| Frontend   | HTML, CSS, JavaScript, Jinja2       |
| Data tools | pandas (Excel/CSV import)           |

---

## Project Structure

```
Micro-polling-capstone-project/
├── project/                        # Main application directory
│   ├── main.py                     # Flask app — version 1 (zip code only)
│   ├── main_v2.py                  # Flask app — version 2 (recommended, adds districts)
│   ├── model.py                    # SQLAlchemy models for v1
│   ├── model_v2.py                 # SQLAlchemy models for v2
│   ├── models_school.py            # School/district specific models
│   │
│   ├── db_init.py                  # Initialize v1 database schema
│   ├── reset.py                    # Wipe and recreate the v2 database
│   ├── migrate_2_v2.py             # Migrate data from v1 to v2
│   │
│   ├── import_zipcode_db.py        # Import zip codes from ZIP_Locale_Detail.csv
│   ├── import_schools_v2.py        # Import school/district data from Excel
│   │
│   ├── create_admin.py             # Create admin user (v1)
│   ├── create_admin_v2.py          # Create admin user (v2)
│   ├── create_admin_school.py      # Create admin user (school version)
│   │
│   ├── fix.py                      # Data fixing utilities
│   ├── check.py                    # Diagnostic and testing script
│   ├── get_school.py               # School data query utilities
│   ├── debug.py                    # Debug helpers
│   │
│   ├── templates/                  # Jinja2 HTML templates
│   │   ├── index.html              # Home / search page
│   │   ├── poll.html               # Voting page (v1)
│   │   ├── poll_v2.html            # Voting page (v2)
│   │   ├── results_v2.html         # Results display (v2)
│   │   └── admin/
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── create_poll_v2.html
│   │       ├── edit_poll_v2.html
│   │       └── poll_detail_v2.html
│   │
│   ├── polling.db                  # SQLite database — v1 (git-ignored)
│   ├── polling_v2.db               # SQLite database — v2 (git-ignored)
│   └── polling_school.db           # SQLite database — school version (git-ignored)
│
├── capstone/                       # Python virtual environment (git-ignored)
├── CDESchoolDirectoryExport.xlsx   # California school directory data
├── ZIP_Locale_Detail.csv           # US zip code to city/state mapping
└── get_city_name.py                # Utility to extract city names from Excel
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

**For version 2 (recommended):**

```bash
# Reset and create the v2 database schema
python reset.py

# Import US zip code data (~40,000 entries)
python import_zipcode_db.py

# Import California school and district data
python import_schools_v2.py

# Create the admin account
python create_admin_v2.py
```

> The default admin credentials are **username: `admin`** and **password: `12345678`**.
> You can change these by modifying `create_admin_v2.py` before running it, or through the script's prompts if it supports interactive input.

**For version 1 (legacy):**

```bash
python db_init.py
python import_zipcode_db.py
python create_admin.py
```

---

## Running the App

```bash
# Version 2 (recommended)
python main_v2.py

# Version 1 (legacy)
python main.py
```

The app will start at:

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

The admin dashboard (`/admin`) lists all polls with their status (active/inactive), the number of votes received, and associated zip codes or districts.

### Create a Poll

Go to **Create Poll** in the dashboard. Fill in:

| Field | Description |
|-------|-------------|
| Title | Short name for the poll |
| Question | The main question displayed to voters |
| Poll Type | Single choice, multiple choice, rating scale, or ranked choice |
| Choices | Add answer options (for single/multiple choice) |
| Rating Range | Min and max values and labels (for rating scale) |
| Zip Codes | One or more zip codes this poll appears under |
| Districts | One or more school districts (v2 only) |
| Active | Whether the poll is immediately visible to users |

### Manage Polls

From the admin dashboard you can:

- **View results** — see vote counts and percentages per choice
- **Edit** — update the question, choices, or targeting
- **Toggle active/inactive** — hide or show the poll to users
- **Delete** — permanently remove the poll and its votes
- **Export CSV** — download results as a CSV file

---

## User Workflow

1. Go to `http://localhost:5000`
2. Type a **zip code**, **city name**, or **school district** into the search box. The autocomplete will suggest matches.
3. Select your location to see available polls.
4. Click on a poll, make your selection, and submit your vote.
5. Results are displayed immediately after voting.

> **Test data**: Zip codes `11111`, `22222`, `33333`, `44444`, and `55555` have pre-loaded sample polls for development testing.

---

## API Endpoints

### Public Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page and search |
| GET | `/poll/<poll_id>` | View poll and voting form |
| POST | `/poll/<poll_id>/vote` | Submit a vote |
| GET | `/api/autocomplete` | Autocomplete for zip codes and cities |
| GET | `/api/search-cities` | Search cities by name (v2) |
| GET | `/api/search-schools` | Search school districts (v2) |
| GET | `/api/get-district-zipcodes` | Get zip codes belonging to a district (v2) |

### Admin Routes (login required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/admin/login` | Admin login |
| GET | `/admin/logout` | Admin logout |
| GET | `/admin` | Admin dashboard |
| GET/POST | `/admin/poll/create` | Create a new poll |
| GET | `/admin/poll/<poll_id>` | Poll detail and results |
| GET/POST | `/admin/poll/<poll_id>/edit` | Edit a poll |
| POST | `/admin/poll/<poll_id>/delete` | Delete a poll |
| POST | `/admin/poll/<poll_id>/toggle` | Toggle active/inactive |
| GET | `/admin/poll/<poll_id>/export` | Export results as CSV |

---

## Database Overview

### Version 2 Schema

| Table | Description |
|-------|-------------|
| `polls` | Poll definitions: title, question, type, options, active status |
| `votes` | Individual vote records linked to a poll |
| `admins` | Admin users with hashed passwords |
| `zipcodes` | US zip code directory with city and state |
| `schools` | California school and district directory |
| `poll_zipcodes` | Many-to-many: polls linked to zip codes |
| `poll_districts` | Many-to-many: polls linked to districts |

---

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `reset.py` | Wipe and reinitialize the v2 database |
| `migrate_2_v2.py` | Migrate polls and votes from v1 schema to v2 |
| `import_zipcode_db.py` | Load `ZIP_Locale_Detail.csv` into the `zipcodes` table |
| `import_schools_v2.py` | Load `CDESchoolDirectoryExport.xlsx` into the `schools` table |
| `fix.py` | Patch known data inconsistencies |
| `check.py` | Run diagnostics against the database |
| `get_school.py` | Query and inspect school/district records |
| `debug.py` | Print debug info for development |

---

## Known Issues

- **Mobile scaling**: UI layout does not scale correctly on small screens
- **Orphaned votes**: Deleting a choice from an existing poll leaves vote records that reference the removed choice, causing incorrect percentage calculations (see test Poll 5)
- **No IP-based deduplication**: There is currently no mechanism to prevent a single user from voting multiple times
- **Geographic verification**: The system does not verify that a user is actually located in the zip code or district they are browsing

---

## Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `12345678` |

> Change the default password before deploying to any shared or public environment.
