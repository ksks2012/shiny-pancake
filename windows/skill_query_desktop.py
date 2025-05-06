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
SIZE_ORDER = ["Small", "Medium", "Large"]

# Skill-related database functions
def get_rarities():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT rarity FROM skill_rarities WHERE rarity IS NOT NULL")
    rarities = [row[0] for row in cursor.fetchall()]
    conn.close()
    # Sort rarities by custom order, only including those present
    sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
    return [""] + sorted_rarities

# Function to get distinct heroes from database
def get_heroes():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT hero FROM skill_heroes WHERE hero IS NOT NULL ORDER BY hero")
    heroes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return [""] + heroes

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
        query += " AND s.id IN (SELECT skill_id FROM skill_heroes WHERE hero IN ({}) OR hero = "")".format(",".join("?" * len(heroes)))
        params.extend(heroes)
    
    query += " GROUP BY s.id"
    
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
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    skills = []
    for row in results:
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

# Item-related database functions
def get_item_rarities():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT rarity FROM item_rarities WHERE rarity IS NOT NULL")
    rarities = [row[0] for row in cursor.fetchall()]
    conn.close()
    sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
    return [""] + sorted_rarities

def get_item_types():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM item_types WHERE type IS NOT NULL ORDER BY type")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return types

def get_item_heroes():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT hero FROM item_heroes WHERE hero IS NOT NULL ORDER BY hero")
    heroes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return [""] + heroes

def get_item_sizes():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT size FROM items WHERE size IS NOT NULL ORDER BY size")
    sizes = [row[0] for row in cursor.fetchall()]
    conn.close()
    sorted_size = sorted([s for s in sizes if s in SIZE_ORDER], key=lambda x: SIZE_ORDER.index(x))
    return [""] + sorted_size

