# Import required libraries
from bs4 import BeautifulSoup
import sqlite3

# Define default enchantment effects for missing enchantments
DEFAULT_ENCHANTMENTS = {
    "Heavy": "None",
    "Icy": "None",
    "Turbo": "None",
    "Shielded": "None",
    "Restorative": "None",
    "Toxic": "None",
    "Fiery": "None",
    "Shiny": "None",
    "Deadly": "None",
    "Radiant": "None",
    "Obsidian": "None",
    "Golden": "None",
}

# Function to create database and tables
def create_database():
    # Connect to SQLite database (creates file if not exists)
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Create items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hero TEXT NOT NULL,
            size TEXT NOT NULL
        )
    """)
    
    # Create item_types table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_types (
            item_id INTEGER,
            type TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Create item_rarities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_rarities (
            item_id INTEGER,
            rarity TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Create item_effects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_effects (
            item_id INTEGER,
            effect TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Create enchantments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enchantments (
            item_id INTEGER,
            enchantment_name TEXT NOT NULL,
            enchantment_effect TEXT NOT NULL,
            PRIMARY KEY (item_id, enchantment_name),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

# Function to parse HTML and store data in database
def parse_and_store(html_file):
    # Read HTML file
    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    # Connect to database
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Find all item containers
    item_containers = soup.find_all("div", class_="x6ac99c x1qhigcl x1n2onr6 x1n9hxaw x25l62i xiy17q3 x19l6gds x4bs4gw")
    
    for item in item_containers:
        # Extract item name
        name_tag = item.find("p", class_="x1cabzks")
        name = name_tag.get_text(strip=True) if name_tag else ""
        
        # Extract hero
        hero_tag = item.find("p", class_="x2fl5vp x5gn1fm")
        hero = hero_tag.get_text(strip=True) if hero_tag else ""
        
        # Extract size and types
        size_types = item.find_all("div", class_="x1x4sc3n x5gn1fm xmpun7n x19l6gds x1m59ps7 x78zum5 xl56j7k x6s0dn4 x1jnr06f x1xq1gxn xxk0z11")
        size = size_types[0].get_text(strip=True) if size_types else ""
        types = [t.get_text(strip=True) for t in size_types[1:]] if len(size_types) > 1 else []
        
        # Extract rarities
        rarity_group = item.find("div", role="radiogroup")
        rarities = [label.find("div", class_="x2lah0s").get_text(strip=True) for label in rarity_group.find_all("label")] if rarity_group else []
        
        # Extract effects
        effects_list = item.find("ul", class_="x2fl5vp x5gn1fm x5tiur9 x1q9hu08")
        effects = [li.get_text(strip=True) for li in effects_list.find_all("li")] if effects_list else []
        
        # Extract enchantments
        enchantments = {}
        # Find all divs that might contain enchantments
        potential_enc_divs = item.find_all("div", recursive=True)
        for div in potential_enc_divs:
            enc_name = div.find("span", class_="x19jf9pv x1g1qkmr x1db2dqx")
            enc_effect = div.find("span", class_="x2fl5vp xqxvn2f")
            if enc_name and enc_effect:
                enc_name_text = enc_name.get_text(strip=True)
                enc_effect_text = enc_effect.get_text(strip=True)
                if enc_name_text not in enchantments:
                    enchantments[enc_name_text] = enc_effect_text
                    print(f"Found enchantment for {name}: {enc_name_text} - {enc_effect_text}")
        
        # Ensure all enchantments are present
        for enc_name in DEFAULT_ENCHANTMENTS:
            if enc_name not in enchantments:
                enchantments[enc_name] = DEFAULT_ENCHANTMENTS[enc_name]
                print(f"Missing enchantment for {name}: {enc_name}. Using default: {DEFAULT_ENCHANTMENTS[enc_name]}")
        
        # Insert item into database
        cursor.execute("INSERT INTO items (name, hero, size) VALUES (?, ?, ?)", (name, hero, size))
        item_id = cursor.lastrowid
        
        # Insert types
        for type_name in types:
            cursor.execute("INSERT INTO item_types (item_id, type) VALUES (?, ?)", (item_id, type_name))
        
        # Insert rarities
        for rarity in rarities:
            cursor.execute("INSERT INTO item_rarities (item_id, rarity) VALUES (?, ?)", (item_id, rarity))
        
        # Insert effects
        for effect in effects:
            cursor.execute("INSERT INTO item_effects (item_id, effect) VALUES (?, ?)", (item_id, effect))
        
        # Insert enchantments
        for enc_name, enc_effect in enchantments.items():
            cursor.execute("INSERT INTO enchantments (item_id, enchantment_name, enchantment_effect) VALUES (?, ?, ?)",
                          (item_id, enc_name, enc_effect))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

# Main execution
if __name__ == "__main__":
    # Create database and tables
    create_database()
    
    # Parse HTML and store item data
    parse_and_store("./var/item_data.html")
    
    print("Data parsed and stored successfully.")