# Import required libraries
from bs4 import BeautifulSoup
import sqlite3
import logging
import re
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to create database and skill-related tables
def create_database_skills():
    # Connect to SQLite database (creates file if not exists)
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Create skills table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
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
    
    # Create skill_rarities table with is_starting column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_rarities (
            skill_id INTEGER,
            rarity TEXT NOT NULL,
            is_starting BOOLEAN DEFAULT 0,
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

# Function to parse HTML and store skill data in database
def parse_and_store_skills(html_file):
    # Read HTML file
    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    # Connect to database
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Determine file type based on filename
    is_wiki_file = "./var/skill_w_types.html" in html_file
    logging.info(f"Parsing {'wiki' if is_wiki_file else 'mobalytics'} file: {html_file}")
    
    if is_wiki_file:
        # Parse skill_w_types.html (wiki format)
        skill_table = soup.find("table", class_="wikitable sortable jquery-tablesorter")
        print("skill_table", skill_table)
        if not skill_table:
            logging.error("No skill table found in ./var/skill_w_types.html")
            return
        
        skill_rows = skill_table.find("tbody").find_all("tr")
        for row in skill_rows:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue
                
            # Extract name
            name = cols[1].find("a").get_text(strip=True) if cols[1].find("a") else ""
            logging.info(f"Processing skill: {name}")
            
            # Extract icon URL
            img_tag = cols[0].find("img")
            icon_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
            if icon_url.startswith("/images/"):
                icon_url = f"https://thebazaar.wiki{icon_url.split('?')[0]}"  # Convert relative to absolute URL
            
            # Extract effect
            effect_html = str(cols[2])
            effect = clean_effect_text(effect_html)
            
            # Extract starting tier
            starting_tier = cols[3].get_text(strip=True)
            
            # Extract types
            types_html = cols[4]
            types = [font.get_text(strip=True) for font in types_html.find_all("font", color="#9aabff")]
            
            # Insert skill into database
            cursor.execute("INSERT OR IGNORE INTO skills (name, icon_url) VALUES (?, ?)", (name, icon_url))
            cursor.execute("SELECT id FROM skills WHERE name = ?", (name,))
            skill_id = cursor.fetchone()[0]
            
            # Insert effect
            if effect:
                cursor.execute("INSERT INTO skill_effects (skill_id, effect) VALUES (?, ?)", (skill_id, effect))
                logging.info(f"Added effect for skill {name}: {effect}")
            
            # Insert starting tier
            if starting_tier:
                cursor.execute("INSERT OR IGNORE INTO skill_rarities (skill_id, rarity, is_starting) VALUES (?, ?, ?)", 
                             (skill_id, starting_tier, 1))
                logging.info(f"Added starting rarity for skill {name}: {starting_tier}")
            
            # Insert types
            for skill_type in types:
                cursor.execute("INSERT OR IGNORE INTO skill_types (skill_id, type) VALUES (?, ?)", 
                             (skill_id, skill_type))
                logging.info(f"Added type for skill {name}: {skill_type}")
            
            # Heroes are not specified in skill_w_types.html; assume none for now
            logging.info(f"No heroes specified for skill {name} in wiki file")
    
    else:
        # Parse skill.html (mobalytics format)
        skill_containers = soup.find_all("div", class_="x6ac99c x1qhigcl x1n2onr6 x1n9hxaw x25l62i xiy17q3 x19l6gds x4bs4gw")
        
        for skill in skill_containers:
            # Extract skill name
            name_tag = skill.find("p", class_="x1cabzks")
            name = name_tag.get_text(strip=True) if name_tag else ""
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
            effects_list = skill.find("ul", class_="x2fl5vp x5gn1fm x5tiur9 x1q9hu08")
            effects = [li.get_text(strip=True) for li in effects_list.find_all("li")] if effects_list else []
            
            # Insert skill into database
            cursor.execute("INSERT OR IGNORE INTO skills (name, icon_url) VALUES (?, ?)", (name, icon_url))
            cursor.execute("SELECT id FROM skills WHERE name = ?", (name,))
            skill_id = cursor.fetchone()[0]
            
            # Insert heroes
            for hero in heroes:
                cursor.execute("INSERT OR IGNORE INTO skill_heroes (skill_id, hero) VALUES (?, ?)", 
                             (skill_id, hero))
                logging.info(f"Associated hero with skill {name}: {hero}")
            
            # Insert rarities
            for rarity in rarities:
                cursor.execute("INSERT OR IGNORE INTO skill_rarities (skill_id, rarity, is_starting) VALUES (?, ?, ?)", 
                             (skill_id, rarity, 0))
                logging.info(f"Added rarity for skill {name}: {rarity}")
            
            # Insert effects
            for effect in effects:
                cursor.execute("INSERT INTO skill_effects (skill_id, effect) VALUES (?, ?)", 
                             (skill_id, effect))
                logging.info(f"Added effect for skill {name}: {effect}")
            
            # No types in skill.html
            logging.info(f"No types specified for skill {name} in mobalytics file")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

# Main execution
if __name__ == "__main__":
    # Create database and tables
    create_database_skills()
    
    # Parse HTML and store data
    html_files = ["./var/skill_data.html", "./var/skill_w_types.html"]
    for html_file in html_files:
        if os.path.exists(html_file):
            parse_and_store_skills(html_file)
        else:
            logging.warning(f"File {html_file} not found, skipping.")
    
    print("Skill data parsed and stored successfully.")