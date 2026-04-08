import os
import random
import tkinter as tk
from PIL import Image, ImageTk

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")

class CaptchaPuzzle(tk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._tiles = []
        self._order = []
        self._selected = None
        self._buttons = []
        self._load()
        self._render()
    
    def _load(self):
        images = sorted([f for f in os.listdir(IMAGES_DIR) if f.endswith(".png")])
        if len(images) < 4:
            for i in range(4):
                img = Image.new('RGB', (100, 100), color=(100, 150, 200))
                self._tiles.append(ImageTk.PhotoImage(img))
        else:
            for f in images[:4]:
                img = Image.open(os.path.join(IMAGES_DIR, f)).resize((100, 100), Image.Resampling.LANCZOS)
                self._tiles.append(ImageTk.PhotoImage(img))
        
        self._order = list(range(4))
        while self._order == [0, 1, 2, 3]:
            random.shuffle(self._order)
    
    def _render(self):
        for btn in self._buttons:
            btn.destroy()
        self._buttons = []
        self._selected = None
        for i, tile_idx in enumerate(self._order):
            r, c = divmod(i, 2)
            photo = self._tiles[tile_idx]
            btn = tk.Button(
                self,
                image=photo,
                relief="raised",
                bd=2,
                command=lambda pos=i: self._on_click(pos),
            )
            btn.image = photo
            btn.grid(row=r, column=c, padx=1, pady=1)
            self._buttons.append(btn)
    
    def _on_click(self, pos):
        if self._selected is None:
            self._selected = pos
            self._buttons[pos].config(relief="sunken", bg="gray")
        else:
            if self._selected != pos:
                self._order[self._selected], self._order[pos] = (
                    self._order[pos],
                    self._order[self._selected],
                )
            self._render()
    
    def is_solved(self):
        return self._order == [0, 1, 2, 3]

    def reset(self):
        self._load()
        self._render()
