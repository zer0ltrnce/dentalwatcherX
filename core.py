# Project: dental_watcher_v3.17.0.py - Core Logic
# Author: zer0ltrnce (@zer0ltrnce, zerotlrnce@gmail.com)
# GitHub: https://github.com/zer0ltrnce/exodbhealer
# Original Author: David Kamarauli (smiledesigner.us)
# Version: 3.17.0+


import sys
import os
import shutil
import datetime
import xml.etree.ElementTree as ET
import threading
import time
import json # config stuff

# vtk import and check if available
try:
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
except Exception as e_vtk_load:
    print(f"Error loading VTK: {e_vtk_load}")
    VTK_AVAILABLE = False

# keyboard import section
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
except Exception as e_kbd_load:
    print(f"Error loading keyboard: {e_kbd_load}")
    KEYBOARD_AVAILABLE = False

# watchdog import for file monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    FileSystemEvent = object
    print("Warning: 'watchdog' library not found. Real-time notifications/auto-send disabled.")
    print("         Install it using: pip install watchdog")
except Exception as e_wd_load:
    print(f"Error loading watchdog: {e_wd_load}")
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    FileSystemEvent = object

# define constants
APP_NAME = "DentalWatcher X"
ORG_NAME = "KamarauliTech" #
SETTINGS_WATCH_FOLDER = "watch_folder"
SETTINGS_TARGET_FOLDER_CAM = "target_folder_cam"
SETTINGS_MODELS_FOLDER = "target_folder_print"
SETTINGS_HOTKEY = "hotkey"
DEFAULT_HOTKEY = "ctrl+alt+f7"
SETTINGS_ARCHIVE_ENABLED = "archive_enabled"
DEFAULT_ARCHIVE_ENABLED = True
SETTINGS_LAST_ARCHIVE_DATE_CAM = "last_archive_date_cam"
SETTINGS_LAST_ARCHIVE_DATE_PRINT = "last_archive_date_print"
SETTINGS_LIVE_NOTIFY_ENABLED = "live_notify_enabled"
DEFAULT_LIVE_NOTIFY_ENABLED = True
SETTINGS_NOTIFICATION_DEBOUNCE_SECS = "notification_debounce_secs"
DEFAULT_NOTIFICATION_DEBOUNCE_SECS = 45
SETTINGS_AUTO_SEND_ENABLED = "auto_send_enabled"
DEFAULT_AUTO_SEND_ENABLED = False
SETTINGS_DUPLICATE_CHECK_ACTION = "duplicate_check_action" # For manual actions
DEFAULT_DUPLICATE_CHECK_ACTION = "ask" # 'ask', 'overwrite', 'skip'
SETTINGS_AUTO_DUPLICATE_ACTION = "auto_duplicate_action" # For auto-send/triggered updates
DEFAULT_AUTO_DUPLICATE_ACTION = "manual" # 'skip', 'overwrite', 'manual' (use manual setting)
SETTINGS_NETWORK_SCAN_DEPTH = "network_scan_depth"
DEFAULT_NETWORK_SCAN_DEPTH = 0 # 0 for unlimited, effectively relying on os.walk default.

APP_VERSION = "3.17.0+"
AUTO_SEND_STATUS_FILE = "autosend_status.json"

# constants for the vtk viewer
VIEWER_BACKGROUND_COLOR = (0.15, 0.16, 0.18)
VIEWER_MODEL_COLOR = (0.85, 0.85, 0.9)
VIEWER_AXES_ENABLED = True

# some helper functions

def is_network_path(path_str: str) -> bool:
    """
    Basic check for network paths. Primarily for UNC paths on Windows.
    For other OSes, this is less reliable and the depth limit is applied if set.
    """
    if not path_str:
        return False
    # Windows UNC paths
    if os.name == 'nt' and path_str.startswith('\\\\'):
        return True
    # Add other checks if necessary, e.g., for specific mount points on POSIX
    # For now, keep it simple as the depth limit is the main control.
    return False

def shorten_path(p, length=2):
    if not p or p == "Not set" or os.sep not in p: return p
    parts = p.split(os.sep);
    return f"...{os.sep}{os.sep.join(parts[-length:])}" if len(parts) > length + 1 else p

