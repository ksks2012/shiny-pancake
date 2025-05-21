# Bazaar Data Manager

## Introduction

Bazaar Data Manager is a desktop application designed to manage and analyze game-related data, including skills, items, and videos, for a game environment (e.g., a game like "The Bazaar"). It provides a user-friendly graphical interface built with Tkinter, a SQLite database for data storage, and tools for parsing game data from external sources (e.g., HTML pages). The application supports advanced filtering, searching, and management of game assets, making it an essential tool for game analysts, content creators, or players.

The program integrates data parsing scripts to extract skills and items from external sources, a robust database layer for persistent storage, and a modular GUI for managing and visualizing data. It also includes features for checking enchantments and handling video metadata, such as local file paths.

## Features

- **Data Management**:
  - Manage skills, items, and videos with CRUD (Create, Read, Update, Delete) operations.
  - Store and retrieve detailed metadata, including names, types, rarities, and associated heroes.
  - Support for video metadata, including title, type, date, status, description, and local file paths.
- **Graphical User Interface**:
  - Built with Tkinter and ttk for a modern, responsive UI.
  - Features tabs for managing different data types (e.g., `VideoTab` for videos).
  - Advanced search and filtering with customizable criteria (e.g., type, status, skills, items, heroes).
  - Date picker for video dates and listbox for hero selection.
- **Data Parsing**:
  - Parse skill and item data from external sources (e.g., Mobalytics HTML pages) using scripts like `parse_bazaar_skills.py` and `parse_bazaar_items.py`.
  - Handle structured data extraction with BeautifulSoup or similar libraries.
- **Database Integration**:
  - Uses SQLite for lightweight, file-based storage.
  - Modular database routines (`db_routine.py`) for executing queries and managing connections.
  - Separate modules for skills (`skills.py`), items (`items.py`), and videos (`videos.py`) with tailored database operations.
- **Enchantment Checking**:
  - Includes `enchantments_checker.py` for validating or analyzing enchantment data.
- **Configuration and Utilities**:
  - Centralized configuration management via `config.py`.
  - JSON-based rarity rates (`rarity_rate.json`) for reference data.
- **Extensibility**:
  - Modular structure with clear separation of concerns (UI, database, utilities).
  - Easy to extend with new data types or parsing scripts.

## Project Structure

The project is organized into several directories, each serving a specific purpose. Below is the directory structure with descriptions of key files and folders:

```
├── checker
│   └── enchantments_checker.py
│       # Script for checking or validating enchantment data, likely used for game asset analysis.
├── db
│   ├── db_routine.py
│   │   # Core database routines for SQLite connection management and query execution.
│   ├── items.py
│   │   # Database operations for managing items (e.g., querying, adding, updating).
│   ├── skills.py
│   │   # Database operations for managing skills (e.g., querying, adding, updating).
│   └── videos.py
│       # Database operations for managing videos, including title, type, date, status, description, and local_path.
├── etc
│   └── rarity_rate.json
│       # JSON file containing rarity rates or probabilities for skills/items, used for reference or validation.
├── setup.py
│   ├── dependency_links.txt
│   │   # List of dependency URLs for setup.
│   ├── PKG-INFO
│   │   # Metadata for the Python package (e.g., name, version, description).
│   ├── requires.txt
│   │   # List of Python dependencies required by the project.
│   ├── SOURCES.txt
│   │   # List of source files included in the package.
│   └── top_level.txt
│       # List of top-level modules or packages in the project.
├── ui
│   ├── filter_widgets.py
│   │   # Custom Tkinter widgets for filtering data (e.g., comboboxes, entries).
│   ├── search_popup.py
│   │   # Implementation of a search popup window for selecting skills, items, or other data.
│   ├── skill_query_desktop.py
│   │   # Main desktop application logic, likely orchestrating the GUI and tabs.
│   └── tabs
│       # Directory containing tab-specific UI modules (e.g., VideoTab.py for video management).
├── utils
│   ├── config.py
│   │   # Configuration management (e.g., database paths, parsing settings).
│   ├── parse_bazaar_items.py
│   │   # Script for parsing item data from external sources (e.g., Mobalytics HTML).
│   ├── parse_bazaar_skills.py
│   │   # Script for parsing skill data, extracting names like "Adaptive Ordinance".
│   └── parse_data.py
│       # General-purpose data parsing utilities, possibly shared by skills and items parsers.
```

### Key Components

