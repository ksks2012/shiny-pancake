import tkinter as tk
from tkinter import ttk

class FilterWidgets:
    def __init__(self, parent, get_rarities_func, get_types_func, get_heroes_func, get_sizes_func=None):
        self.parent = parent
        self.get_rarities_func = get_rarities_func
        self.get_types_func = get_types_func
        self.get_heroes_func = get_heroes_func
        self.get_sizes_func = get_sizes_func
        self.widgets = {}

    def create_filters(self, main_frame):
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.grid(row=0, column=0, sticky="ew", pady=5)

        # Name
        ttk.Label(filter_frame, text="Name:").grid(row=0, column=0, padx=5, sticky="w")
        self.widgets["name_var"] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.widgets["name_var"]).grid(row=0, column=1, padx=5, sticky="ew")

        # Effect Keyword
        ttk.Label(filter_frame, text="Effect Keyword:").grid(row=1, column=0, padx=5, sticky="w")
        self.widgets["effect_var"] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.widgets["effect_var"]).grid(row=1, column=1, padx=5, sticky="ew")

        # Rarity
        ttk.Label(filter_frame, text="Rarity:").grid(row=2, column=0, padx=5, sticky="w")
        self.widgets["rarity_var"] = tk.StringVar()
        rarities = self.get_rarities_func()
        ttk.Combobox(filter_frame, textvariable=self.widgets["rarity_var"], values=rarities, state="readonly").grid(row=2, column=1, padx=5, sticky="ew")

        # Hero
        ttk.Label(filter_frame, text="Hero:").grid(row=3, column=0, padx=5, sticky="w")
        self.widgets["hero_var"] = tk.StringVar()
        heroes = self.get_heroes_func()
        ttk.Combobox(filter_frame, textvariable=self.widgets["hero_var"], values=heroes, state="readonly").grid(row=3, column=1, padx=5, sticky="ew")

        # Size (if applicable)
        row_offset = 4
        if self.get_sizes_func:
            ttk.Label(filter_frame, text="Size:").grid(row=4, column=0, padx=5, sticky="w")
            self.widgets["size_var"] = tk.StringVar()
            sizes = self.get_sizes_func()
            ttk.Combobox(filter_frame, textvariable=self.widgets["size_var"], values=sizes, state="readonly").grid(row=4, column=1, padx=5, sticky="ew")
            row_offset += 1

        # Types
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

        self.widgets["type_vars"] = {}
        types = self.get_types_func()
        for i, type_name in enumerate(types):
            var = tk.BooleanVar()
            self.widgets["type_vars"][type_name] = var
            ttk.Checkbutton(scrollable_frame, text=type_name, variable=var).grid(row=i, column=0, sticky="w")

        return filter_frame

    def get_filter_values(self):
        return {
            "name": self.widgets["name_var"].get().strip(),
            "rarity": self.widgets["rarity_var"].get(),
            "types": [t for t, var in self.widgets["type_vars"].items() if var.get()],
            "effect_keyword": self.widgets["effect_var"].get().strip(),
            "hero": self.widgets["hero_var"].get(),
            "size": self.widgets.get("size_var", tk.StringVar()).get()
        }