def get_relative_time(timestamp):
    now = datetime.datetime.now();
    dt_object = datetime.datetime.fromtimestamp(timestamp);
    delta = now - dt_object;
    seconds = delta.total_seconds()
    if seconds < 0: return "in the future?";
    if seconds < 5: return "just now";
    if seconds < 60: return f"{int(seconds)}s ago";
    if seconds < 3600: return f"{int(seconds // 60)}m ago";
    if seconds < 86400: return f"{int(seconds // 3600)}h ago";
    if delta.days == 1: return "Yesterday";
    if delta.days < 7: return f"{delta.days}d ago";
    if delta.days < 30: return f"{delta.days // 7}w ago";
    if delta.days < 365: return f"{delta.days // 30}mo ago";
    return f"{delta.days // 365}y ago"


# xml project parser
def parse_dental_project(filepath):
    """Parses .dentalProject XML file, identifies full arches."""
    if not filepath or not os.path.exists(filepath): return None
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        p_name_raw = root.findtext('.//Patient/PatientName', default='?').strip()
        p_parts = [p.strip() for p in p_name_raw.split(',') if p.strip()]
        p_name = p_parts[0] if p_parts else "Patient N/A"
        case_id = root.findtext('.//Patient/PatientFirstName', default='').strip()
        practice = root.findtext('.//Practice/PracticeName', default='').strip()

        work_types = set()
        teeth_numbers = []
        for tooth_element in root.findall('.//Teeth/Tooth'):
            num_text = tooth_element.findtext('Number')
            r_type = tooth_element.findtext('ReconstructionType')

            if not r_type:
                child_elements = list(tooth_element)
                relevant_child = next((el for el in child_elements if
                                       el.tag not in ['Number', 'Parameters', 'MaterialName', 'Material', 'ImplantType',
                                                      'PreparationType', 'Color', 'MesialConnector', 'ScanAbutmentScan',
                                                      'SeparateGingivaScan', 'SituScan']), None)
                if relevant_child is not None:
                    r_type = relevant_child.tag

            if r_type and r_type.lower() != 'antagonist':
                if num_text:
                    try:
                        teeth_numbers.append(int(num_text))
                    except ValueError:
                        pass
                if r_type:
                    display_rtype = r_type.replace('_', ' ').title()
                    work_types.add(display_rtype)

        teeth_numbers = sorted(list(set(teeth_numbers)))

        # full arch logic here
        upper_teeth = [t for t in teeth_numbers if 11 <= t <= 28]
        lower_teeth = [t for t in teeth_numbers if 31 <= t <= 48]
        other_teeth = [t for t in teeth_numbers if not (11 <= t <= 28 or 31 <= t <= 48)]

        teeth_parts = []
        if len(upper_teeth) >= 8:
            teeth_parts.append("Full Arch Upper")
        elif upper_teeth:
            teeth_parts.append(", ".join(map(str, upper_teeth)))

        if len(lower_teeth) >= 8:
            teeth_parts.append("Full Arch Lower")
        elif lower_teeth:
            teeth_parts.append(", ".join(map(str, lower_teeth)))

        if other_teeth:
            teeth_parts.append(", ".join(map(str, other_teeth)))

        tooth_str = ", ".join(teeth_parts) if teeth_parts else "?"

        if work_types:
            work_str = ", ".join(sorted(list(work_types)))
        elif not teeth_numbers and any(
                t.findtext('ReconstructionType', '').lower() == 'antagonist' for t in root.findall('.//Teeth/Tooth')):
            work_str = "Antagonist?"
        else:
            work_str = "Type N/A"

        disp_p = f"{p_name}" + (f" ({case_id})" if case_id else "")

        return {
            "patient": disp_p,
            "practice": practice,
            "work_type": work_str,
            "teeth": tooth_str,
            "filename": os.path.basename(filepath),
            "case_id": case_id
        }

    except ET.ParseError:
        print(f"XML parse error in: {filepath}")
        return None
    except Exception as e_parse:
        print(f"Unexpected error parsing {filepath}: {e_parse}")
        return None


