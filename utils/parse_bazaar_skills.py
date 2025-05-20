# Import required libraries
from bs4 import BeautifulSoup
import sqlite3
import logging
import re
import os
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_skills.log"),
        logging.StreamHandler()
    ]
)

# Function to create database and skill-related tables
def create_database_skills():
    # Connect to SQLite database (creates file if not exists)
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Create skills table with unique constraint on name
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon_url TEXT
        )
    """)
    
    # Create skill_heroes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_heroes (
            skill_id INTEGER,
            hero TEXT NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)
    
    # Create skill_rarities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_rarities (
            skill_id INTEGER,
            rarity TEXT NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)
    
    # Create skill_effects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_effects (
            skill_id INTEGER,
            effect TEXT NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)
    
    # Create skill_types table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_types (
            skill_id INTEGER,
            type TEXT NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

# Function to clean HTML from effect text
def clean_effect_text(effect_html):
    # Convert HTML to plain text, remove extra spaces
    soup = BeautifulSoup(effect_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Function to update database with new HTML data
def update_skills_from_html(html_files, monster_html_file=None, delete_obsolete=False):
    # Connect to database
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()

    # Track processed skill names for obsolete check
    processed_names = set()
    updated_count = 0
    inserted_count = 0

    # Process skill HTML files
    for html_file in html_files:
        if not os.path.exists(html_file):
            logging.warning(f"File {html_file} not found, skipping.")
            continue

        try:
            with open(html_file, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file, "html.parser")
        except Exception as e:
            logging.error(f"Failed to read HTML file {html_file}: {e}")
            continue

        is_wiki_file = "./var/skill_w_types.html" in html_file
        logging.info(f"Parsing {'wiki' if is_wiki_file else 'mobalytics'} file: {html_file}")

        if is_wiki_file:
            # Parse skill_w_types.html (wiki format)
            skill_table = soup.find("table", class_="wikitable sortable jquery-tablesorter")
            if not skill_table:
                logging.error(f"No skill table found in {html_file}")
                continue

            skill_rows = skill_table.find("tbody").find_all("tr")
            for row in skill_rows:
                try:
                    cols = row.find_all("td")
                    if len(cols) < 5:
                        continue

                    # Extract name
                    name = cols[1].find("a").get_text(strip=True) if cols[1].find("a") else ""
                    if not name:
                        logging.warning("Skipping skill with empty name")
                        continue

                    processed_names.add(name)
                    logging.info(f"Processing skill: {name}")

                    # Extract icon URL
                    img_tag = cols[0].find("img")
                    icon_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                    if icon_url.startswith("/images/"):
                        icon_url = f"https://thebazaar.wiki{icon_url.split('?')[0]}"

                    # Extract effect
                    effect_html = str(cols[2])
                    effect = clean_effect_text(effect_html)

                    # Extract types
                    types_html = cols[4]
                    types = [font.get_text(strip=True) for font in types_html.find_all("font", color="#9aabff")]

                    # Check if skill exists
                    cursor.execute("SELECT id, icon_url FROM skills WHERE name = ?", (name,))
                    existing_skill = cursor.fetchone()

                    if existing_skill:
                        # Update existing skill
                        skill_id, old_icon_url = existing_skill
                        update_fields = []
                        update_params = []
                        if old_icon_url != icon_url:
                            update_fields.append("icon_url = ?")
                            update_params.append(icon_url)
                        if update_fields:
                            update_params.append(skill_id)
                            cursor.execute(f"UPDATE skills SET {', '.join(update_fields)} WHERE id = ?", update_params)
                            logging.info(f"Updated skill {name}: {', '.join(update_fields)}")
                        updated_count += 1

                        # Delete old related data
                        cursor.execute("DELETE FROM skill_effects WHERE skill_id = ?", (skill_id,))
                        cursor.execute("DELETE FROM skill_types WHERE skill_id = ?", (skill_id,))
                    else:
                        # Insert new skill
                        cursor.execute("INSERT INTO skills (name, icon_url) VALUES (?, ?)", 
                                     (name, icon_url))
                        skill_id = cursor.lastrowid
                        inserted_count += 1
                        logging.info(f"Inserted new skill: {name}")

                    # Insert related data
                    if effect:
                        cursor.execute("INSERT INTO skill_effects (skill_id, effect) VALUES (?, ?)", (skill_id, effect))
                        logging.info(f"Added effect for skill {name}: {effect}")
                    for skill_type in types:
                        skill_type = skill_type.replace("Reference", "").replace("SLow", "Slow").strip()
                        cursor.execute("INSERT OR IGNORE INTO skill_types (skill_id, type) VALUES (?, ?)", 
                                     (skill_id, skill_type))
                        logging.info(f"Added type for skill {name}: {skill_type}")

                except Exception as e:
                    logging.error(f"Error processing skill {name}: {e}")
                    conn.rollback()
                    continue

        else:
            # Parse skill_data.html (mobalytics format)
            skill_containers = soup.find_all("div", class_="x6ac99c x1qhigcl x1n2onr6 x1n9hxaw x25l62i xiy17q3 x19l6gds xvrka61")
            for skill in skill_containers:
                try:
                    # Extract skill name
                    name_tag = skill.find("p", class_="x1cabzks")
                    name = name_tag.get_text(strip=True) if name_tag else ""
                    if not name:
                        logging.warning("Skipping skill with empty name")
                        logging.info(name_tag)
                        continue

                    processed_names.add(name)
                    logging.info(f"Processing skill: {name}")

                    # Extract icon URL
                    icon_tag = skill.find("img", class_="x19kjcj4")
                    icon_url = icon_tag["src"] if icon_tag and "src" in icon_tag.attrs else ""

                    # Extract heroes
                    hero_tag = skill.find("p", class_="x2fl5vp x5gn1fm")
                    hero_text = hero_tag.get_text(strip=True) if hero_tag else ""
                    heroes = [h.strip() for h in hero_text.split(",") if h.strip()] if hero_text else []

                    # Extract rarities
                    rarity_group = skill.find("div", role="radiogroup")
                    rarities = [label.find("div", class_="x2lah0s").get_text(strip=True) 
                               for label in rarity_group.find_all("label")] if rarity_group else []

                    # Extract effects
                    effects_list = skill.find("ul", class_="x2fl5vp x5gn1fm x5tiur9 x1ghz6dp")
                    effects = [li.get_text(strip=True) for li in effects_list.find_all("li")] if effects_list else []

                    # Check if skill exists
                    cursor.execute("SELECT id, icon_url FROM skills WHERE name = ?", (name,))
                    existing_skill = cursor.fetchone()

                    if existing_skill:
                        # Update existing skill
                        skill_id, old_icon_url = existing_skill
                        if old_icon_url != icon_url:
                            cursor.execute("UPDATE skills SET icon_url = ? WHERE id = ?", (icon_url, skill_id))
                            logging.info(f"Updated icon_url for skill {name}: {old_icon_url} -> {icon_url}")
                        updated_count += 1

                        # Delete old related data
                        cursor.execute("DELETE FROM skill_heroes WHERE skill_id = ?", (skill_id,))
                        cursor.execute("DELETE FROM skill_rarities WHERE skill_id = ?", (skill_id,))
                        cursor.execute("DELETE FROM skill_effects WHERE skill_id = ?", (skill_id,))
                    else:
                        # Insert new skill
                        cursor.execute("INSERT INTO skills (name, icon_url) VALUES (?, ?)", (name, icon_url))
                        skill_id = cursor.lastrowid
                        inserted_count += 1
                        logging.info(f"Inserted new skill: {name}")

                    # Insert related data
                    for hero in heroes:
                        cursor.execute("INSERT OR IGNORE INTO skill_heroes (skill_id, hero) VALUES (?, ?)", 
                                     (skill_id, hero))
                        logging.info(f"Associated hero with skill {name}: {hero}")
                    for rarity in rarities:
                        cursor.execute("INSERT OR IGNORE INTO skill_rarities (skill_id, rarity) VALUES (?, ?)", 
                                     (skill_id, rarity))
                        logging.info(f"Added rarity for skill {name}: {rarity}")
                    for effect in effects:
                        cursor.execute("INSERT INTO skill_effects (skill_id, effect) VALUES (?, ?)", 
                                     (skill_id, effect))
                        logging.info(f"Added effect for skill {name}: {effect}")

                except Exception as e:
                    logging.error(f"Error processing skill {name}: {e}")
                    conn.rollback()
                    continue

    # Process monster skills
    if monster_html_file and os.path.exists(monster_html_file):
        try:
            with open(monster_html_file, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file, "html.parser")
        except Exception as e:
            logging.error(f"Failed to read monster HTML file {monster_html_file}: {e}")
        else:
            skill_table = soup.find("table", class_="wikitable sortable jquery-tablesorter")
            if not skill_table:
                logging.error(f"No skill table found in {monster_html_file}")
            else:
                count = 0
                skill_rows = skill_table.find("tbody").find_all("tr")
                for row in skill_rows:
                    try:
                        cols = row.find_all("td")
                        if len(cols) < 5:
                            continue

                        # Extract name
                        name = cols[1].find("a").get_text(strip=True) if cols[1].find("a") else ""
                        if not name:
                            logging.warning("Skipping monster skill with empty name")
                            continue

                        processed_names.add(name)
                        logging.info(f"Processing monster skill: {name}")

                        # Check if skill exists
                        cursor.execute("SELECT id FROM skills WHERE name = ?", (name,))
                        skill_id = cursor.fetchone()
                        if skill_id:
                            skill_id = skill_id[0]
                            cursor.execute("INSERT OR IGNORE INTO skill_heroes (skill_id, hero) VALUES (?, ?)", 
                                         (skill_id, "Monster"))
                            logging.info(f"Marked skill {name} as associated with 'Monster'")
                            updated_count += 1
                        else:
                            logging.warning(f"Skill {name} not found in skills table, skipping monster association")

                        count += 1
                    except Exception as e:
                        logging.error(f"Error processing monster skill {name}: {e}")
                        conn.rollback()
                        continue

                logging.info(f"Total monster skills processed: {count}")

    # Optional: Delete obsolete skills
    deleted_count = 0
    if delete_obsolete:
        cursor.execute("SELECT id, name FROM skills")
        for skill_id, name in cursor.fetchall():
            if name not in processed_names:
                cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
                deleted_count += 1
                logging.info(f"Deleted obsolete skill: {name}")

    # Commit changes
    try:
        conn.commit()
        logging.info(f"Update completed: {inserted_count} inserted, {updated_count} updated, {deleted_count} deleted")
    except Exception as e:
        logging.error(f"Failed to commit changes: {e}")
        conn.rollback()
    finally:
        conn.close()

# Main execution
if __name__ == "__main__":
    # Create database and tables
    create_database_skills()
    
    # Update database with HTML data
    html_files = ["./var/skill_w_types.html", "./var/skill_data_v2_0_0_may_8.html"]
    update_skills_from_html(html_files, monster_html_file="./var/monster_skill_data.html", delete_obsolete=False)
    
    print("Skill data updated successfully.")