- **checker/enchantments_checker.py**: Validates enchantment data, ensuring consistency or correctness for game assets.
- **db/**: Manages SQLite database interactions:
  - `db_routine.py`: Provides a `DBRoutine` class for connection pooling and query execution.
  - `skills.py`, `items.py`, `videos.py`: Handle specific data types with tailored SQL queries.
- **etc/rarity_rate.json**: Stores static data for rarity probabilities, used in parsing or validation.
- **ui/**: Implements the Tkinter-based GUI:
  - `skill_query_desktop.py`: Likely the main entry point for the application.
  - `search_popup.py`: A reusable popup for advanced search/selection of skills or items.
  - `filter_widgets.py`: Custom widgets for filtering data in the UI.
  - `tabs/`: Contains modules like `VideoTab.py` for managing specific data views.
- **utils/**: Provides supporting functionality:
  - `parse_bazaar_skills.py`, `parse_bazaar_items.py`: Extract data from external sources.
  - `config.py`: Centralizes configuration settings.
  - `parse_data.py`: Shared parsing utilities.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd bazaar-data-manager
   ```

2. **Install Dependencies**:
   Ensure Python 3.8+ is installed, then install required packages:
   ```bash
   pip install -r setup.py/requires.txt
   ```
   Key dependencies include:
   - `tkinter` (usually included with Python)
   - `tkcalendar` (for date picker in UI)
   - `beautifulsoup4` (for HTML parsing)
   - `sqlite3` (for database operations)

3. **Database Setup**:
   - The application uses a SQLite database (e.g., `bazaar.db`).
   - Initialize the database by running the application or manually executing schema scripts in `db/`.
   - Apply migrations if needed:
     ```sql
     ALTER TABLE videos ADD COLUMN local_path TEXT;
     ```

4. **Run the Application**:
   ```bash
   python ui/skill_query_desktop.py
   ```

## Usage

1. **Launch the Application**:
   - Run `ui/skill_query_desktop.py` to open the GUI.
   - The interface includes tabs for managing skills, items, and videos.

2. **Manage Videos**:
   - Navigate to the Videos tab.
   - **Add a Video**:
     - Enter details (title, type, date, status, description, local path).
     - Select associated skills, items, and heroes.
     - Click "Add Video".
   - **Edit a Video**:
     - Select a video from the table.
     - Modify fields, including the local file path.
     - Click "Update Selected".
   - **Delete a Video**:
     - Select a video and click "Delete Selected".
   - **Filter Videos**:
     - Use filters (type, status, skills, items, heroes) to narrow down results.

3. **Parse Data**:
   - Run `parse_bazaar_skills.py` or `parse_bazaar_items.py` to extract data from external sources (e.g., Mobalytics HTML).
   - Example:
     ```bash
     python utils/parse_bazaar_skills.py
     ```
   - Parsed data is stored in the database via `skills.py` or `items.py`.

4. **Check Enchantments**:
   - Use `enchantments_checker.py` to validate enchantment data:
     ```bash
     python checker/enchantments_checker.py
     ```

## Development

### Adding New Features
- **New Data Types**:
  - Create a new module in `db/` (e.g., `new_type.py`) with database operations.
  - Add a corresponding tab in `ui/tabs/`.
- **New Parsers**:
  - Extend `utils/` with new parsing scripts, following the pattern of `parse_bazaar_skills.py`.
- **UI Enhancements**:
  - Add widgets to `filter_widgets.py` or create new popups in `search_popup.py`.

### Database Migrations
- Use `db_routine.py` to execute schema changes.
- Example migration for adding `local_path`:
  ```python
  self.db.execute("ALTER TABLE videos ADD COLUMN local_path TEXT")
  ```

### Testing
- **Unit Tests**:
  - Add tests for database operations in `db/` (e.g., test `VideoDB.add_video`).
  - Example:
    ```python
    import unittest
    from db.db_routine import DBRoutine
    from db.videos import VideoDB

    class TestVideoDB(unittest.TestCase):
        def setUp(self):
            self.db = DBRoutine("test.db")
            self.video_db = VideoDB(self.db)
            self.db.execute("CREATE TABLE videos (id INTEGER PRIMARY KEY, title TEXT, type TEXT, date TEXT, status TEXT, description TEXT, local_path TEXT)")

        def test_add_video(self):
            self.video_db.add_video("Test", "Short", "2025-05-18", "Draft", "Desc", [], [], [], "C:/test.mp4")
            videos = self.video_db.get_videos()
            self.assertEqual(videos[0]["local_path"], "C:/test.mp4")
    ```
- **Manual Testing**:
  - Test UI interactions (add/edit/delete videos).
  - Verify parsed data in the database.

## DB Migration

- Generate Alembic Migration
  ```
    alembic revision --autogenerate -m "{message}"
  ```

- Apply Migration
  ```
    alembic upgrade head
  ```