# directory scanner function
def scan_directory(watch_folder, target_folder=None, network_scan_depth=DEFAULT_NETWORK_SCAN_DEPTH):
    """
    Scans the watch_folder (or a specific target_folder within it)
    for projects modified today OR (if target_folder is specified) projects
    containing files modified today. Uses updated file classification for CAM/Print relevance.
    Handles multiple *cad.stl files.
    Applies network_scan_depth if scanning the whole watch_folder and depth > 0.
    """
    scan_root_is_watch_folder = not target_folder # True if we are scanning the main watch_folder
    scan_root = watch_folder if scan_root_is_watch_folder else target_folder

    if not scan_root or not os.path.isdir(scan_root):
        print(f"Scan error: root path invalid '{scan_root}'")
        return []

    today_date = datetime.date.today()
    found_projects = []
    processed_folders = set() # Used to avoid re-processing if symlinks or weird structures exist

    # Determine the initial list of directories to scan
    if not scan_root_is_watch_folder: # Scanning a specific target_folder (e.g., from watcher trigger)
        try:
            items_list = os.listdir(scan_root)
            # Structure for os.walk: (root, dirnames, filenames)
            root_dirs_iter = [(scan_root, [d for d in items_list if os.path.isdir(os.path.join(scan_root, d))],
                                         [f for f in items_list if os.path.isfile(os.path.join(scan_root, f))])]
        except FileNotFoundError:
            print(f"Scan warning: Target folder not found during scan: {scan_root}")
            return []
        except Exception as e:
            print(f"Scan error: Error listing target folder {scan_root}: {e}")
            return []
    else: # Full scan of watch_folder
        # os.walk is a generator, which is good.
        # We need to normalize watch_folder path for correct depth calculation.
        normalized_watch_folder = os.path.normpath(watch_folder)
        root_dirs_iter = os.walk(normalized_watch_folder, topdown=True)


    for current_root, dirs, files in root_dirs_iter:
        current_folder_norm = os.path.normpath(current_root)

        if scan_root_is_watch_folder: # Apply depth limiting and archive skipping only for full watch_folder scans
            # Depth calculation
            # Ensure current_root starts with normalized_watch_folder for correct relative path
            if current_folder_norm.startswith(normalized_watch_folder):
                relative_path = current_folder_norm[len(normalized_watch_folder):].lstrip(os.sep)
                depth = relative_path.count(os.sep) if relative_path else 0
            else: # Should not happen if os.walk is used correctly with watch_folder
                depth = 0 

            if network_scan_depth > 0 and depth >= network_scan_depth:
                print(f"[Scan Depth] Reached depth limit ({network_scan_depth}) at '{current_folder_norm}'. Pruning dirs: {dirs}")
                dirs[:] = [] # Don't go deeper

            # Archive path skipping logic (remains unchanged)
            is_likely_archive_path = False
            basename = os.path.basename(current_folder_norm)
            parent_dir = os.path.dirname(current_folder_norm)
            parent_basename = os.path.basename(parent_dir)
            grandparent_dir = os.path.dirname(parent_dir)
            grandparent_basename = os.path.basename(grandparent_dir)

            if basename.isdigit() and len(basename) == 2: # DD
                if parent_basename.isdigit() and len(parent_basename) == 2: # MM
                    if grandparent_basename.isdigit() and len(grandparent_basename) == 4: # YYYY
                        is_likely_archive_path = True
            elif parent_basename.isdigit() and len(parent_basename) == 4: # YYYY
                 if basename.isdigit() and len(basename) == 2: # MM (less common structure, but possible)
                    # This could be YYYY/MM, check if dirs contains DD
                    # For simplicity, we'll stick to YYYY/MM/DD as the primary archive marker
                    pass


            if is_likely_archive_path:
                print(f"[Scan Depth] Skipping likely archive path: {current_folder_norm}")
                dirs[:] = [] # Prune archive subfolders
                continue # Don't process files in this folder either, go to next item from os.walk

            if current_folder_norm in processed_folders: # Avoid reprocessing (e.g. symlink loops)
                print(f"[Scan Depth] Already processed, skipping: {current_folder_norm}")
                dirs[:] = [] # Don't descend again
                continue
            processed_folders.add(current_folder_norm)

        folder_modified_today = False
        latest_mtime_today = 0.0
        relevant_files_in_folder = []

        for filename in files:
            filepath = os.path.join(current_folder_norm, filename) # Use normalized current_folder_norm
            try:
                filename_lower = filename.lower()
                ext_lower = os.path.splitext(filename_lower)[1]
                if ext_lower not in [".dentalproject", ".constructioninfo", ".stl"]:
                    continue

                if not os.path.isfile(filepath): continue # Should not happen with os.walk files list

                mtime_ts = os.path.getmtime(filepath)
                base_name_lower = os.path.splitext(filename_lower)[0]

                is_project = ext_lower == ".dentalproject"
                is_info = ext_lower == ".constructioninfo"
                is_stl = ext_lower == ".stl"

                is_cad_stl = False
                is_model_stl = False
                is_other_stl = False

                if is_stl:
                    if filename_lower.endswith("cad.stl"):
                        is_cad_stl = True
                    elif "model" in base_name_lower: # Covers *model*.stl, *models*.stl etc.
                        is_model_stl = True
                    else:
                        is_other_stl = True

                mtime_date = datetime.date.fromtimestamp(mtime_ts)
                if mtime_date == today_date:
                    folder_modified_today = True
                    latest_mtime_today = max(latest_mtime_today, mtime_ts)

                file_info = {
                    'path': filepath, 'name': filename, 'base': os.path.splitext(filename)[0],
                    'is_project': is_project, 'is_info': is_info, 'is_stl': is_stl,
                    'is_cad_stl': is_cad_stl, 'is_model_stl': is_model_stl, 'is_other_stl': is_other_stl,
                    'mtime': mtime_ts
                }
                relevant_files_in_folder.append(file_info)
            except FileNotFoundError: # File might disappear during scan
                continue
            except Exception as e_file: # Catch other errors reading file properties
                print(f"Error processing file '{filepath}': {e_file}")
                continue

        # After processing all files in current_root, decide if this folder is a project
        # A folder is considered a project if it contains files modified today,
        # OR if we are scanning a specific target_folder (triggered by watcher).
        if folder_modified_today or not scan_root_is_watch_folder:
            project_files = sorted([f for f in relevant_files_in_folder if f['is_project']], key=lambda x: x['mtime'], reverse=True)
            
            if not project_files: # No .dentalProject file
                if not scan_root_is_watch_folder: # If it's a specific target_folder scan (watcher)
                    project_base_name = os.path.basename(current_folder_norm)
                    project_path = None
                    parsed_data = {"patient": project_base_name, "practice": "N/A", "work_type": "N/A", "teeth": "?", "filename": "N/A", "case_id": ""}
                else: # Full scan and no .dentalProject file, skip this folder
                    continue 
            else: # Has .dentalProject file(s)
                project_file_info = project_files[0] # Use the most recent one
                project_path = project_file_info['path']
                project_base_name = project_file_info['base']
                parsed_data = parse_dental_project(project_path)
                if not parsed_data: # Parsing failed
                    parsed_data = {
                        "patient": project_base_name, "practice": "N/A",
                        "work_type": "Parse Error", "teeth": "?",
                        "filename": project_file_info['name'], "case_id": ""
                    }

            # Gather associated files based on project_base_name or any relevant files if base_name is generic
            info_file = next((f for f in relevant_files_in_folder if f['is_info'] and f['base'] == project_base_name), None)
            if not info_file: info_file = next((f for f in relevant_files_in_folder if f['is_info']), None) # Fallback: any info file
            info_path = info_file['path'] if info_file else None

            cad_stl_files = [f for f in relevant_files_in_folder if f['is_cad_stl']]
            cad_stl_paths = [f['path'] for f in cad_stl_files] # Collect all CAD STLs

            model_stl_paths = [f['path'] for f in relevant_files_in_folder if f['is_model_stl']]
            other_stl_paths = [f['path'] for f in relevant_files_in_folder if f['is_other_stl']]
            
            has_cad = bool(cad_stl_paths)
            has_info = bool(info_path)
            has_models = bool(model_stl_paths)

            cam_icon = "✓" if has_cad else "✗"; info_icon = "✓" if has_info else "✗"; print_icon = "✓" if has_models else "✗"
            file_status_display = f"{cam_icon}C {info_icon}I {print_icon}P"

            # Determine the timestamp for sorting:
            # If scanning a specific target folder, use its mtime or latest file mtime.
            # If full scan, use the latest file mtime from today.
            timestamp_to_use = latest_mtime_today
            if not scan_root_is_watch_folder: # target_folder scan
                 timestamp_to_use = os.path.getmtime(current_folder_norm) if os.path.exists(current_folder_norm) else time.time()
                 if relevant_files_in_folder: # If files were found, use the newest one
                     timestamp_to_use = max(f['mtime'] for f in relevant_files_in_folder)
            
            project_entry = {
                "last_modified_timestamp": timestamp_to_use,
                "patient": parsed_data.get('patient', project_base_name),
                "work_type": parsed_data.get('work_type', 'N/A'),
                "teeth": parsed_data.get('teeth', '?'),
                "file_status": file_status_display, "base_name": project_base_name,
                "project_path": project_path, "info_path": info_path,
                "cad_stl_paths": cad_stl_paths, "other_stl_paths": other_stl_paths,
                "model_stl_paths": model_stl_paths, "parsed_data": parsed_data,
                "folder_path": current_folder_norm,
                "has_cad": has_cad, "has_info": has_info, "has_models": has_models,
                "status_icons": (cam_icon, info_icon, print_icon)
            }
            found_projects.append(project_entry)

            if not scan_root_is_watch_folder: # If scanning a specific target_folder, we are done with this single iteration.
                 break 

    found_projects.sort(key=lambda x: x['last_modified_timestamp'], reverse=True)
    return found_projects


