import subprocess
import sys
import os

def check_and_install():
    modules = {
        'pyautogui': 'pyautogui',
        'keyboard': 'keyboard',
        'PIL': 'Pillow',
        'tkinter': 'tk'
    }
    for module, package in modules.items():
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

check_and_install()

import pyautogui
import keyboard
import time
import ctypes
import math
import tkinter as tk
from PIL import ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

pyautogui.PAUSE = 0.001
ENEMY_COLORS = [(158, 20, 20), (250, 28, 29)]
FOREST_COLORS = [(34, 49, 21), (50, 65, 30), (45, 60, 25)]
TOLERANCE = 10
SCAN_STEP = 4  
current_cluster_dist = 5 
target_mode = "Uniform"
path_mode = "Smart"

def get_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def sort_points(points):
    if not points or path_mode == "Direct":
        return sorted(points, key=lambda p: (p[1], p[0]))
    pts = list(points)
    sorted_pts = [pts.pop(0)]
    while pts:
        curr = sorted_pts[-1]
        nearest = min(range(len(pts)), key=lambda i: get_dist(curr, pts[i]))
        sorted_pts.append(pts.pop(nearest))
    return sorted_pts

def is_target(r, g, b, targets):
    for tc in targets:
        if all(abs(c1 - c2) <= TOLERANCE for c1, c2 in zip((r, g, b), tc)):
            return True
    return False

def select_area():
    region = []
    root = tk.Tk()
    root.attributes("-alpha", 0.3, "-fullscreen", True, "-topmost", True)
    canvas = tk.Canvas(root, cursor="cross", bg="grey")
    canvas.pack(fill="both", expand=True)
    start_x = start_y = rect = None
    def on_press(e):
        nonlocal start_x, start_y, rect
        start_x, start_y = e.x, e.y
        rect = canvas.create_rectangle(start_x, start_y, 1, 1, outline='red')
    def on_move(e):
        canvas.coords(rect, start_x, start_y, e.x, e.y)
    def on_release(e):
        region.append((min(start_x, e.x), min(start_y, e.y), max(start_x, e.x), max(start_y, e.y)))
        root.destroy()
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.mainloop()
    return region[0] if region else None

def process_pixels(area, raw_data, dist):
    pixels = raw_data['pixels']
    off_x, off_y = area[0], area[1]
    points = []
    targets = FOREST_COLORS if target_mode == "Lumberjack" else ENEMY_COLORS
    found_pixels = [(x + off_x, y + off_y) for x, y, r, g, b in pixels if is_target(r, g, b, targets)]
    if not found_pixels: return []
    
    if target_mode in ["Uniform", "Lumberjack"]:
        for px, py in found_pixels:
            if len(points) > 5000: return "OVERLOAD"
            if not any(get_dist((px, py), p) < dist for p in points):
                points.append((px, py))
    else:
        clusters = []
        for px, py in found_pixels:
            if len(clusters) > 5000: return "OVERLOAD"
            found = False
            for c in clusters:
                if get_dist((px, py), c['avg']) < dist:
                    c['pts'].append((px, py))
                    c['avg'] = (sum(p[0] for p in c['pts'])/len(c['pts']), sum(p[1] for p in c['pts'])/len(c['pts']))
                    found = True
                    break
            if not found: clusters.append({'pts': [(px, py)], 'avg': (px, py)})
        points = [(int(c['avg'][0]), int(c['avg'][1])) for c in clusters]
    return sort_points(points)

