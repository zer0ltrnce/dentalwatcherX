# DentalWatcher X v3.17.0+
[![Version](https://img.shields.io/badge/version-3.17.0%2B-blue.svg)](https://github.com/zer0ltrnce/DentalWatcherX) <!-- Optional: Replace with your actual repo link -->
[![Python Version](https://img.shields.io/badge/python-3.x-brightgreen.svg)](https://www.python.org/)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)


## Overview

DentalWatcher X is a desktop application designed to streamline the workflow of dental technicians and CAD designers using software like Exocad. It automates the often tedious process of identifying, organizing, and transferring completed design files (*.constructionInfo, *cad.stl) and 3D printable models (*model*.stl) from your working directory (e.g., CAD-DATA) to designated network or local folders for CAM processing and 3D printing.

This tool eliminates manual searching and copying, reducing errors and saving valuable time in the dental lab production chain.
![2](https://github.com/user-attachments/assets/efb767d3-779f-40f0-a254-9f4527eab47b)
![1](https://github.com/user-attachments/assets/022ae562-44f6-47f5-8053-6cf3e915c6b5)



# [DOWNLOAD WINDOWS VERSION](https://github.com/zer0ltrnce/dentalwatcherX/releases/tag/production)

## Key Features

*   **Automated Project Scanning:** Scans your designated 'Watch Folder' for dental projects modified within the current day.
*   **Flexible Scan Triggers:**
    *   **Manual Scan:** Initiate a scan via the UI button.
    *   **Hotkey Scan:** Trigger a scan using a configurable global hotkey (default: `Ctrl+Alt+F7`).
    *   **Real-time Monitoring (Optional):** Automatically detects newly saved or modified relevant project files (`*.constructionInfo`, `*cad.stl`, `*model*.stl`) if the `watchdog` library is installed.
*   **Targeted File Transfer:** Send CAM-related files (`*.constructionInfo`, all `*cad.stl` files) and Print-related files (`*model*.stl`) to separate, user-defined target folders.
*   **Intelligent File Recognition:** Specifically identifies `.constructionInfo` files, multiple `*cad.stl` files per project for CAM, and various model files (e.g., `model.stl`, `modelbase.stl`, `upper_model.stl`) for printing.
*   **Automatic Daily Archiving:** A key feature to prevent clutter in your target folders. Before copying new files, the application automatically moves any files from the *previous days* found in the root of the target folders into structured subdirectories (`YYYY/MM/DD`) based on their last modification date. This keeps your main target directories clean and contains only the current day's work.
*   **Real-time Notifications (Optional):** If file monitoring is active, receive desktop popup notifications for newly changed projects, offering quick actions like 'Send to CAM', 'Send to Print', or '3D Preview' (requires cooldown period to avoid spam).
*   **Configurable Auto-Send (Optional):** Set the application to automatically send required files to their respective target folders once detected by the real-time monitor (runs once per project, per type, per day).
*   **Integrated 3D STL Viewer (Optional):** Preview `*cad.stl` and `*model*.stl` files directly within the application (requires `vtk` library).
*   **Duplicate File Handling:** Configure how the application handles files that already exist in the target destination (Ask User, Overwrite, Skip). Separate settings for manual and automatic operations prevent unwanted interruptions during auto-send.
*   **Clear User Interface:** Displays detected projects in a sortable table with status indicators (CAM/Info/Print files present), patient details, work type, and relative time.
*   **Configurable Settings:** Easily configure watch/target folders, hotkeys, archiving, notification behavior, and duplicate handling via the Settings dialog.

## How it Works

1.  **Configuration:** Define your main 'Watch Folder' (where your CAD software saves projects, e.g., `Exocad\CAD-Data`), a 'Target Folder (CAM)', and a 'Target Folder (Print)'.
2.  **Scanning:**
    *   **Manual/Hotkey:** The application scans the entire Watch Folder for projects modified today.
    *   **Real-time:** The application monitors the Watch Folder for specific file creation/modification events (`.constructionInfo`, `*cad.stl`, `*model*.stl`).
3.  **Processing:** When a project is identified (either through scanning or real-time detection):
    *   It parses the `.dentalProject` file (if found) for details like Patient Name, Work Type, and Teeth.
    *   It checks for the presence of associated `.constructionInfo`, `*cad.stl` (all of them), and `*model*.stl` files within the project folder.
    *   Results are displayed in the main table.
4.  **Actions:**
    *   **Manual:** Select projects in the table and use the 'Send to CAM' or 'Send to Print' buttons (or right-click context menu).
    *   **Notification Popup:** If enabled and triggered, use the popup buttons for immediate action on a single project.
    *   **Auto-Send:** If enabled, the application automatically initiates the 'Send to CAM' or 'Send to Print' process when the necessary files are detected for a project that hasn't been auto-sent today.
5.  **File Transfer & Archiving:**
    *   Before copying files to a target folder, **if Archiving is enabled**, the application checks the *root* of that target folder for any files modified *before* the current date.
    *   These older files are **moved** into a `YYYY/MM/DD` subfolder structure within the target folder (e.g., `TargetFolder/2023/10/26/`).
    *   Only then are the *new* files for the selected/detected project copied into the (now clean) root of the target folder.
    *   Duplicate file handling rules (Ask/Overwrite/Skip) are applied during the copy process based on your settings.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/zer0ltrnce/DentalWatcherX.git # Replace with your actual repo URL if different
    cd DentalWatcherX
    ```
2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
   
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *   **Note:** `requirements.txt` should list `PyQt6` as the core requirement.

4.  **Optional Dependencies:** For full functionality, install the following:
    *   **Real-time Monitoring & Auto-Send:** `pip install watchdog`
    *   **Global Hotkey:** `pip install keyboard` (*Note: May require administrator/root privileges to function globally.*)
    *   **3D STL Viewer:** `pip install vtk` (*Ensure it's a version compatible with PyQt6, often requires specific wheels or compilation.*)
    *   **Dummy Icon Generation (if `icon.png` is missing):** `pip install Pillow`

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```
2.  **Initial Configuration:**
    *   On first run, or via the **File -> Settings** menu (or the ⚙️ button), configure your **Watch Folder**, **Target Folder (CAM)**, and **Target Folder (Print)**.
    *   Adjust other settings like the hotkey, archiving, notifications, auto-send, and duplicate handling as needed.
3.  **Operation:**
    *   Click the **Scan** button or use the configured hotkey to manually populate the project list.
    *   If real-time monitoring is active, the application will detect changes automatically.
    *   Select rows in the table and use the **Send to CAM** / **Send to Print** buttons for manual transfer.
    *   Right-click on a row for context menu actions (Send, Open Folders).
    *   Double-click a row to open the STL Viewer (if VTK is available and STLs exist).
    *   Interact with notification popups when they appear (if enabled).
    *   Use the main 'Open CAM Target' / 'Open Print Target' buttons or File menu options to quickly access the destination folders.
    *   The application can be minimized to the system tray. Use the tray icon menu for quick actions (Show, Scan, Settings, Quit).

## About the Author


My name is David Kamarauli (**zer0ltrnce**), and I work as a Dental Technician and CAD Designer. As a self-taught Python developer and DevOps enthusiast, I created this enhanced version of DentalWatcher X primarily to automate repetitive tasks in my own daily workflow and add features like multi-CAD STL handling and improved real-time monitoring.

[smiledesigner.us](https://smiledesigner.us) [@davidkamarauli](https://www.instagram.com/davidkamaraulli).

Witnessing the potential for efficiency gains through simple automation in the dental lab environment inspired this project. We firmly believe in the power of open-source collaboration to improve our industry.

If you find this tool useful, or if you are interested in custom automation solutions tailored to your dental laboratory's specific needs, feel free to reach out (zerotlrnce@gmail.com).

## Contributing

Contributions, issues, and feature requests are welcome! Please feel free to open an issue or submit a pull request.

## License

Distributed under the GNU\GPL licence. See `LICENSE` file for more information.
