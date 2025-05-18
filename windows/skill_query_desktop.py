import tkinter as tk
from tkinter import ttk
from db.db_routine import DBRoutine
from db.skills import SkillDB
from db.items import ItemDB
from db.videos import VideoDB
from tabs.skills_tab import SkillsTab
from tabs.items_tab import ItemsTab
from tabs.videos_tab import VideoTab

class SkillQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skill, Item, and Video Query")
        self.root.geometry("1000x600")
        
        # Initialize database
        self.db_routine = DBRoutine()
        self.skill_db = SkillDB(self.db_routine)
        self.item_db = ItemDB(self.db_routine)
        self.video_db = VideoDB(self.db_routine)

        # Create notebook
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Add tabs
        skills_frame = ttk.Frame(notebook)
        items_frame = ttk.Frame(notebook)
        videos_frame = ttk.Frame(notebook)
        notebook.add(skills_frame, text="Skills")
        notebook.add(items_frame, text="Items")
        notebook.add(videos_frame, text="Videos")

        self.skills_tab = SkillsTab(skills_frame, self.skill_db)
        self.items_tab = ItemsTab(items_frame, self.item_db)
        self.videos_tab = VideoTab(videos_frame, self.video_db, self.skill_db, self.item_db)

if __name__ == "__main__":
    root = tk.Tk()
    app = SkillQueryApp(root)
    root.mainloop()