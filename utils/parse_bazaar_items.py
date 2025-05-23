# Import required libraries
from bs4 import BeautifulSoup
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("update_items.log"),
        logging.StreamHandler()
    ]
)

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
def create_database_items():
    # Connect to SQLite database (creates file if not exists)
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Create items table with unique constraint on name
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            size TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_heroes (
            item_id INTEGER,
            hero TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_types (
            item_id INTEGER,
            type TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_rarities (
            item_id INTEGER,
            rarity TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_effects (
            item_id INTEGER,
            effect TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enchantments (
            item_id INTEGER,
            enchantment_name TEXT NOT NULL,
            enchantment_effect TEXT NOT NULL,
            PRIMARY KEY (item_id, enchantment_name),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Function to update database with new HTML data
def update_items_from_html(html_file, delete_obsolete=False):
    # Read HTML file
    try:
        with open(html_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
    except Exception as e:
        logging.error(f"Failed to read HTML file {html_file}: {e}")
        return

    # Connect to database
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()

    # Track processed item names for obsolete check
    processed_names = set()
    updated_count = 0
    inserted_count = 0

    # Find all item containers
    item_containers = soup.find_all("div", class_="x6ac99c x1qhigcl x1n2onr6 x1n9hxaw x25l62i xiy17q3 x19l6gds xvrka61")
    logging.info(f"Found {len(item_containers)} items in HTML")

    for item in item_containers:
        try:
            # Extract item name
            name_tag = item.find("p", class_="x1cabzks")
            name = name_tag.get_text(strip=True) if name_tag else ""
            if not name:
                logging.warning("Skipping item with empty name")
                continue

            processed_names.add(name)

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
            effects_list = item.find("ul", class_="x2fl5vp x5gn1fm x5tiur9 x1ghz6dp")
            effects = [li.get_text(strip=True) for li in effects_list.find_all("li")] if effects_list else []

            # Extract enchantments
            enchantments = {}
            potential_enc_divs = item.find_all("div", recursive=True)
            for div in potential_enc_divs:
                enc_name = div.find("span", class_="x19jf9pv x1g1qkmr x1db2dqx")
                enc_effect = div.find("span", class_="x2fl5vp xqxvn2f")
                if enc_name and enc_effect:
                    enc_name_text = enc_name.get_text(strip=True)
                    enc_effect_text = enc_effect.get_text(strip=True).replace(",", " ")
                    if enc_name_text not in enchantments:
                        enchantments[enc_name_text] = enc_effect_text
                        logging.debug(f"Found enchantment for {name}: {enc_name_text} - {enc_effect_text}")

            # Ensure all enchantments are present
            for enc_name in DEFAULT_ENCHANTMENTS:
                if enc_name not in enchantments:
                    enchantments[enc_name] = DEFAULT_ENCHANTMENTS[enc_name]
                    logging.debug(f"Missing enchantment for {name}: {enc_name}. Using default: {DEFAULT_ENCHANTMENTS[enc_name]}")

            # Check if item exists
            cursor.execute("SELECT id, size FROM items WHERE name = ?", (name,))
            existing_item = cursor.fetchone()

            if existing_item:
                # Update existing item
                item_id, old_size = existing_item
                if old_size != size:
                    cursor.execute("UPDATE items SET size = ? WHERE id = ?", (size, item_id))
                    logging.info(f"Updated size for {name}: {old_size} -> {size}")
                updated_count += 1

                # Delete old related data
                cursor.execute("DELETE FROM item_heroes WHERE item_id = ?", (item_id,))
                cursor.execute("DELETE FROM item_types WHERE item_id = ?", (item_id,))
                cursor.execute("DELETE FROM item_rarities WHERE item_id = ?", (item_id,))
                cursor.execute("DELETE FROM item_effects WHERE item_id = ?", (item_id,))
                cursor.execute("DELETE FROM enchantments WHERE item_id = ?", (item_id,))
            else:
                # Insert new item
                cursor.execute("INSERT INTO items (name, size) VALUES (?, ?)", (name, size))
                item_id = cursor.lastrowid
                inserted_count += 1
                logging.info(f"Inserted new item: {name}")

            # Insert related data
            if hero:
                cursor.execute("INSERT INTO item_heroes (item_id, hero) VALUES (?, ?)", (item_id, hero))
            for type_name in types:
                cursor.execute("INSERT INTO item_types (item_id, type) VALUES (?, ?)", (item_id, type_name))
            for rarity in rarities:
                cursor.execute("INSERT INTO item_rarities (item_id, rarity) VALUES (?, ?)", (item_id, rarity))
            for effect in effects:
                cursor.execute("INSERT INTO item_effects (item_id, effect) VALUES (?, ?)", (item_id, effect))
            for enc_name, enc_effect in enchantments.items():
                cursor.execute("INSERT INTO enchantments (item_id, enchantment_name, enchantment_effect) VALUES (?, ?, ?)",
                              (item_id, enc_name, enc_effect))

        except Exception as e:
            logging.error(f"Error processing item {name}: {e}")
            conn.rollback()
            continue

    # Optional: Delete obsolete items
    deleted_count = 0
    if delete_obsolete:
        cursor.execute("SELECT id, name FROM items")
        for item_id, name in cursor.fetchall():
            if name not in processed_names:
                cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
                deleted_count += 1
                logging.info(f"Deleted obsolete item: {name}")

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
    create_database_items()
    
    # Update database with HTML data
    update_items_from_html("./var/item_data_v2_0_0_may_8.html", delete_obsolete=False)
    
    print("Data updated successfully.")