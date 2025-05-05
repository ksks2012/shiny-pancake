from parse_bazaar_items import create_database_items, parse_and_store_items
from parse_bazaar_skills import create_database_skills, parse_and_store_skills

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    create_database_items()
    create_database_skills()

    # Parse HTML and store item data
    parse_and_store_items("./var/item_data.html")
    
    print("Data parsed and stored successfully.")

    # Parse HTML and store data
    html_files = ["./var/skill_w_types.html", "./var/skill_data.html"]
    for html_file in html_files:
        if os.path.exists(html_file):
            parse_and_store_skills(html_file)
        else:
            logging.warning(f"File {html_file} not found, skipping.")
    
    print("Skill data parsed and stored successfully.")