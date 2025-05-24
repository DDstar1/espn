# ESPN Football Data Scraper

A Python scraper designed to extract football data from ESPN’s website and store it locally in SQLite. This tool powers data collection for the GoalGraph platform, enabling automated, data-driven sports betting insights.

---

## Features

* Scrapes football team URLs and match data from ESPN
* Stores data in SQLite to avoid duplicates and keep track of scraping progress
* Supports resuming scraping from the last saved state
* Modular scripts for fetching teams and their matches separately

---

## Tech Stack

* Python 3.x
* Selenium (HTTP requests and User interaction)
* SQLite (local data storage via `sqlite3`)

---

## Getting Started

### 1. Clone repo

```bash
git clone https://github.com/yourusername/espn-football-scraper.git
cd espn-football-scraper
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run scraper scripts

* To get the list of teams and save locally:

```bash
python main.py
```
