from bs4 import BeautifulSoup
from datetime import datetime
from tkinter import ttk, messagebox

import tkinter as tk
import sqlite3
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

# Video-related database functions
def get_videos(video_type="", status="", skill_name="", item_name="", sort_by="date", sort_order="DESC"):
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    query = """
        SELECT v.id, v.title, v.type, v.date, v.status, v.description,
               GROUP_CONCAT(DISTINCT s.name) as skills,
               GROUP_CONCAT(DISTINCT i.name) as items
        FROM videos v
        LEFT JOIN video_skills vs ON v.id = vs.video_id
        LEFT JOIN skills s ON vs.skill_id = s.id
        LEFT JOIN video_items vi ON v.id = vi.video_id
        LEFT JOIN items i ON vi.item_id = i.id
        WHERE 1=1
    """
    params = []
    
    if video_type:
        query += " AND v.type = ?"
        params.append(video_type)
    if status:
        query += " AND v.status = ?"
        params.append(status)
    if skill_name:
        query += " AND v.id IN (SELECT video_id FROM video_skills WHERE skill_id IN (SELECT id FROM skills WHERE name LIKE ?))"
        params.append(f"%{skill_name}%")
    if item_name:
        query += " AND v.id IN (SELECT video_id FROM video_items WHERE item_id IN (SELECT id FROM items WHERE name LIKE ?))"
        params.append(f"%{item_name}%")
    
    query += " GROUP BY v.id"
    query += f" ORDER BY v.{sort_by} {sort_order}"
    
    cursor.execute(query, params)
    videos = [
        {
            "id": row[0],
            "title": row[1],
            "type": row[2],
            "date": row[3],
            "status": row[4],
            "description": row[5],
            "skills": row[6] or "",
            "items": row[7] or ""
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return videos

def add_video(title, video_type, date, status, description, skill_ids, item_ids):
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Insert video
    cursor.execute("INSERT INTO videos (title, type, date, status, description) VALUES (?, ?, ?, ?, ?)",
                  (title, video_type, date, status, description))
    video_id = cursor.lastrowid
    
    # Insert skill tags
    for skill_id in skill_ids:
        cursor.execute("INSERT INTO video_skills (video_id, skill_id) VALUES (?, ?)", (video_id, skill_id))
    
    # Insert item tags
    for item_id in item_ids:
        cursor.execute("INSERT INTO video_items (video_id, item_id) VALUES (?, ?)", (video_id, item_id))
    
    conn.commit()
    conn.close()

def update_video(video_id, title, video_type, date, status, description, skill_ids, item_ids):
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    
    # Update video
    cursor.execute("UPDATE videos SET title = ?, type = ?, date = ?, status = ?, description = ? WHERE id = ?",
                  (title, video_type, date, status, description, video_id))
    
    # Delete existing tags
    cursor.execute("DELETE FROM video_skills WHERE video_id = ?", (video_id,))
    cursor.execute("DELETE FROM video_items WHERE video_id = ?", (video_id,))
    
    # Insert new skill tags
    for skill_id in skill_ids:
        cursor.execute("INSERT INTO video_skills (video_id, skill_id) VALUES (?, ?)", (video_id, skill_id))
    
    # Insert new item tags
    for item_id in item_ids:
        cursor.execute("INSERT INTO video_items (video_id, item_id) VALUES (?, ?)", (video_id, item_id))
    
    conn.commit()
    conn.close()

def delete_video(video_id):
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))  # Cascades to video_skills and video_items
    conn.commit()
    conn.close()

def get_all_skills():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM skills ORDER BY name")
    skills = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()
    return skills

def get_all_items():
    conn = sqlite3.connect("bazaar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM items ORDER BY name")
    items = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()
    return items

