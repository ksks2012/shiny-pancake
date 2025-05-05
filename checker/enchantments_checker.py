import sqlite3

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

if __name__ == "__main__":
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()

    maxi_item_id = cursor.execute("SELECT MAX(id) FROM items").fetchone()[0]

    for item_id in range(1, maxi_item_id + 1):
        count = 0
        print(f"Checking item with ID {item_id} for enchantments...")
        for rows in cursor.execute("SELECT * FROM enchantments WHERE item_id = ?", (item_id,)):
            enchantment_name = rows[1]

            if enchantment_name in DEFAULT_ENCHANTMENTS:
                count += 1
            else:
                print(f"Enchantment {enchantment_name} not found in DEFAULT_ENCHANTMENTS")
                continue
        if count != 12:
            print(f"Item with ID {item_id} has {count} enchantments instead of 12.")
    