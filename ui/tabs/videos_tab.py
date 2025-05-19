import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from ui.search_popup import SearchPopup

class VideoTab:
    def __init__(self, parent, video_db, skill_db, item_db):
        self.parent = parent
        self.video_db = video_db
        self.skill_db = skill_db
        self.item_db = item_db
        self.heroes = self.video_db.get_all_heroes()
        self.selected_skills = []
        self.selected_items = []
        self.sort_by = "date"
        self.sort_order = "DESC"
        self.skill_filter_ids = []
        self.item_filter_ids = []
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

        ttk.Label(filter_frame, text="Skill:").grid(row=2, column=0, padx=5, sticky="w")
        self.skill_filter_var = tk.StringVar()
        self.skill_filter_entry = ttk.Entry(filter_frame, textvariable=self.skill_filter_var, state="readonly")
        self.skill_filter_entry.grid(row=2, column=1, padx=5, sticky="ew")
        ttk.Button(filter_frame, text="Advanced Search", command=self.open_skill_search).grid(row=2, column=2, padx=5)

        ttk.Label(filter_frame, text="Item:").grid(row=3, column=0, padx=5, sticky="w")
        self.item_filter_var = tk.StringVar()
        self.item_filter_entry = ttk.Entry(filter_frame, textvariable=self.item_filter_var, state="readonly")
        self.item_filter_entry.grid(row=3, column=1, padx=5, sticky="ew")
        ttk.Button(filter_frame, text="Advanced Search", command=self.open_item_search).grid(row=3, column=2, padx=5)

        ttk.Label(filter_frame, text="Heroes:").grid(row=4, column=0, padx=5, sticky="nw")
        self.heroes_filter_listbox = tk.Listbox(filter_frame, selectmode="single", height=5, exportselection=0)
        self.heroes_filter_listbox.grid(row=4, column=1, padx=5, sticky="ew")
        for hero in self.heroes:
            self.heroes_filter_listbox.insert("end", hero)
        heroes_scrollbar = ttk.Scrollbar(filter_frame, orient="vertical", command=self.heroes_filter_listbox.yview)
        heroes_scrollbar.grid(row=4, column=2, sticky="ns")
        self.heroes_filter_listbox.configure(yscrollcommand=heroes_scrollbar.set)

        ttk.Button(filter_frame, text="Search", command=self.update_results).grid(row=5, column=0, columnspan=3, pady=5)

        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Add/Edit Video", padding="5")
        input_frame.grid(row=1, column=0, sticky="ew", pady=5)

        ttk.Label(input_frame, text="Title:").grid(row=0, column=0, padx=5, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.title_var).grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Type:").grid(row=1, column=0, padx=5, sticky="w")
        self.input_type_var = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.input_type_var, values=["Short", "Long"], state="readonly").grid(row=1, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Date:").grid(row=2, column=0, padx=5, sticky="w")
        self.date_entry = DateEntry(input_frame, date_pattern="yyyy-mm-dd", width=12)
        self.date_entry.grid(row=2, column=1, padx=5, sticky="ew")
        self.date_entry.set_date(datetime.now())

        ttk.Label(input_frame, text="Status:").grid(row=3, column=0, padx=5, sticky="w")
        self.input_status_var = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.input_status_var, values=["Draft", "Published"], state="readonly").grid(row=3, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Description:").grid(row=4, column=0, padx=5, sticky="w")
        self.description_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.description_var).grid(row=4, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Local Path:").grid(row=5, column=0, padx=5, sticky="w")
        self.local_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.local_path_var).grid(row=5, column=1, padx=5, sticky="ew")

        ttk.Label(input_frame, text="Skills:").grid(row=6, column=0, padx=5, sticky="w")
        self.skills_var = tk.StringVar()
        self.skills_entry = ttk.Entry(input_frame, textvariable=self.skills_var, state="readonly")
        self.skills_entry.grid(row=6, column=1, padx=5, sticky="ew")
        ttk.Button(input_frame, text="Select Skills", command=self.select_skills).grid(row=6, column=2, padx=5)

        ttk.Label(input_frame, text="Items:").grid(row=7, column=0, padx=5, sticky="w")
        self.items_var = tk.StringVar()
        self.items_entry = ttk.Entry(input_frame, textvariable=self.items_var, state="readonly")
        self.items_entry.grid(row=7, column=1, padx=5, sticky="ew")
        ttk.Button(input_frame, text="Select Items", command=self.select_items).grid(row=7, column=2, padx=5)

        ttk.Label(input_frame, text="Heroes:").grid(row=8, column=0, padx=5, sticky="nw")
        self.heroes_listbox = tk.Listbox(input_frame, selectmode="single", height=5, exportselection=0)
        self.heroes_listbox.grid(row=8, column=1, padx=5, sticky="ew")
        for hero in self.heroes:
            self.heroes_listbox.insert("end", hero)
        scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.heroes_listbox.yview)
        scrollbar.grid(row=8, column=2, sticky="ns")
        self.heroes_listbox.configure(yscrollcommand=scrollbar.set)

        ttk.Button(input_frame, text="Add Video", command=self.add_video).grid(row=9, column=0, pady=5)
        ttk.Button(input_frame, text="Update Selected", command=self.update_selected).grid(row=9, column=1, pady=5)

        # Results table
        columns = ("title", "type", "date", "status", "skills", "items", "heroes", "description", "local_path")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("title", text="Title", command=lambda: self.sort_column("title"))
        self.tree.heading("type", text="Type", command=lambda: self.sort_column("type"))
        self.tree.heading("date", text="Date", command=lambda: self.sort_column("date"))
        self.tree.heading("status", text="Status", command=lambda: self.sort_column("status"))
        self.tree.heading("skills", text="Skills")
        self.tree.heading("items", text="Items")
        self.tree.heading("heroes", text="Heroes")
        self.tree.heading("description", text="Description")
        self.tree.heading("local_path", text="Local Path")
        self.tree.column("title", width=200)
        self.tree.column("type", width=80)
        self.tree.column("date", width=100)
        self.tree.column("status", width=80)
        self.tree.column("skills", width=150)
        self.tree.column("items", width=150)
        self.tree.column("heroes", width=150)
        self.tree.column("description", width=150)
        self.tree.column("local_path", width=200)
        self.tree.grid(row=2, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(main_frame, text="Delete Selected", command=self.delete_selected).grid(row=3, column=0, pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.load_selected)
        self.update_results()

    def open_skill_search(self):
        popup = SearchPopup(
            self.parent,
            "Search Skills",
            self.skill_db.query_skills,
            self.skill_db.get_rarities,
            self.skill_db.get_types,
            self.skill_db.get_heroes,
            "Skill"
        )
        self.parent.wait_window(popup.popup)
        self.skill_filter_ids = [int(id) for id, name in popup.selected_items]
        self.skill_filter_var.set(", ".join(name for _, name in popup.selected_items))
        self.update_results()

    def open_item_search(self):
        popup = SearchPopup(
            self.parent,
            "Search Items",
            self.item_db.query_items,
            self.item_db.get_rarities,
            self.item_db.get_types,
            self.item_db.get_heroes,
            "Item",
            self.item_db.get_sizes
        )
        self.parent.wait_window(popup.popup)
        self.item_filter_ids = [int(id) for id, name in popup.selected_items]
        self.item_filter_var.set(", ".join(name for _, name in popup.selected_items))
        self.update_results()

    def select_skills(self):
        popup = SearchPopup(
            self.parent,
            "Select Skills",
            self.skill_db.query_skills,
            self.skill_db.get_rarities,
            self.skill_db.get_types,
            self.skill_db.get_heroes,
            "Skill"
        )
        self.parent.wait_window(popup.popup)
        self.selected_skills = popup.selected_items
        self.skills_var.set(", ".join(name for _, name in self.selected_skills))

    def select_items(self):
        popup = SearchPopup(
            self.parent,
            "Select Items",
            self.item_db.query_items,
            self.item_db.get_rarities,
            self.item_db.get_types,
            self.item_db.get_heroes,
            "Item",
            self.item_db.get_sizes
        )
        self.parent.wait_window(popup.popup)
        self.selected_items = popup.selected_items
        self.items_var.set(", ".join(name for _, name in self.selected_items))

    def update_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        selected_heroes = [self.heroes[i] for i in self.heroes_filter_listbox.curselection()]
        videos = self.video_db.get_videos(
            video_type=self.type_var.get(),
            status=self.status_var.get(),
            skill_ids=self.skill_filter_ids if self.skill_filter_ids else None,
            item_ids=self.item_filter_ids if self.item_filter_ids else None,
            hero_name=selected_heroes[0] if len(selected_heroes) != 0 else None,
            sort_by=self.sort_by,
            sort_order=self.sort_order
        )
        for video in videos:
            self.tree.insert("", "end", values=(
                video["title"],
                video["type"],
                video["date"],
                video["status"],
                video["skills"],
                video["items"],
                video["heroes"],
                video["description"],
                video["local_path"] or ""
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
        date = self.date_entry.get()
        status = self.input_status_var.get()
        description = self.description_var.get().strip()
        local_path = self.local_path_var.get().strip()
        if not title or not video_type or not date or not status:
            messagebox.showerror("Error", "Please fill all required fields (Title, Type, Date, Status).")
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        skill_ids = [int(id) for id, _ in self.selected_skills]
        item_ids = [int(id) for id, _ in self.selected_items]
        hero_names = [self.heroes[i] for i in self.heroes_listbox.curselection()]
        self.video_db.add_video(title, video_type, date, status, description, skill_ids, item_ids, hero_names, local_path)
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
        self.date_entry.set_date(datetime.strptime(values[2], "%Y-%m-%d"))
        self.input_status_var.set(values[3])
        self.description_var.set(values[7])
        self.local_path_var.set(values[8])
        with self.video_db.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT skill_id FROM video_skills WHERE video_id = (SELECT id FROM videos WHERE title = ?)", (values[0],))
            selected_skill_ids = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT item_id FROM video_items WHERE video_id = (SELECT id FROM videos WHERE title = ?)", (values[0],))
            selected_item_ids = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT hero_name FROM video_heroes WHERE video_id = (SELECT id FROM videos WHERE title = ?)", (values[0],))
            selected_hero_names = [row[0] for row in cursor.fetchall()]
        self.selected_skills = [(str(id), name) for id, name in self.skill_db.get_all_skills() if id in selected_skill_ids]
        self.selected_items = [(str(id), name) for id, name in self.item_db.get_all_items() if id in selected_item_ids]
        self.skills_var.set(", ".join(name for _, name in self.selected_skills))
        self.items_var.set(", ".join(name for _, name in self.selected_items))
        self.heroes_listbox.selection_clear(0, "end")
        for i, hero in enumerate(self.heroes):
            if hero in selected_hero_names:
                self.heroes_listbox.selection_set(i)

    def update_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to update.")
            return
        video_id = self.tree.item(selected[0])["values"][0]
        videos = self.video_db.get_videos()
        video_id = next(v["id"] for v in videos if v["title"] == video_id)
        title = self.title_var.get().strip()
        video_type = self.input_type_var.get()
        date = self.date_entry.get()
        status = self.input_status_var.get()
        description = self.description_var.get().strip()
        local_path = self.local_path_var.get().strip()
        if not title or not video_type or not date or not status:
            messagebox.showerror("Error", "Please fill all required fields (Title, Type, Date, Status).")
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return
        skill_ids = [int(id) for id, _ in self.selected_skills]
        item_ids = [int(id) for id, _ in self.selected_items]
        hero_names = [self.heroes[i] for i in self.heroes_listbox.curselection()]
        self.video_db.update_video(video_id, title, video_type, date, status, description, skill_ids, item_ids, hero_names, local_path)
        self.update_results()
        self.clear_inputs()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to delete.")
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected video?"):
            video_id = self.tree.item(selected[0])["values"][0]
            videos = self.video_db.get_videos()
            video_id = next(v["id"] for v in videos if v["title"] == str(video_id))
            self.video_db.delete_video(video_id)
            self.update_results()
            self.clear_inputs()

    def clear_inputs(self):
        self.title_var.set("")
        self.input_type_var.set("")
        self.date_entry.set_date(datetime.now())
        self.input_status_var.set("")
        self.description_var.set("")
        self.local_path_var.set("")
        self.selected_skills = []
        self.selected_items = []
        self.skills_var.set("")
        self.items_var.set("")
        self.heroes_listbox.selection_clear(0, "end")