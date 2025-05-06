import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from bs4 import BeautifulSoup
import logging
import csv
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define custom rarity order
RARITY_ORDER = ["Bronze", "Silver", "Gold", "Diamond", "Legendary"]

# Function to get distinct rarities from database, sorted by custom order
def get_rarities():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT rarity FROM skill_rarities WHERE rarity IS NOT NULL")
    rarities = [row[0] for row in cursor.fetchall()]
    conn.close()
    # Sort rarities by custom order, only including those present
    sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
    return [""] + sorted_rarities  # Include empty option for "All"

# Function to get distinct heroes from database
def get_heroes():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT hero FROM skill_heroes WHERE hero IS NOT NULL ORDER BY hero")
    heroes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return [""] + heroes  # Include empty option for "All"

# Function to get distinct types from database
def get_types():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM skill_types WHERE type IS NOT NULL ORDER BY type")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return types

# Function to query skills with filters
def query_skills(name="", rarities=None, types=None, effect_keyword="", heroes=None, sort_by="name", sort_order="ASC"):
    conn = sqlite3.connect("bazaar.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Base query with DISTINCT in GROUP_CONCAT and custom rarity order
    query = """
        SELECT DISTINCT s.id, s.name,
               GROUP_CONCAT(DISTINCT sr.rarity) as rarities,
               GROUP_CONCAT(DISTINCT se.effect) as effects,
               GROUP_CONCAT(DISTINCT st.type) as types,
               GROUP_CONCAT(DISTINCT sh.hero) as heroes
        FROM skills s
        LEFT JOIN skill_rarities sr ON s.id = sr.skill_id
        LEFT JOIN skill_effects se ON s.id = se.skill_id
        LEFT JOIN skill_types st ON s.id = st.skill_id
        LEFT JOIN skill_heroes sh ON s.id = sh.skill_id
        WHERE 1=1
    """
    params = []
    
    # Add filters
    if name:
        query += " AND s.name LIKE ?"
        params.append(f"%{name}%")
    if rarities:
        query += " AND s.id IN (SELECT skill_id FROM skill_rarities WHERE rarity IN ({}))".format(",".join("?" * len(rarities)))
        params.extend(rarities)
    if types:
        query += " AND s.id IN (SELECT skill_id FROM skill_types WHERE type IN ({}))".format(",".join("?" * len(types)))
        params.extend(types)
    if effect_keyword:
        query += " AND se.effect LIKE ?"
        params.append(f"%{effect_keyword}%")
    if heroes:
        query += " AND s.id IN (SELECT skill_id FROM skill_heroes WHERE hero IN ({}))".format(",".join("?" * len(heroes)))
        params.extend(heroes)
    
    # Group by to avoid duplicates
    query += " GROUP BY s.id"
    
    # Add sorting
    if sort_by == "name":
        query += f" ORDER BY s.name {sort_order}"
    elif sort_by == "rarity":
        query += f"""
            ORDER BY (
                MIN(
                    CASE sr.rarity
                        WHEN 'Bronze' THEN 1
                        WHEN 'Silver' THEN 2
                        WHEN 'Gold' THEN 3
                        WHEN 'Diamond' THEN 4
                        WHEN 'Legendary' THEN 5
                        ELSE 6
                    END
                )
            ) {sort_order}
        """
    elif sort_by == "types":
        query += f" ORDER BY GROUP_CONCAT(DISTINCT st.type) {sort_order}"
    
    # Execute query
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    # Process results
    skills = []
    for row in results:
        # Clean HTML from effects
        effects = row["effects"] or ""
        if effects:
            soup = BeautifulSoup(effects, "html.parser")
            effects = soup.get_text(strip=True)
        
        # Split and deduplicate effects, types, rarities, and heroes
        effects_list = list(set(effects.split(","))) if effects else []
        types_list = list(set(row["types"].split(","))) if row["types"] else []
        rarities_list = sorted(
            [r for r in row["rarities"].split(",") if r] if row["rarities"] else [],
            key=lambda x: RARITY_ORDER.index(x) if x in RARITY_ORDER else len(RARITY_ORDER)
        )
        heroes_list = list(set(row["heroes"].split(","))) if row["heroes"] else []
        
        skills.append({
            "id": row["id"],
            "name": row["name"],
            "rarities": ", ".join(rarities_list),
            "effects": ", ".join(effects_list),
            "types": types_list,
            "heroes": heroes_list
        })
    
    conn.close()
    return skills

# Main application class
class SkillQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skill Query")
        self.root.geometry("1000x600")
        
        # Sorting state
        self.sort_by = "name"
        self.sort_order = "ASC"
        
        # Create UI elements
        self.create_widgets()
        
        # Initial load
        self.update_results()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Name search
        ttk.Label(filter_frame, text="Skill Name:").grid(row=0, column=0, padx=5, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.name_var).grid(row=0, column=1, padx=5, sticky="ew")
        
        # Effect keyword
        ttk.Label(filter_frame, text="Effect Keyword:").grid(row=1, column=0, padx=5, sticky="w")
        self.effect_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.effect_var).grid(row=1, column=1, padx=5, sticky="ew")
        
        # Rarity dropdown
        ttk.Label(filter_frame, text="Rarity:").grid(row=2, column=0, padx=5, sticky="w")
        self.rarity_var = tk.StringVar()
        rarities = get_rarities()
        ttk.Combobox(filter_frame, textvariable=self.rarity_var, values=rarities, state="readonly").grid(row=2, column=1, padx=5, sticky="ew")
        
        # Hero dropdown
        ttk.Label(filter_frame, text="Hero:").grid(row=3, column=0, padx=5, sticky="w")
        self.hero_var = tk.StringVar()
        heroes = get_heroes()
        ttk.Combobox(filter_frame, textvariable=self.hero_var, values=heroes, state="readonly").grid(row=3, column=1, padx=5, sticky="ew")
        
        # Types checkboxes
        ttk.Label(filter_frame, text="Types:").grid(row=4, column=0, padx=5, sticky="nw")
        types_frame = ttk.Frame(filter_frame)
        types_frame.grid(row=4, column=1, padx=5, sticky="nsew")
        canvas = tk.Canvas(types_frame, height=100)
        scrollbar = ttk.Scrollbar(types_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.type_vars = {}
        types = get_types()
        for i, type_name in enumerate(types):
            var = tk.BooleanVar()
            self.type_vars[type_name] = var
            ttk.Checkbutton(scrollable_frame, text=type_name, variable=var).grid(row=i, column=0, sticky="w")
        
        # Search and export buttons
        ttk.Button(main_frame, text="Search", command=self.update_results).grid(row=1, column=0, pady=5)
        ttk.Button(main_frame, text="Export to CSV", command=self.export_results).grid(row=2, column=0, pady=5)
        
        # Results table
        columns = ("name", "effects", "rarities", "types", "heroes")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Name", command=lambda: self.sort_column("name"))
        self.tree.heading("effects", text="Effects", command=lambda: self.sort_column("name"))
        self.tree.heading("rarities", text="Rarities", command=lambda: self.sort_column("rarity"))
        self.tree.heading("types", text="Types", command=lambda: self.sort_column("types"))
        self.tree.heading("heroes", text="Heroes", command=lambda: self.sort_column("name"))
        
        self.tree.column("name", width=150)
        self.tree.column("effects", width=300)
        self.tree.column("rarities", width=100)
        self.tree.column("types", width=200)
        self.tree.column("heroes", width=150)
        
        self.tree.grid(row=3, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Scrollbar for table
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def update_results(self):
        # Clear existing results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get filter values
        name = self.name_var.get().strip()
        rarity = self.rarity_var.get()
        rarities = [rarity] if rarity else []
        types = [t for t, var in self.type_vars.items() if var.get()]
        effect_keyword = self.effect_var.get().strip()
        hero = self.hero_var.get()
        heroes = [hero] if hero else []
        
        # Query skills
        skills = query_skills(name, rarities, types, effect_keyword, heroes, self.sort_by, self.sort_order)
        self.current_skills = skills  # Store for export
        
        # Populate table
        for skill in skills:
            self.tree.insert("", "end", values=(
                skill["name"],
                skill["effects"],
                skill["rarities"],
                ", ".join(skill["types"]),
                ", ".join(skill["heroes"])
            ))

    def sort_column(self, column):
        if self.sort_by == column:
            self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        else:
            self.sort_by = column
            self.sort_order = "ASC"
        self.update_results()

    def export_results(self):
        if not hasattr(self, "current_skills") or not self.current_skills:
            messagebox.showinfo("Export", "No results to export.")
            return
        
        filename = "skill_results.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Effects", "Rarities", "Types", "Heroes"])
            for skill in self.current_skills:
                writer.writerow([
                    skill["name"],
                    skill["effects"],
                    skill["rarities"],
                    ", ".join(skill["types"]),
                    ", ".join(skill["heroes"])
                ])
        messagebox.showinfo("Export", f"Results exported to {filename}")

# Main execution
if __name__ == "__main__":
    # Create indexes for performance (if not already created)
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_name ON skills(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_rarity ON skill_rarities(rarity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_type ON skill_types(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_hero ON skill_heroes(hero)")
    conn.commit()
    conn.close()
    
    root = tk.Tk()
    app = SkillQueryApp(root)
    root.mainloop()