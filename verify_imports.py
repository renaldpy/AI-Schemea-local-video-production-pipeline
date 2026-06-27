import sys
import os

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting verification...")

try:
    from PIL import Image, ImageTk
    print("[OK] Successfully imported PIL (Pillow)")
except ImportError:
    print("[WARN] PIL (Pillow) is NOT installed. JPG images will not display correctly.")
except Exception as e:
    print(f"[FAIL] Error importing PIL: {e}")

try:
    from AI_App import CorporateUIApp
    print("[OK] Successfully imported CorporateUIApp from AI_App")
except Exception as e:
    print(f"[FAIL] Failed to import CorporateUIApp from AI_App: {e}")

try:
    from MAIN_AI_PIPELINE import run_Flux_Image_Gen
    print("[OK] Successfully imported run_Flux_Image_Gen from MAIN_AI_PIPELINE")
except Exception as e:
    print(f"[FAIL] Failed to import run_Flux_Image_Gen from MAIN_AI_PIPELINE: {e}")

try:
    from pipeline_tasks import run_Flux_Image_Gen, run_WAN_I2V_Gen
    print("[OK] Successfully imported tasks from pipeline_tasks")
except Exception as e:
    print(f"[FAIL] Failed to import tasks from pipeline_tasks: {e}")

print("Verification complete.")