def show_preview(area, raw_data):
    global current_cluster_dist, target_mode, path_mode
    res = {"go": False, "pts": []}
    preview = tk.Tk()
    preview.attributes("-alpha", 0.3, "-fullscreen", True, "-topmost", True)
    preview.overrideredirect(True)
    canvas = tk.Canvas(preview, bg='black', highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    def redraw():
        canvas.delete("all")
        canvas.create_rectangle(area[0], area[1], area[2], area[3], outline='yellow')
        data = process_pixels(area, raw_data, current_cluster_dist)
        
        if data == "OVERLOAD":
            res["pts"] = []
            canvas.create_rectangle(area[0], area[1], area[0]+550, area[1]+60, fill="#721c24", outline="#f5c6cb")
            canvas.create_text(area[0]+10, area[1]+10, 
                               text="⚠️ HIGH DENSITY: OVER 5000 POINTS\nCalculation stopped, CPUs are expensive nowadays!", 
                               fill="#f8d7da", font=("Consolas", 11, "bold"), anchor="nw")
            pts_count = "5000+"
            y_info = area[1]+65
        else:
            res["pts"] = data
            pts_count = len(res["pts"])
            y_info = area[1]+5
            p_color = {"Uniform": "#00FF00", "Center": "#00FFFF", "Lumberjack": "#8B4513"}[target_mode]
            if target_mode != "Lumberjack" and len(res["pts"]) > 1:
                l_col = "white" if path_mode == "Smart" else "gray30"
                for i in range(len(res["pts"])-1):
                    canvas.create_line(res["pts"][i][0], res["pts"][i][1], res["pts"][i+1][0], res["pts"][i+1][1], fill=l_col, dash=(2, 2))
            for x, y in res["pts"]:
                canvas.create_oval(x-2, y-2, x+2, y+2, fill=p_color, outline="white")

        info = f"[{target_mode}] | {path_mode} | PTS: {pts_count} | RAD: {current_cluster_dist}\n" \
               f"[TAB] Mode | [S] Path | [MWheel] Rad | [ENT] Fire"
        canvas.create_text(area[0]+5, y_info, text=info, fill="#00FF00", font=("Consolas", 10, "bold"), anchor="nw")

    def handle_keys(e):
        global path_mode, target_mode, current_cluster_dist
        key = e.keysym.lower()
        if key == 's' or e.keycode == 83:
            path_mode = "Smart" if path_mode == "Direct" else "Direct"
        elif key == 'tab':
            if e.state & 0x0001:
                target_mode = "Lumberjack"
                current_cluster_dist = 100
            else:
                target_mode = "Center" if target_mode == "Uniform" else "Uniform"
        redraw()

    def on_wheel(e):
        global current_cluster_dist
        up = e.delta > 0
        if up:
            if current_cluster_dist < 10: current_cluster_dist += 1
            else: current_cluster_dist = (current_cluster_dist // 5) * 5 + 5
        else:
            if current_cluster_dist <= 10: current_cluster_dist -= 1
            else:
                current_cluster_dist = (current_cluster_dist // 5) * 5 - 5
                if current_cluster_dist < 10: current_cluster_dist = 10
        current_cluster_dist = max(1, current_cluster_dist)
        redraw()

    preview.bind("<Key>", handle_keys)
    preview.bind("<MouseWheel>", on_wheel)
    preview.bind("<Return>", lambda e: [res.update({"go": True}), preview.destroy()] if res["pts"] else None)
    preview.bind("<Button-1>", lambda e: preview.destroy())
    redraw()
    preview.focus_force()
    preview.mainloop()
    return res["pts"] if res["go"] else None

def start_process():
    area = select_area()
    if not area: return
    shot = ImageGrab.grab(bbox=area)
    pix = shot.load()
    w, h = shot.size
    raw_pixels = []
    for x in range(0, w, SCAN_STEP):
        for y in range(0, h, SCAN_STEP):
            raw_pixels.append((x, y, *pix[x, y]))
    final_points = show_preview(area, {'pixels': raw_pixels})
    if final_points:
        for px, py in final_points:
            if keyboard.is_pressed('f5'): break
            pyautogui.rightClick(px, py)
            time.sleep(0.015)

print("F6: Start | F5: Stop | S: Path Mode | TAB/Shift+TAB: Target Mode")

while True:
    if keyboard.is_pressed('f6'):
        time.sleep(0.2)
        start_process()
    time.sleep(0.05)