# Video management tab
class VideoTab:
    def __init__(self, parent):
        self.parent = parent
        self.skills = get_all_skills()
        self.items = get_all_items()
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.grid(row=0, column=0, sticky="ew", pady=5)

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=0, padx=5, sticky="w")
        self.type_var = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.type_var, values=["", "Short", "Long"], state="readonly").grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(filter_frame, text="Status:").grid(row=1, column=0, padx=5, sticky="w")
        self.status_var = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.status_var, values=["", "Draft", "Published"], state="readonly").grid(row=1, column=1, padx=5, sticky="ew")

        ttk.Label(filter_frame, text="Skill Name:").grid(row=2, column=0, padx=5, sticky="w")
        self.skill_filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.skill_filter_var).grid(row=2, column=1, padx=5, sticky="ew")

        ttk.Label(filter_frame, text="Item Name:").grid(row=3, column=0, padx=5, sticky="w")
        self.item_filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.item_filter_var).grid(row=3, column=1, padx=5, sticky="ew")

        ttk.Button(filter_frame, text="Search", command=self.update_results).grid(row=4, column=0, columnspan=2, pady=5)

        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Add/Edit Video", padding="5")
        input_frame.grid(row=1, column=0, sticky="ew", pady=5)

        ttk.Label(input_frame, text="Title:").grid(row=0, column=0, padx=5, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.title_var).grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Type:").grid(row=1, column=0, padx=5, sticky="w")
        self.input_type_var = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.input_type_var, values=["Short", "Long"], state="readonly").grid(row=1, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, sticky="w")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(input_frame, textvariable=self.date_var).grid(row=2, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Status:").grid(row=3, column=0, padx=5, sticky="w")
        self.input_status_var = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.input_status_var, values=["Draft", "Published"], state="readonly").grid(row=3, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Description:").grid(row=4, column=0, padx=5, sticky="w")
        self.description_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.description_var).grid(row=4, column=1, padx=5, sticky="ew")

        # Skills selection
        ttk.Label(input_frame, text="Skills:").grid(row=5, column=0, padx=5, sticky="nw")
        self.skills_listbox = tk.Listbox(input_frame, selectmode="multiple", height=5, exportselection=0)
        self.skills_listbox.grid(row=5, column=1, padx=5, sticky="ew")
        for _, skill_name in self.skills:
            self.skills_listbox.insert("end", skill_name)
        scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.skills_listbox.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.skills_listbox.configure(yscrollcommand=scrollbar.set)

        # Items selection
        ttk.Label(input_frame, text="Items:").grid(row=6, column=0, padx=5, sticky="nw")
        self.items_listbox = tk.Listbox(input_frame, selectmode="multiple", height=5, exportselection=0)
        self.items_listbox.grid(row=6, column=1, padx=5, sticky="ew")
        for _, item_name in self.items:
            self.items_listbox.insert("end", item_name)
        scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.items_listbox.yview)
        scrollbar.grid(row=6, column=2, sticky="ns")
        self.items_listbox.configure(yscrollcommand=scrollbar.set)

        ttk.Button(input_frame, text="Add Video", command=self.add_video).grid(row=7, column=0, pady=5)
        ttk.Button(input_frame, text="Update Selected", command=self.update_selected).grid(row=7, column=1, pady=5)

        # Results table
        columns = ("title", "type", "date", "status", "skills", "items", "description")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("title", text="Title", command=lambda: self.sort_column("title"))
        self.tree.heading("type", text="Type", command=lambda: self.sort_column("type"))
        self.tree.heading("date", text="Date", command=lambda: self.sort_column("date"))
        self.tree.heading("status", text="Status", command=lambda: self.sort_column("status"))
        self.tree.heading("skills", text="Skills")
        self.tree.heading("items", text="Items")
        self.tree.heading("description", text="Description")
        self.tree.column("title", width=250)
        self.tree.column("type", width=80)
        self.tree.column("date", width=100)
        self.tree.column("status", width=80)
        self.tree.column("skills", width=150)
        self.tree.column("items", width=150)
        self.tree.column("description", width=200)
        self.tree.grid(row=2, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(main_frame, text="Delete Selected", command=self.delete_selected).grid(row=3, column=0, pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.load_selected)

        self.sort_by = "date"
        self.sort_order = "DESC"
        self.update_results()

    def update_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        video_type = self.type_var.get()
        status = self.status_var.get()
        skill_name = self.skill_filter_var.get().strip()
        item_name = self.item_filter_var.get().strip()
        
        videos = get_videos(video_type, status, skill_name, item_name, self.sort_by, self.sort_order)
        
        for video in videos:
            self.tree.insert("", "end", values=(
                video["title"],
                video["type"],
                video["date"],
                video["status"],
                video["skills"],
                video["items"],
                video["description"]
            ))

    def sort_column(self, column):
        if self.sort_by == column:
            self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        else:
            self.sort_by = column
            self.sort_order = "ASC"
        self.update_results()

    def add_video(self):
        title = self.title_var.get().strip()
        video_type = self.input_type_var.get()
        date = self.date_var.get().strip()
        status = self.input_status_var.get()
        description = self.description_var.get().strip()
        
        if not title or not video_type or not date or not status:
            messagebox.showerror("Error", "Please fill all required fields.")
            return
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        
        # Get selected skills and items
        selected_skills = [self.skills[i][0] for i in self.skills_listbox.curselection()]
        selected_items = [self.items[i][0] for i in self.items_listbox.curselection()]
        
        add_video(title, video_type, date, status, description, selected_skills, selected_items)
        self.update_results()
        self.clear_inputs()

    def load_selected(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        values = item["values"]
        self.title_var.set(values[0])
        self.input_type_var.set(values[1])
        self.date_var.set(values[2])
        self.input_status_var.set(values[3])
        self.description_var.set(values[6])
        
        # Load skill and item tags
        self.skills_listbox.selection_clear(0, "end")
        self.items_listbox.selection_clear(0, "end")
        
        conn = sqlite3.connect("bazaar.db")
        cursor = conn.cursor()
        
        # Get selected skills
        cursor.execute("SELECT skill_id FROM video_skills WHERE video_id = (SELECT id FROM videos WHERE title = ?)", (values[0],))
        selected_skill_ids = [row[0] for row in cursor.fetchall()]
        for i, (skill_id, _) in enumerate(self.skills):
            if skill_id in selected_skill_ids:
                self.skills_listbox.selection_set(i)
        
        # Get selected items
        cursor.execute("SELECT item_id FROM video_items WHERE video_id = (SELECT id FROM videos WHERE title = ?)", (values[0],))
        selected_item_ids = [row[0] for row in cursor.fetchall()]
        for i, (item_id, _) in enumerate(self.items):
            if item_id in selected_item_ids:
                self.items_listbox.selection_set(i)
        
        conn.close()

    def update_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to update.")
            return
        
        video_id = self.tree.item(selected[0])["values"][0]
        videos = get_videos()
        video_id = next(v["id"] for v in videos if v["title"] == video_id)
        
        title = self.title_var.get().strip()
        video_type = self.input_type_var.get()
        date = self.date_var.get().strip()
        status = self.input_status_var.get()
        description = self.description_var.get().strip()
        
        if not title or not video_type or not date or not status:
            messagebox.showerror("Error", "Please fill all required fields.")
            return
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        
        # Get selected skills and items
        selected_skills = [self.skills[i][0] for i in self.skills_listbox.curselection()]
        selected_items = [self.items[i][0] for i in self.items_listbox.curselection()]
        
        update_video(video_id, title, video_type, date, status, description, selected_skills, selected_items)
        self.update_results()
        self.clear_inputs()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to delete.")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected video?"):
            video_id = self.tree.item(selected[0])["values"][0]
            videos = get_videos()
            video_id = next(v["id"] for v in videos if v["title"] == video_id)
            delete_video(video_id)
            self.update_results()
            self.clear_inputs()

    def clear_inputs(self):
        self.title_var.set("")
        self.input_type_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.input_status_var.set("")
        self.description_var.set("")
        self.skills_listbox.selection_clear(0, "end")
        self.items_listbox.selection_clear(0, "end")


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

# Main application class (unchanged)
class SkillQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skill, Item, and Video Query")
        self.root.geometry("1000x600")
        
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        skills_frame = ttk.Frame(notebook)
        items_frame = ttk.Frame(notebook)
        videos_frame = ttk.Frame(notebook)
        
        notebook.add(skills_frame, text="Skills")
        notebook.add(items_frame, text="Items")
        notebook.add(videos_frame, text="Videos")
        
        self.skills_tab = QueryTab(
            skills_frame, query_skills, get_rarities, get_types, get_heroes, "Skill"
        )
        self.items_tab = QueryTab(
            items_frame, query_items, get_item_rarities, get_item_types, get_item_heroes, "Item", get_item_sizes
        )
        self.videos_tab = VideoTab(videos_frame)

def create_video_table(cursor):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            date TEXT,
            status TEXT,
            description TEXT
        )
    """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_skills (
                video_id INTEGER,
                skill_id INTEGER,
                PRIMARY KEY (video_id, skill_id),
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_items (
                video_id INTEGER,
                item_id INTEGER,
                PRIMARY KEY (video_id, item_id),
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        """)


# Main execution
if __name__ == "__main__":
    # Create indexes and tables
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

    create_video_table(cursor)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_date ON videos(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_skills ON video_skills(video_id, skill_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_items ON video_items(video_id, item_id)")
    conn.commit()
    conn.close()
    
    root = tk.Tk()
    app = SkillQueryApp(root)
    root.mainloop()