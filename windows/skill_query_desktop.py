import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from bs4 import BeautifulSoup
import logging
import csv
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to query skills with filters
def query_skills(name="", rarity="", types=None, effect_keyword="", sort_by="name", sort_order="ASC"):
    conn = sqlite3.connect("bazaar.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Base query
    query = """
        SELECT DISTINCT s.id, s.name, sr.rarity, GROUP_CONCAT(se.effect) as effects, GROUP_CONCAT(st.type) as types
        FROM skills s
        LEFT JOIN skill_rarities sr ON s.id = sr.skill_id
        LEFT JOIN skill_effects se ON s.id = se.skill_id
        LEFT JOIN skill_types st ON s.id = st.skill_id
        WHERE 1=1
    """
    params = []
    
    # Add filters
    if name:
        query += " AND s.name LIKE ?"
        params.append(f"%{name}%")
    if rarity:
        query += " AND sr.rarity = ?"
        params.append(rarity)
    if types:
        query += " AND st.type IN ({})".format(",".join("?" * len(types)))
        params.extend(types)
    if effect_keyword:
        query += " AND se.effect LIKE ?"
        params.append(f"%{effect_keyword}%")
    
    # Group by to avoid duplicates
    query += " GROUP BY s.id"
    
    # Add sorting
    if sort_by in ["name", "rarity"]:
        query += f" ORDER BY {sort_by} {sort_order}"
    
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
        
        # Split comma-separated types
        types = row["types"].split(",") if row["types"] else []
        
        skills.append({
            "id": row["id"],
            "name": row["name"],
            "rarity": row["rarity"],
            "effects": effects,
            "types": types
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
        rarities = ["", "Bronze", "Silver", "Gold", "Diamond"]
        ttk.Combobox(filter_frame, textvariable=self.rarity_var, values=rarities, state="readonly").grid(row=2, column=1, padx=5, sticky="ew")
        
        # Types checkboxes
        ttk.Label(filter_frame, text="Types:").grid(row=3, column=0, padx=5, sticky="nw")
        types_frame = ttk.Frame(filter_frame)
        types_frame.grid(row=3, column=1, padx=5, sticky="nsew")
        canvas = tk.Canvas(types_frame, height=100)
        scrollbar = ttk.Scrollbar(types_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.type_vars = {}
        types = [
            "Regen", "AmmoReference", "Weapon", "Crit", "Charge", "CritReference", "DamageReference",
            "HealthReference", "Damage", "Ammo", "Poison", "Burn", "NonWeapon", "Gold", "Health",
            "ShieldReference", "Shield", "Friend", "Aquatic", "Cooldown", "Lifesteal", "Haste", "Freeze",
            "Property", "SlowReference", "Core", "Tech", "Tool", "Value", "EconomyReference"
        ]
        for i, type_name in enumerate(types):
            var = tk.BooleanVar()
            self.type_vars[type_name] = var
            ttk.Checkbutton(scrollable_frame, text=type_name, variable=var).grid(row=i, column=0, sticky="w")
        
        # Search and export buttons
        ttk.Button(main_frame, text="Search", command=self.update_results).grid(row=1, column=0, pady=5)
        ttk.Button(main_frame, text="Export to CSV", command=self.export_results).grid(row=2, column=0, pady=5)
        
        # Results table
        # TODO: icon
        columns = ("name", "effects", "rarity", "types")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Name", command=lambda: self.sort_column("name"))
        self.tree.heading("effects", text="Effects", command=lambda: self.sort_column("name"))
        self.tree.heading("rarity", text="Rarity", command=lambda: self.sort_column("rarity"))
        self.tree.heading("types", text="Types", command=lambda: self.sort_column("name"))
        
        self.tree.column("name", width=150)
        self.tree.column("effects", width=300)
        self.tree.column("rarity", width=100)
        self.tree.column("types", width=200)
        
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
        types = [t for t, var in self.type_vars.items() if var.get()]
        effect_keyword = self.effect_var.get().strip()
        
        # Query skills
        skills = query_skills(name, rarity, types, effect_keyword, self.sort_by, self.sort_order)
        self.current_skills = skills  # Store for export
        
        # Populate table
        for skill in skills:
            self.tree.insert("", "end", values=(
                skill["name"],
                skill["effects"],
                skill["rarity"],
                ", ".join(skill["types"])
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
            writer.writerow(["Name", "Icon URL", "Effects", "Rarity", "Types"])
            for skill in self.current_skills:
                writer.writerow([
                    skill["name"],
                    skill["effects"],
                    skill["rarity"],
                    ", ".join(skill["types"])
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
    conn.commit()
    conn.close()
    
    root = tk.Tk()
    app = SkillQueryApp(root)
    root.mainloop()