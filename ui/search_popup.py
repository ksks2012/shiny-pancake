import tkinter as tk
from tkinter import ttk
from ui.filter_widgets import FilterWidgets

class SearchPopup:
    def __init__(self, parent, title, query_func, get_rarities_func, get_types_func, get_heroes_func, entity_name, get_sizes_func=None):
        self.popup = tk.Toplevel(parent)
        self.popup.title(title)
        self.popup.geometry("1000x600")
        self.query_func = query_func
        self.entity_name = entity_name
        self.selected_items = []
        self.filter_widgets = FilterWidgets(self.popup, get_rarities_func, get_types_func, get_heroes_func, get_sizes_func)
        self.get_sizes_func = get_sizes_func
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.popup, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.popup.columnconfigure(0, weight=1)
        self.popup.rowconfigure(0, weight=1)

        self.filter_widgets.create_filters(main_frame)
        ttk.Button(main_frame, text="Search", command=self.update_results).grid(row=1, column=0, pady=5)

        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=2, column=0, sticky="nsew")
        main_frame.rowconfigure(2, weight=1)

        # Treeview (Query Results)
        columns = ("name", "size", "effects", "rarities", "types", "heroes", "enchantments") if self.filter_widgets.get_sizes_func else ("name", "effects", "rarities", "types", "heroes", "enchantments")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="extended")
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
        self.tree.column("effects", width=200)
        self.tree.column("rarities", width=100)
        self.tree.column("types", width=150)
        self.tree.column("heroes", width=100)
        self.tree.column("enchantments", width=150)
        self.tree.grid(row=0, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=3)
        results_frame.rowconfigure(0, weight=1)

        tree_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        selected_frame = ttk.LabelFrame(results_frame, text="Selected Items", padding="5")
        selected_frame.grid(row=0, column=2, sticky="nsew", padx=10)
        results_frame.columnconfigure(2, weight=1)

        self.selected_count_var = tk.StringVar(value="Selected: 0 items")
        ttk.Label(selected_frame, textvariable=self.selected_count_var).grid(row=1, column=0, pady=5)
        self.selected_listbox = tk.Listbox(selected_frame, selectmode="multiple", width=30, height=15)
        self.selected_listbox.grid(row=0, column=0, sticky="nsew")
        selected_frame.rowconfigure(0, weight=1)

        listbox_scrollbar = ttk.Scrollbar(selected_frame, orient="vertical", command=self.selected_listbox.yview)
        listbox_scrollbar.grid(row=0, column=1, sticky="ns")
        self.selected_listbox.configure(yscrollcommand=listbox_scrollbar.set)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=5)

        ttk.Button(button_frame, text="Add Selected", command=self.add_selected).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Confirm", command=self.confirm_selection).grid(row=0, column=3, padx=5)

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
            ) if self.get_sizes_func != None else self.query_func(
                name=filters["name"],
                rarities=[filters["rarity"]] if filters["rarity"] else [],
                types=filters["types"],
                effect_keyword=filters["effect_keyword"],
                heroes=[filters["hero"]] if filters["hero"] else [],
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
            )
            self.tree.insert("", "end", values=values, tags=(result["id"],))

    def add_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        existing_names = {name for _, name in self.selected_items}
        for item in selected:
            item_id = self.tree.item(item, "tags")[0]
            item_name = self.tree.item(item, "values")[0]
            if item_name not in existing_names:
                self.selected_items.append((item_id, item_name))
                self.selected_listbox.insert("end", item_name)
                existing_names.add(item_name)
        self.selected_count_var.set(f"Selected: {len(self.selected_items)} items")

    def remove_selected(self):
        selected_indices = self.selected_listbox.curselection()
        if not selected_indices:
            return
        # Remove from the end to avoid index shifting
        for index in reversed(selected_indices):
            item_name = self.selected_listbox.get(index)
            self.selected_listbox.delete(index)
            # Remove the corresponding selected_items
            self.selected_items = [(id_, name) for id_, name in self.selected_items if name != item_name]
        self.selected_count_var.set(f"Selected: {len(self.selected_items)} items")

    def clear_all(self):
        self.selected_listbox.delete(0, "end")
        self.selected_items = []
        self.selected_count_var.set(f"Selected: {len(self.selected_items)} items")

    def confirm_selection(self):
        self.popup.destroy()