import tkinter as tk
from tkinter import ttk
from ui.filter_widgets import FilterWidgets

class SearchPopup:
    def __init__(self, parent, title, query_func, get_rarities_func, get_types_func, get_heroes_func, entity_name, get_sizes_func=None):
        self.popup = tk.Toplevel(parent)
        self.popup.title(title)
        self.popup.geometry("800x600")
        self.query_func = query_func
        self.entity_name = entity_name
        self.selected_items = []
        self.filter_widgets = FilterWidgets(self.popup, get_rarities_func, get_types_func, get_heroes_func, get_sizes_func)
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.popup, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.popup.columnconfigure(0, weight=1)
        self.popup.rowconfigure(0, weight=1)

        self.filter_widgets.create_filters(main_frame)
        ttk.Button(main_frame, text="Search", command=self.update_results).grid(row=1, column=0, pady=5)

        columns = ("name", "size", "effects", "rarities", "types", "heroes", "enchantments") if self.filter_widgets.get_sizes_func else ("name", "effects", "rarities", "types", "heroes", "enchantments")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("name", text="Name")
        if self.filter_widgets.get_sizes_func:
            self.tree.heading("size", text="Size")
        self.tree.heading("effects", text="Effects")
        self.tree.heading("rarities", text="Rarities")
        self.tree.heading("types", text="Types")
        self.tree.heading("heroes", text="Heroes")
        self.tree.heading("enchantments", text="Enchantments")
        self.tree.column("name", width=150)
        if self.filter_widgets.get_sizes_func:
            self.tree.column("size", width=80)
        self.tree.column("effects", width=300)
        self.tree.column("rarities", width=100)
        self.tree.column("types", width=200)
        self.tree.column("heroes", width=150)
        self.tree.column("enchantments", width=200)
        self.tree.grid(row=2, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(main_frame, text="Confirm", command=self.confirm_selection).grid(row=3, column=0, pady=5)

    def update_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        filters = self.filter_widgets.get_filter_values()
        results = self.query_func(
            name=filters["name"],
            rarities=[filters["rarity"]] if filters["rarity"] else [],
            types=filters["types"],
            effect_keyword=filters["effect_keyword"],
            heroes=[filters["hero"]] if filters["hero"] else [],
            size=filters["size"],
            sort_by="name",
            sort_order="ASC"
        )
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
            ) if self.filter_widgets.get_sizes_func else (
                result["name"],
                result["effects"],
                result["rarities"],
                ", ".join(result["types"]),
                ", ".join(result["heroes"]),
                result["enchantments"]
            )
            self.tree.insert("", "end", values=values, tags=(result["id"],))

    def confirm_selection(self):
        selected = self.tree.selection()
        self.selected_items = [(self.tree.item(item, "tags")[0], self.tree.item(item, "values")[0]) for item in selected]
        self.popup.destroy()