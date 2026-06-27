import os
import json
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
import asyncio
import threading
from tkinter import ttk, messagebox
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from pipeline_tasks import run_Flux_Image_Gen

# Paths defined based on requirements
BASE_DIR = r"D:\AI_Schemea"
IMAGE_DIR = os.path.join(BASE_DIR, "IMAGE")
JSON_FILE = os.path.join(BASE_DIR, "Text_Files", "processed_output.json")

MAX_WORKERS = 4   # how many parallel threads (image + video jobs combined)


class CorporateUIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Visualizer - Corporate Edition")
        self.geometry("1400x900")
        
        # Simple Corporate UI Styling (Dark Theme)
        self.configure(bg="#1E1E1E")
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
            
        self.style.configure("TFrame", background="#1E1E1E")
        self.style.configure("Card.TFrame", background="#2D2D30", borderwidth=1, relief="solid")
        self.style.configure("Sidebar.TFrame", background="#252526", borderwidth=0)
        self.style.configure("TLabel", background="#1E1E1E", foreground="#CCCCCC", font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#FFFFFF", background="#1E1E1E")
        self.style.configure("SidebarHeader.TLabel", font=("Segoe UI", 14, "bold"), foreground="#FFFFFF", background="#252526")
        self.style.configure("Sidebar.TLabel", background="#252526", foreground="#CCCCCC", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8, background="#0E639C", foreground="#FFFFFF")
        self.style.map("TButton", background=[("active", "#1177BB")])
        self.style.configure("Danger.TButton", background="#C53A3A", foreground="#FFFFFF")
        self.style.map("Danger.TButton", background=[("active", "#E54A4A")])

        self.data_var = tk.StringVar()
        self.batches = {}
        self.prompts = {}
        self.scene_keys = []
        self.current_scene_index = 0
        self.photo_refs = []
        
        # Initialize attributes for linter and structure
        self.input_frame = None
        self.entry_data = None
        self.sidebar = None
        self.lbl_total_scenes = None
        self.lbl_total_images = None
        self.main_area = None
        self.top_nav = None
        self.btn_prev = None
        self.lbl_scene_name = None
        self.btn_next = None
        self.prompt_frame = None
        self.txt_prompt = None
        self.canvas_container = None
        self.image_canvas = None
        self.scrollbar = None
        self.image_frame = None
        self.bottom_frame = None
        
        self.show_input_page()

    def show_input_page(self):
        self.input_frame = ttk.Frame(self)
        self.input_frame.pack(expand=True, fill="both")
        
        center_frame = ttk.Frame(self.input_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(center_frame, text="System Initialization", style="Header.TLabel").pack(pady=(0, 20))
        ttk.Label(center_frame, text="Please enter your authentication/input data:").pack(pady=5)
        
        self.entry_data = ttk.Entry(center_frame, textvariable=self.data_var, width=45, font=("Segoe UI", 12))
        self.entry_data.pack(pady=10)
        
        submit_btn = ttk.Button(center_frame, text="Proceed to Dashboard", command=self.load_main_page)
        submit_btn.pack(pady=20)

    def load_main_page(self):
        input_val = self.data_var.get().strip()
        if not input_val:
            messagebox.showwarning("Input Required", "Data input is required to proceed.")
            return
            
        print(f"[INFO] Initialized with data: {input_val}")
        
        self.input_frame.destroy()
        self.setup_main_page()
        self.load_data()
        self.display_current_scene()

    def setup_main_page(self):
        # Sidebar
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        ttk.Label(self.sidebar, text="Dashboard Overview", style="SidebarHeader.TLabel").pack(pady=20, padx=15, anchor="w")
        
        self.lbl_total_scenes = ttk.Label(self.sidebar, text="Unique Scenes: 0", style="Sidebar.TLabel")
        self.lbl_total_scenes.pack(pady=5, padx=15, anchor="w")
        
        self.lbl_total_images = ttk.Label(self.sidebar, text="Total Images: 0", style="Sidebar.TLabel")
        self.lbl_total_images.pack(pady=5, padx=15, anchor="w")
        
        # Main Layout
        self.main_area = ttk.Frame(self)
        self.main_area.pack(side="right", expand=True, fill="both")
        
        # Top Navigation
        self.top_nav = ttk.Frame(self.main_area)
        self.top_nav.pack(side="top", fill="x", padx=20, pady=20)
        
        self.btn_prev = ttk.Button(self.top_nav, text="◀ Previous Batch", command=self.prev_scene)
        self.btn_prev.pack(side="left")
        
        self.lbl_scene_name = ttk.Label(self.top_nav, text="Current Scene: None", font=("Segoe UI", 16, "bold"), foreground="#FFFFFF")
        self.lbl_scene_name.pack(side="left", expand=True)
        
        self.btn_next = ttk.Button(self.top_nav, text="Next Batch ▶", command=self.next_scene)
        self.btn_next.pack(side="right")
        
        # Prompt Area
        self.prompt_frame = ttk.Frame(self.main_area)
        self.prompt_frame.pack(side="top", fill="x", padx=20)
        ttk.Label(self.prompt_frame, text="Scene Prompt (Editable):", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.txt_prompt = tk.Text(self.prompt_frame, height=3, font=("Segoe UI", 12), bg="#2D2D30", fg="#FFFFFF", insertbackground="#FFFFFF", relief="flat", padx=10, pady=10)
        self.txt_prompt.pack(fill="x", pady=5)
        
        # Image Grid Canvas
        self.canvas_container = ttk.Frame(self.main_area)
        self.canvas_container.pack(side="top", expand=True, fill="both", padx=20, pady=10)
        
        self.image_canvas = tk.Canvas(self.canvas_container, bg="#1E1E1E", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.image_canvas.yview)
        
        self.image_frame = ttk.Frame(self.image_canvas)
        self.image_frame.bind("<Configure>", lambda e: self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all")))
        
        self.image_canvas.bind('<Configure>', lambda e: self.image_canvas.itemconfig('frame', width=self.image_canvas.winfo_width()))
        self.image_canvas.create_window((0, 0), window=self.image_frame, anchor="nw", tags="frame")
        
        self.scrollbar.pack(side="right", fill="y")
        self.image_canvas.pack(side="left", expand=True, fill="both")
        self.image_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Mousewheel binding
        def _on_mousewheel(event):
            self.image_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        self.image_canvas.bind('<Enter>', lambda e: self.image_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.image_canvas.bind('<Leave>', lambda e: self.image_canvas.unbind_all("<MouseWheel>"))
        
        # Bottom Controls
        self.bottom_frame = ttk.Frame(self.main_area)
        self.bottom_frame.pack(side="bottom", fill="x", pady=20, padx=20)
        
        ttk.Button(self.bottom_frame, text="↻ Reload Data", command=self.reload_data).pack(side="left")
        
        ttk.Button(self.bottom_frame, text="Exit Application", style="Danger.TButton", command=self.destroy).pack(side="right", padx=(10, 0))
        ttk.Button(self.bottom_frame, text="▶ Video Process", command=self.video_process).pack(side="right")

    def reload_data(self):
        self.load_data()
        self.display_current_scene()

    def load_data(self):
        self.batches = {}
        self.prompts = {}
        total_images = 0
        
        if os.path.exists(IMAGE_DIR):
            for file in os.listdir(IMAGE_DIR):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    parts = file.split('_')
                    if len(parts) > 0:
                        scene_prefix = parts[0]
                        if scene_prefix not in self.batches:
                            self.batches[scene_prefix] = []
                        self.batches[scene_prefix].append(os.path.join(IMAGE_DIR, file))
                        total_images += 1
                        
        for scene in self.batches:
            self.batches[scene].sort()
            
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Try to map prompts using common structures
                for item in data.get('scene_visuals', []):
                    scene_id = f"scene{item.get('scene', '')}"
                    self.prompts[scene_id] = item.get('primary_visual_image', "")
            except Exception as e:
                print(f"[ERROR] Loading JSON: {e}")
                
        self.scene_keys = sorted(list(self.batches.keys()))
        self.lbl_total_scenes.config(text=f"Unique Scenes: {len(self.scene_keys)}")
        self.lbl_total_images.config(text=f"Total Images: {total_images}")
        
        if not self.scene_keys:
            self.lbl_scene_name.config(text="No Scenes Available")

    def display_current_scene(self):
        for widget in self.image_frame.winfo_children():
            widget.destroy()
            
        self.photo_refs.clear()
        
        if not self.scene_keys:
            ttk.Label(self.image_frame, text="No images found in directory.", font=("Segoe UI", 12)).pack(pady=20)
            return
            
        scene_key = self.scene_keys[self.current_scene_index]
        self.lbl_scene_name.config(text=f"Scene: {scene_key.upper()}  ({self.current_scene_index + 1} of {len(self.scene_keys)})")
        
        self.txt_prompt.delete("1.0", tk.END)
        prompt_text = self.prompts.get(scene_key, "No prompt available for this scene.")
        self.txt_prompt.insert(tk.END, prompt_text)
        
        images = self.batches.get(scene_key, [])
        cols = 2
        
        for idx, img_path in enumerate(images):
            row = idx // cols
            col = idx % cols
            
            card = ttk.Frame(self.image_frame, style="Card.TFrame", padding=15)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            try:
                if HAS_PIL:
                    pil_img = Image.open(img_path)
                    # Resize while keeping aspect ratio
                    pil_img.thumbnail((450, 350), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    self.photo_refs.append(photo)
                    lbl_img = tk.Label(card, image=photo, bg="#2D2D30")
                else:
                    # Fallback to tk.PhotoImage if PIL is missing, scaling only works for subsets
                    photo = tk.PhotoImage(file=img_path)
                    self.photo_refs.append(photo)
                    lbl_img = tk.Label(card, image=photo, bg="#2D2D30")
                
                lbl_img.pack(pady=(0, 10))
                
                btn_frame = ttk.Frame(card)
                btn_frame.pack(fill="x")
                
                # Delete Rest Button
                btn_keep = ttk.Button(btn_frame, text="Keep & Delete Rest", 
                                      command=lambda p=img_path, s=scene_key: self.keep_one_delete_rest(s, p))
                btn_keep.pack(side="left", expand=True, padx=5)
                
                # Regenerate Button
                btn_regen = ttk.Button(btn_frame, text="Edit Prompt & Regen", 
                                       command=lambda p=img_path: self.regenerate_image(p))
                btn_regen.pack(side="right", expand=True, padx=5)
                
            except Exception as e:
                lbl_err = ttk.Label(card, text=f"[Image Loading Error]\n{os.path.basename(img_path)}")
                lbl_err.pack(pady=20)

    def keep_one_delete_rest(self, scene_key, keep_path):
        if messagebox.askyesno("Confirm Deletion", "This will delete all other images in this batch permanently. Proceed?"):
            images = self.batches.get(scene_key, [])
            for img_path in images:
                if img_path != keep_path:
                    try:
                        os.remove(img_path)
                        print(f"[REMOVED] {img_path}")
                    except Exception as e:
                        print(f"[WARN] Failed to remove {img_path}: {e}")
            self.reload_data()

    def regenerate_image(self, target_img_path):
        new_prompt = self.txt_prompt.get("1.0", tk.END).strip()
        messagebox.showinfo("Regeneration Triggered", 
                           f"Processing Regeneration for:\n{target_img_path}\n\nUsing Prompt:\n{new_prompt}")
        
        Image_prompts_regen=[]

        scene_key = self.scene_keys[self.current_scene_index]
        scene_number = int(scene_key.replace("scene", ""))

        Image_prompts_regen.append({
            "scene": scene_number,
            "prompt": new_prompt
        })
        
        print(f"[REGENERATE] File: {target_img_path} | Prompt: {new_prompt}")
        threading.Thread(
            target=lambda: asyncio.run(Image_pipeline(Image_prompts_regen)),
            daemon=True
        ).start()

    def video_process(self):
        messagebox.showinfo("Video Process", "Initiating Video Processing pipeline for all selected scenes...")
        print("[PROCESS] Video Process Initiated.")

    def prev_scene(self):
        if self.scene_keys:
            self.current_scene_index = (self.current_scene_index - 1) % len(self.scene_keys)
            self.display_current_scene()

    def next_scene(self):
        if self.scene_keys:
            self.current_scene_index = (self.current_scene_index + 1) % len(self.scene_keys)
            self.display_current_scene()


async def Image_pipeline(scenes: list) -> None:
    """
    Full pipeline:
      - Generate image(s)
      - For every output image, launch a video gen job concurrently
    """
    print("Pipeline Activated")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        # Launch image generation for every prompt
        image_tasks = [
            asyncio.create_task(run_Flux_Image_Gen(scene, executor))
            for scene in scenes   # EACH scene is a dict
        ]

        image_results = await asyncio.gather(*image_tasks)

        # Flatten list (because each prompt returns a list of image paths)
        image_paths = []
        for result in image_results:
            image_paths.extend(result)

        print(f"[MAIN] ✔ Generated {len(image_paths)} image(s)")

if __name__ == "__main__":
    app = CorporateUIApp()
    app.mainloop()