# watchdog file system event handler
if WATCHDOG_AVAILABLE:
    class WatcherEventHandler(FileSystemEventHandler):
        """Handles file system events, triggers popups/auto-send for specific files."""
        last_processed_time = {}
        DEBOUNCE_SECONDS = 1.0

        def __init__(self, signal_emitter, watch_path):
            super().__init__()
            self.signal_emitter = signal_emitter
            self.watch_path_norm = os.path.normpath(watch_path) if watch_path else None
            print(f"[WatcherEventHandler] Initialized for path: {self.watch_path_norm}")

        def _is_relevant_change(self, event_path):
            """Checks if the file path change is relevant based on specific file types and is within the watched path."""
            if not event_path or not self.watch_path_norm:
                return False

            try:
                abs_event_path = os.path.abspath(event_path)
                event_path_norm = os.path.normpath(abs_event_path)

                if not event_path_norm.startswith(self.watch_path_norm):
                     return False

            except Exception as e:
                print(f"[WatcherEventHandler] Path check error for '{event_path}': {e}")
                return False

            filename = os.path.basename(event_path)
            filename_lower = filename.lower()
            base_name_lower, ext_lower = os.path.splitext(filename_lower)

            if ext_lower == ".constructioninfo":
                return True

            if ext_lower == ".stl":
                if filename_lower.endswith("cad.stl"):
                    return True
                if "model" in base_name_lower:
                    return True

            return False

        def _emit_signal_debounced(self, event_path):
            """Emits the file change signal if the event is relevant and not debounced."""
            abs_event_path = os.path.abspath(event_path)
            now = time.time()
            last_time = self.last_processed_time.get(abs_event_path, 0)

            if self._is_relevant_change(event_path):
                 if (now - last_time > self.DEBOUNCE_SECONDS):
                    self.last_processed_time[abs_event_path] = now
                    print(f"[WatcherEventHandler] Change detected & debounced: {event_path}")
                    try:
                        self.signal_emitter.file_change_detected.emit(event_path)
                    except RuntimeError:
                        print("[WatcherEventHandler] Warning: Could not emit signal, likely main window closing.")
                        pass
                    except Exception as e:
                        print(f"[WatcherEventHandler] Error emitting watchdog signal: {e}")

        def on_created(self, event: FileSystemEvent):
            if not event.is_directory:
                self._emit_signal_debounced(event.src_path)

        def on_modified(self, event: FileSystemEvent):
            if not event.is_directory:
                self._emit_signal_debounced(event.src_path)
