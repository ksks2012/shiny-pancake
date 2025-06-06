import tkinter as tk
from tkinter import ttk
import csv
from ui.filter_widgets import FilterWidgets

class SkillsTab:
    def __init__(self, parent, skill_db):
        self.parent = parent
        self.skill_db = skill_db
        self.sort_by = "name"
        self.sort_order = "ASC"
        self.filter_widgets = FilterWidgets(
            self.parent,
            self.skill_db.get_rarities,
            self.skill_db.get_types,
            self.skill_db.get_heroes
        )
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

        self.filter_widgets.create_filters(main_frame)
        ttk.Button(main_frame, text="Search", command=self.update_results).grid(row=1, column=0, pady=5)
        ttk.Button(main_frame, text="Export to CSV", command=self.export_results).grid(row=2, column=0, pady=5)

        columns = ("name", "effects", "rarities", "types", "heroes")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Name", command=lambda: self.sort_column("name"))
        self.tree.heading("effects", text="Effects")
        self.tree.heading("rarities", text="Rarities", command=lambda: self.sort_column("rarity"))
        self.tree.heading("types", text="Types", command=lambda: self.sort_column("types"))
        self.tree.heading("heroes", text="Heroes")
        self.tree.column("name", width=150)
        self.tree.column("effects", width=300)
        self.tree.column("rarities", width=100)
        self.tree.column("types", width=200)
        self.tree.column("heroes", width=150)
        self.tree.grid(row=3, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def update_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        filters = self.filter_widgets.get_filter_values()
        results = self.skill_db.query_skills(
            name=filters["name"],
            rarities=[filters["rarity"]] if filters["rarity"] else [],
            types=filters["types"],
            effect_keyword=filters["effect_keyword"],
            heroes=[filters["hero"]] if filters["hero"] else [],
            sort_by=self.sort_by,
            sort_order=self.sort_order
        )
        self.current_results = results
        for result in results:
            self.tree.insert("", "end", values=(
                result["name"],
                result["effects"],
                result["rarities"],
                ", ".join(result["types"]),
                ", ".join(result["heroes"])
            ))

    def sort_column(self, column):
        if self.sort_by == column:
            self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        else:
            self.sort_by = column
            self.sort_order = "ASC"
        self.update_results()

    def export_results(self):
        if not hasattr(self, "current_results") or not self.current_results:
            tk.messagebox.showinfo("Export", "No results to export.")
            return
        with open("skills_results.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Effects", "Rarities", "Types", "Heroes"])
            for result in self.current_results:
                writer.writerow([
                    result["name"],
                    result["effects"],
                    result["rarities"],
                    ", ".join(result["types"]),
                    ", ".join(result["heroes"])
                ])
        tk.messagebox.showinfo("Export", "Results exported to skills_results.csv")