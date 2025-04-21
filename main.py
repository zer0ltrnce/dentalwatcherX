# Project: dental_watcher_v3.17.0.py  - Main Entry Point
# Author: zer0ltrnce (@zer0ltrnce, zerotlrnce@gmail.com)
# GitHub: https://github.com/zer0ltrnce
# Original Author: David Kamarauli (smiledesigner.us)
# Version: 3.17.0+

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui import MainWindow, HotkeySignalEmitter, WatchdogSignalEmitter

from core import APP_NAME, ORG_NAME, APP_VERSION, check_or_create_dummy_icon

if __name__ == "__main__":
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'): QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'): QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path: sys.path.insert(0, app_dir)
    os.chdir(app_dir)

    # create the qapplication instance
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG_NAME);
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    check_or_create_dummy_icon()
    hotkey_signal_emitter = HotkeySignalEmitter()
    watchdog_signal_emitter = WatchdogSignalEmitter()
    main_window = MainWindow(hotkey_signal_emitter, watchdog_signal_emitter)
    app.aboutToQuit.connect(main_window.quit_application)

    main_window.show_window()
    print(f"{APP_NAME} v{APP_VERSION} Started...")

    sys.exit(app.exec())