else:
    # Dummy class if watchdog isn't available
    class WatcherEventHandler(object):
        def __init__(self, signal_emitter, watch_path): pass
        def on_created(self, event): pass
        def on_modified(self, event): pass


# hotkey listener thread class
class HotkeyListener(threading.Thread):
    def __init__(self, hotkey_combo, signal_emitter):
        super().__init__(daemon=True, name=f"HotkeyListener-{hotkey_combo}")
        self.hotkey_combo = hotkey_combo
        self.signal_emitter = signal_emitter
        self._running = True
        self.enabled = True  # New instance variable
        self._hooked_key_ref = None
        self._last_emit_time = 0
        self._debounce_interval = 0.3

    def run(self):
        """Main loop for the listener thread."""
        if not KEYBOARD_AVAILABLE: return
        try:
            def _callback_wrapper():
                current_time = time.time()
                if self._running and self.enabled and (current_time - self._last_emit_time > self._debounce_interval):
                    self._last_emit_time = current_time
                    try:
                        self.signal_emitter.hotkey_pressed.emit()
                    except RuntimeError: pass
                    except Exception as e: print(f"[Hotkey Listener] Signal emit failed: {e}")

            if not self.hotkey_combo: print("[Hotkey Listener ERROR] Hotkey is empty, cannot register."); self._running = False; return
            self._hooked_key_ref = keyboard.add_hotkey(self.hotkey_combo, _callback_wrapper, trigger_on_release=False, suppress=False)
            print(f"[Hotkey Listener] Hotkey '{self.hotkey_combo}' registered.")
            while self._running: time.sleep(0.1)
        except ImportError: self._running = False; print("[Hotkey Listener ERROR] Keyboard library gone during run?")
        except ValueError as e: self._running = False; print(f"[Hotkey Listener ERROR] Invalid hotkey format during run: {e}")
        except Exception as e: self._running = False; print(f"[Hotkey Listener ERROR] Listener exception: {e}")
        finally:
            print(f"[Hotkey Listener] Listener ({self.hotkey_combo}) thread exiting run loop.");
            self.remove_hook() # Ensure hook is removed on exit

    def enable_action(self):
        self.enabled = True
        print(f"[Hotkey Listener] Action for '{self.hotkey_combo}' ENABLED.")

    def disable_action(self):
        self.enabled = False
        print(f"[Hotkey Listener] Action for '{self.hotkey_combo}' DISABLED.")

    def remove_hook(self):
        """Removes the registered hotkey hook."""
        if not KEYBOARD_AVAILABLE or not self._hooked_key_ref: return
        hook_to_remove = self._hooked_key_ref; self._hooked_key_ref = None
        try:
            keyboard.remove_hotkey(hook_to_remove);
            print(f"[Hotkey Listener] Hotkey '{self.hotkey_combo}' removed.")
        except KeyError: pass
        except Exception as e: print(f"[Hotkey Listener DEBUG] Exception removing hotkey hook (ignored): {e}")

    def stop(self):
        """Sets the running flag to False to stop the thread loop and removes the hook."""
        print(f"[Hotkey Listener] Listener ({self.hotkey_combo}) stop() called.")
        self._running = False # Signal thread to stop
        self.remove_hook() # Remove the OS-level hook
        if KEYBOARD_AVAILABLE and self.hotkey_combo:
            try:
                # Attempt to release the last key in the combo to break the listener wait
                parts = self.hotkey_combo.split('+')
                key_to_release = parts[-1].strip()
                if key_to_release:
                    keyboard.release(key_to_release)
            except Exception as e:
                print(f"[Hotkey Listener] Minor issue trying to release key during stop: {e}")


# function for dummy icon generation (used in main.py)
def check_or_create_dummy_icon():
    """Checks for icon.png and creates a dummy one if missing and PIL is available."""
    if not os.path.exists("icon.png"):
        print("icon.png not found, attempting to create a dummy icon...")
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("arial.ttf", 40)
            except IOError: font = ImageFont.load_default()
            draw.rectangle([(4, 4), (60, 60)], fill=(26, 27, 30, 220), outline=(0, 160, 160, 255), width=3)
            draw.text((12, 8), "D", fill=(220, 255, 255, 255), font=font)
            draw.text((32, 16), "X", fill=(0, 229, 229, 255), font=font.font_variant(size=30))
            img.save("icon.png"); print("Dummy icon.png created.")
            return True
        except ImportError:
            print("PIL (Pillow) not found, cannot create dummy icon. Please install (pip install Pillow) or provide an icon.png file.")
            return False
        except Exception as e_icon:
            print(f"Error creating dummy icon: {e_icon}")
            return False
    return True