def query_items(name="", rarities=None, types=None, effect_keyword="", heroes=None, size="", sort_by="name", sort_order="ASC"):
    conn = sqlite3.connect("bazaar.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT DISTINCT i.id, i.name, i.size,
               GROUP_CONCAT(DISTINCT ir.rarity) as rarities,
               GROUP_CONCAT(DISTINCT ie.effect) as effects,
               GROUP_CONCAT(DISTINCT it.type) as types,
               GROUP_CONCAT(DISTINCT ih.hero) as heroes,
               GROUP_CONCAT(DISTINCT e.enchantment_name || ': ' || e.enchantment_effect) as enchantments
        FROM items i
        LEFT JOIN item_rarities ir ON i.id = ir.item_id
        LEFT JOIN item_effects ie ON i.id = ie.item_id
        LEFT JOIN item_types it ON i.id = it.item_id
        LEFT JOIN item_heroes ih ON i.id = ih.item_id
        LEFT JOIN enchantments e ON i.id = e.item_id
        WHERE 1=1
    """
    params = []
    
    if name:
        query += " AND i.name LIKE ?"
        params.append(f"%{name}%")
    if rarities:
        query += " AND i.id IN (SELECT item_id FROM item_rarities WHERE rarity IN ({}))".format(",".join("?" * len(rarities)))
        params.extend(rarities)
    if types:
        query += " AND i.id IN (SELECT item_id FROM item_types WHERE type IN ({}))".format(",".join("?" * len(types)))
        params.extend(types)
    if effect_keyword:
        query += " AND ie.effect LIKE ?"
        params.append(f"%{effect_keyword}%")
    if heroes:
        query += " AND (i.id IN (SELECT item_id FROM item_heroes WHERE hero IN ({})) OR i.id NOT IN (SELECT item_id FROM item_heroes))".format(",".join("?" * len(heroes)))
        params.extend(heroes)
    if size:
        query += " AND i.size = ?"
        params.append(size)
    
    query += " GROUP BY i.id"
    
    if sort_by == "name":
        query += f" ORDER BY i.name {sort_order}"
    elif sort_by == "rarity":
        query += f"""
            ORDER BY (
                MIN(
                    CASE ir.rarity
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
        query += f" ORDER BY GROUP_CONCAT(DISTINCT it.type) {sort_order}"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    items = []
    for row in results:
        effects = row["effects"] or ""
        if effects:
            soup = BeautifulSoup(effects, "html.parser")
            effects = soup.get_text(strip=True)
        
        effects_list = list(set(effects.split(","))) if effects else []
        types_list = list(set(row["types"].split(","))) if row["types"] else []
        rarities_list = sorted(
            [r for r in row["rarities"].split(",") if r] if row["rarities"] else [],
            key=lambda x: RARITY_ORDER.index(x) if x in RARITY_ORDER else len(RARITY_ORDER)
        )
        heroes_list = list(set(row["heroes"].split(","))) if row["heroes"] else []
        enchantments_list = list(set(row["enchantments"].split(","))) if row["enchantments"] else []
        
        items.append({
            "id": row["id"],
            "name": row["name"],
            "size": row["size"],
            "rarities": ", ".join(rarities_list),
            "effects": ", ".join(effects_list),
            "types": types_list,
            "heroes": heroes_list,
            "enchantments": ", ".join(enchantments_list)
        })
    
    conn.close()
    return items

# Reusable query tab class
class QueryTab:
    def __init__(self, parent, query_func, get_rarities_func, get_types_func, get_heroes_func, entity_name, get_sizes_func=None):
        self.parent = parent
        self.query_func = query_func
        self.get_rarities_func = get_rarities_func
        self.get_types_func = get_types_func
        self.get_heroes_func = get_heroes_func
        self.get_sizes_func = get_sizes_func
        self.entity_name = entity_name
        
        self.sort_by = "name"
        self.sort_order = "ASC"
        
        # Create UI elements
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)
        
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(filter_frame, text="Name:").grid(row=0, column=0, padx=5, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.name_var).grid(row=0, column=1, padx=5, sticky="ew")
        
        ttk.Label(filter_frame, text="Effect Keyword:").grid(row=1, column=0, padx=5, sticky="w")
        self.effect_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.effect_var).grid(row=1, column=1, padx=5, sticky="ew")
        
        ttk.Label(filter_frame, text="Rarity:").grid(row=2, column=0, padx=5, sticky="w")
        self.rarity_var = tk.StringVar()
        rarities = self.get_rarities_func()
        ttk.Combobox(filter_frame, textvariable=self.rarity_var, values=rarities, state="readonly").grid(row=2, column=1, padx=5, sticky="ew")
        
        ttk.Label(filter_frame, text="Hero:").grid(row=3, column=0, padx=5, sticky="w")
        self.hero_var = tk.StringVar()
        heroes = self.get_heroes_func()
        ttk.Combobox(filter_frame, textvariable=self.hero_var, values=heroes, state="readonly").grid(row=3, column=1, padx=5, sticky="ew")
        
        row_offset = 4
        if self.get_sizes_func:
            ttk.Label(filter_frame, text="Size:").grid(row=4, column=0, padx=5, sticky="w")
            self.size_var = tk.StringVar()
            sizes = self.get_sizes_func()
            ttk.Combobox(filter_frame, textvariable=self.size_var, values=sizes, state="readonly").grid(row=4, column=1, padx=5, sticky="ew")
            row_offset += 1
        
        ttk.Label(filter_frame, text="Types:").grid(row=row_offset, column=0, padx=5, sticky="nw")
        types_frame = ttk.Frame(filter_frame)
        types_frame.grid(row=row_offset, column=1, padx=5, sticky="nsew")
        canvas = tk.Canvas(types_frame, height=100)
        scrollbar = ttk.Scrollbar(types_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.type_vars = {}
        types = self.get_types_func()
        for i, type_name in enumerate(types):
            var = tk.BooleanVar()
            self.type_vars[type_name] = var
            ttk.Checkbutton(scrollable_frame, text=type_name, variable=var).grid(row=i, column=0, sticky="w")
        
        # Search and export buttons
        ttk.Button(main_frame, text="Search", command=self.update_results).grid(row=1, column=0, pady=5)
        ttk.Button(main_frame, text="Export to CSV", command=self.export_results).grid(row=2, column=0, pady=5)
        
        columns = ("name", "effects", "rarities", "types", "heroes", "enchantments")
        if self.get_sizes_func:
            columns = ("name", "size", "effects", "rarities", "types", "heroes", "enchantments")
        
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Name", command=lambda: self.sort_column("name"))
        if self.get_sizes_func:
            self.tree.heading("size", text="Size", command=lambda: self.sort_column("name"))
        self.tree.heading("effects", text="Effects", command=lambda: self.sort_column("name"))
        self.tree.heading("rarities", text="Rarities", command=lambda: self.sort_column("rarity"))
        self.tree.heading("types", text="Types", command=lambda: self.sort_column("types"))
        self.tree.heading("heroes", text="Heroes", command=lambda: self.sort_column("name"))
        self.tree.heading("enchantments", text="Enchantments", command=lambda: self.sort_column("name"))
        
        self.tree.column("name", width=150)
        if self.get_sizes_func:
            self.tree.column("size", width=80)
        self.tree.column("effects", width=300)
        self.tree.column("rarities", width=100)
        self.tree.column("types", width=200)
        self.tree.column("heroes", width=150)
        self.tree.column("enchantments", width=200)
        
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
        size = self.size_var.get() if hasattr(self, "size_var") else ""
        
        results = self.query_func(name, rarities, types, effect_keyword, heroes, size, self.sort_by, self.sort_order)
        self.current_results = results
        
        for result in results:
            values = (
                result["name"],
                result["size"],
                result["effects"],
                result["rarities"],
                ", ".join(result["types"]),
                ", ".join(result["heroes"]),
                result["enchantments"]
            ) if self.get_sizes_func else (
                result["name"],
                result["effects"],
                result["rarities"],
                ", ".join(result["types"]),
                ", ".join(result["heroes"]),
                result["enchantments"]
            )
            self.tree.insert("", "end", values=values)

    def sort_column(self, column):
        if self.sort_by == column:
            self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        else:
            self.sort_by = column
            self.sort_order = "ASC"
        self.update_results()

    def export_results(self):
        if not hasattr(self, "current_results") or not self.current_results:
            messagebox.showinfo("Export", "No results to export.")
            return
        
        filename = f"{self.entity_name.lower()}_results.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            headers = ["Name", "Size", "Effects", "Rarities", "Types", "Heroes", "Enchantments"] if self.get_sizes_func else ["Name", "Effects", "Rarities", "Types", "Heroes", "Enchantments"]
            writer.writerow(headers)
            for result in self.current_results:
                row = [
                    result["name"],
                    result["size"] if self.get_sizes_func else result["effects"],
                    result["rarities"],
                    ", ".join(result["types"]),
                    ", ".join(result["heroes"]),
                    result["enchantments"]
                ] if self.get_sizes_func else [
                    result["name"],
                    result["effects"],
                    result["rarities"],
                    ", ".join(result["types"]),
                    ", ".join(result["heroes"]),
                    result["enchantments"]
                ]
                writer.writerow(row)
        messagebox.showinfo("Export", f"Results exported to {filename}")

# Main application class
class SkillQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skill and Item Query")
        self.root.geometry("1000x600")
        
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        skills_frame = ttk.Frame(notebook)
        items_frame = ttk.Frame(notebook)
        
        notebook.add(skills_frame, text="Skills")
        notebook.add(items_frame, text="Items")
        
        self.skills_tab = QueryTab(
            skills_frame, query_skills, get_rarities, get_types, get_heroes, "Skill"
        )
        self.items_tab = QueryTab(
            items_frame, query_items, get_item_rarities, get_item_types, get_item_heroes, "Item", get_item_sizes
        )

# Main execution
if __name__ == "__main__":
    # Create indexes for performance (if not already created)
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    # Skill indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_name ON skills(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_rarity ON skill_rarities(rarity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_type ON skill_types(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_hero ON skill_heroes(hero)")
    # Item indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_name ON items(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_size ON items(size)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_rarity ON item_rarities(rarity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_type ON item_types(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_hero ON item_heroes(hero)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_enchantment_item_id ON enchantments(item_id)")
    conn.commit()
    conn.close()
    
    root = tk.Tk()
    app = SkillQueryApp(root)
    root.mainloop()