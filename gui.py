# Project: dental_watcher_v3.17.0.py  - GUI Elements etc.
# Author: zer0ltrnce (@zer0ltrnce, zerotlrnce@gmail.com)
# GitHub: https://github.com/zer0ltrnce/exodbhealer
# Original Author: David Kamarauli (smiledesigner.us)
# Version: 3.17.0+

import sys
import os
import shutil
import datetime
import webbrowser
from collections import defaultdict
from functools import partial # for callbacks, nifty
import json # config stuff (Used indirectly via MainWindow methods)
import time

# imporft core functionalities
import core
from core import (
    VTK_AVAILABLE, KEYBOARD_AVAILABLE, WATCHDOG_AVAILABLE, Observer,
    WatcherEventHandler, HotkeyListener, shorten_path, get_relative_time,
    scan_directory, parse_dental_project,
    APP_NAME, ORG_NAME, APP_VERSION, DEFAULT_HOTKEY,
    SETTINGS_WATCH_FOLDER, SETTINGS_TARGET_FOLDER_CAM, SETTINGS_MODELS_FOLDER,
    SETTINGS_HOTKEY, SETTINGS_ARCHIVE_ENABLED, DEFAULT_ARCHIVE_ENABLED,
    SETTINGS_LAST_ARCHIVE_DATE_CAM, SETTINGS_LAST_ARCHIVE_DATE_PRINT,
    SETTINGS_LIVE_NOTIFY_ENABLED, DEFAULT_LIVE_NOTIFY_ENABLED,
    SETTINGS_NOTIFICATION_DEBOUNCE_SECS, DEFAULT_NOTIFICATION_DEBOUNCE_SECS,
    SETTINGS_AUTO_SEND_ENABLED, DEFAULT_AUTO_SEND_ENABLED,
    SETTINGS_DUPLICATE_CHECK_ACTION, DEFAULT_DUPLICATE_CHECK_ACTION,
    SETTINGS_AUTO_DUPLICATE_ACTION, DEFAULT_AUTO_DUPLICATE_ACTION,
    AUTO_SEND_STATUS_FILE, VIEWER_BACKGROUND_COLOR, VIEWER_MODEL_COLOR,
    VIEWER_AXES_ENABLED
)

# vtk import and check if available (Specific GUI part)
if VTK_AVAILABLE:
    import vtk
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
else:
    QVTKRenderWindowInteractor = None # placeholder

# keyboard import (Only needed for the listener start/stop logic in MainWindow)
if KEYBOARD_AVAILABLE:
    import keyboard

# pyqt6 imports for the ui
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QSystemTrayIcon, QMenu, QFileDialog,
    QStatusBar, QSizePolicy, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QStyle, QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox, QFrame, QCheckBox, QComboBox
)
from PyQt6.QtGui import QIcon, QAction, QFont, QColor, QDesktopServices, QGuiApplication, QPixmap, QClipboard, \
    QIntValidator
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QObject, QCoreApplication, QTimer, QSize, QUrl

# setup signals for thread communication
# used to talk between threads (hotkey listener -> main, watchdog -> main)
class HotkeySignalEmitter(QObject):
    hotkey_pressed = pyqtSignal()

class WatchdogSignalEmitter(QObject):
    file_change_detected = pyqtSignal(str) # send the path that changed

# application styles (Neon Void theme)
NEON_VOID_STYLE = """
QWidget {
    background-color: #1A1B1E;
    color: #D0D0D5;
    font-family: Segoe UI, Roboto, Open Sans, Arial, sans-serif;
    font-size: 9.8pt;
    border: none;
}
QMainWindow, QDialog {
    background-color: #1A1B1E;
}
QDialog {
    border: 1px solid #3A3C40;
}
QMenuBar {
    background-color: #252629;
    color: #D0D0D5;
    padding: 2px;
    font-size: 9.5pt;
}
QMenuBar::item { padding: 5px 12px; }
QMenuBar::item:selected { background-color: #3A3C40; }
QMenu {
    background-color: #252629;
    color: #D0D0D5;
    border: 1px solid #4A4C50;
    padding: 5px;
}
QMenu::item { padding: 6px 25px 6px 20px; }
QMenu::item:selected {
    background-color: #00A0A0;
    color: #FFFFFF;
}
QMenu::item:disabled {
    color: #606266;
}
QLabel {
    background-color: transparent;
}
QLabel#infoLabel {
    font-size: 10.5pt;
    font-weight: 500;
    padding: 8px 10px;
    color: #E0E0E5;
    background-color: #252629;
    border-radius: 4px;
    min-height: 24px;
}
QLabel#statusBarLabel {
    color: #A0A0A5;
    padding: 0 5px;
    border-left: 1px solid #3A3C40;
    margin-left: 3px;
}
QLabel#statusBarLabel:first-child {
    border-left: none;
    margin-left: 0px;
}
QLabel#statusBarLabel QWidget {
     background-color: transparent;
}
QLabel#viewerStatusLabel {
    padding: 4px 8px;
    color: #B0B0B5;
    font-size: 9pt;
    background-color: #252629;
    border-top: 1px solid #3A3C40;
}
QLabel#notificationInfoLabel {
    font-size: 10pt;
    padding: 10px;
    border: 1px solid #2C2D30;
    background-color: #202124;
    border-radius: 4px;
    margin-bottom: 10px;
}
QPushButton {
    background-color: #2C2D30;
    color: #E0E0E5;
    border: 1px solid #4A4C50;
    padding: 8px 16px;
    border-radius: 4px;
    min-height: 30px;
    font-weight: 500;
    text-align: center;
}
QPushButton:hover {
    background-color: #3A3C40;
    border-color: #606266;
}
QPushButton:pressed {
    background-color: #1A1B1E;
}
QPushButton:disabled {
    background-color: #252629;
    color: #606266;
    border-color: #3A3C40;
}
QPushButton#sendCamButton, QPushButton#sendPrintButton {
    font-weight: 600;
}
QPushButton#sendCamButton:hover, QPushButton#sendPrintButton:hover {
    background-color: #00A0A0;
    border-color: #00E5E5;
    color: #FFFFFF;
}
QPushButton#sendCamButton:pressed, QPushButton#sendPrintButton:pressed {
    background-color: #007A7A;
}
QPushButton#notifySendCamButton, QPushButton#notifySendPrintButton,
QPushButton#notifyPreviewButton {
    font-weight: 500;
    min-height: 32px;
    padding: 6px 12px;
}
QPushButton#notifySendCamButton:hover, QPushButton#notifySendPrintButton:hover {
    background-color: #00A0A0;
    border-color: #00E5E5;
    color: #FFFFFF;
}
QPushButton#notifyPreviewButton:hover {
    background-color: #4a407a;
    border-color: #9080c0;
    color: #FFFFFF;
}
QPushButton#notifyOpenCamFolderButton, QPushButton#notifyOpenPrintFolderButton {
    font-weight: 500;
    min-height: 32px;
    padding: 6px 12px;
}
QPushButton#notifyOpenCamFolderButton:hover, QPushButton#notifyOpenPrintFolderButton:hover {
    background-color: #3A3C40;
    border-color: #606266;
}
QPushButton#openCamFolderButton, QPushButton#openPrintFolderButton {
    font-weight: 500;
    min-height: 30px;
    padding: 8px 12px;
}
QPushButton#settingsButton {
    font-size: 11pt;
    font-weight: bold;
    padding: 5px;
    min-width: 30px; max-width: 30px;
    min-height: 30px; max-height: 30px;
    border-radius: 15px;
    border: 1px solid #00A0A0;
    color: #00E5E5;
    background-color: #2C2D30;
}
QPushButton#settingsButton:hover {
    background-color: #3A3C40;
    border-color: #00FFFF;
    color: #00FFFF;
}
QPushButton#settingsButton:disabled {
    border-color: #4A4C50;
    color: #606266;
    background-color: #252629;
}
QTableWidget {
    background-color: #1A1B1E;
    color: #D0D0D5;
    border: 1px solid #3A3C40;
    gridline-color: transparent;
    alternate-background-color: #202124;
    outline: 0;
    padding: 0px;
    border-radius: 4px;
    selection-background-color: #007A7A;
    selection-color: #FFFFFF;
}
QTableWidget::item {
    padding: 10px 8px;
    border: none;
    border-bottom: 1px solid #2C2D30;
    min-height: 26px;
}
QHeaderView {
    border: none;
    font-size: 9.5pt;
}
QHeaderView::section {
    background-color: #252629;
    color: #A0A0A5;
    padding: 9px 6px;
    border: none;
    border-bottom: 1px solid #4A4C50;
    font-weight: 600;
    min-height: 34px;
}
QHeaderView::section:horizontal {
    border-right: 1px solid #3A3C40;
}
QHeaderView::section:horizontal:last {
    border-right: none;
}
QToolTip {
    background-color: #252629; color: #E0E0E5; border: 1px solid #505256;
    padding: 5px; font-size: 9.2pt;
    border-radius: 3px;
}
QStatusBar {
    background-color: #252629;
    border-top: 1px solid #4A4C50;
    color: #A0A0A5;
    font-size: 9pt;
    font-weight: normal;
    padding: 3px 5px;
}
QStatusBar::item {
    border: none;
}
QLineEdit {
    background-color: #2C2D30; border: 1px solid #505256; padding: 6px 8px;
    border-radius: 3px; color: #D0D0D5; min-height: 26px;
}
QLineEdit:read-only {
    background-color: #202124; color: #808085; border-color: #404246;
}
QLineEdit:focus {
    border-color: #00A0A0;
}
QComboBox {
    background-color: #2C2D30; border: 1px solid #505256; padding: 4px 8px;
    border-radius: 3px; color: #D0D0D5; min-height: 26px;
    selection-background-color: #007A7A;
}
QComboBox:hover { border-color: #707276; }
QComboBox:focus { border-color: #00A0A0; }
QComboBox::drop-down {
    subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
    border-left: 1px solid #505256; border-top-right-radius: 3px; border-bottom-right-radius: 3px;
    background-color: #2C2D30;
}
QComboBox::down-arrow { width: 10px; height: 10px; }
QComboBox QAbstractItemView {
    background-color: #252629; color: #D0D0D5; border: 1px solid #4A4C50;
    selection-background-color: #00A0A0; selection-color: #FFFFFF; padding: 4px;
}
QDialogButtonBox QPushButton {
    min-width: 90px;
}
QCheckBox {
    spacing: 8px; color: #D0D0D5;
}
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #505256; border-radius: 3px;
    background-color: #2C2D30;
}
QCheckBox::indicator:checked {
    background-color: #00A0A0; border-color: #00A0A0;
}
QCheckBox::indicator:hover { border-color: #707276; }
QCheckBox::indicator:disabled { background-color: #252629; border-color: #404246; }
QCheckBox:disabled { color: #606266; }
QScrollBar:vertical {
    border: none; background: #252629; width: 10px; margin: 0px 0 0px 0;
}
QScrollBar::handle:vertical {
    background: #4A4C50; min-height: 20px; border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: #606266; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none; background: none; height: 0px;
}
QScrollBar:horizontal {
    border: none; background: #252629; height: 10px; margin: 0px 0 0px 0;
}
QScrollBar::handle:horizontal {
    background: #4A4C50; min-width: 20px; border-radius: 5px;
}
QScrollBar::handle:horizontal:hover { background: #606266; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none; background: none; width: 0px;
}
QVTKRenderWindowInteractor {
    background-color: #1A1B1E;
}
"""

def get_icon(file_path="icon.png", fallback_pixmap=QStyle.StandardPixmap.SP_ComputerIcon, size=None):
    """Gets an icon, trying file_path first, then fallback, with optional resizing."""
    app_instance = QApplication.instance()
    style = app_instance.style() if app_instance else None
    icon = QIcon()

    if file_path is not None and os.path.exists(file_path):
        loaded_icon = QIcon(file_path)
        if not loaded_icon.isNull():
            icon = loaded_icon

    if icon.isNull() and style and fallback_pixmap is not None:
        try:
            standard_icon = style.standardIcon(fallback_pixmap)
            if not standard_icon.isNull():
                icon = standard_icon
        except Exception as e_style:
            print(f"Warning: Error getting standard icon {fallback_pixmap}: {e_style}")

    if icon.isNull() and style:
        try:
            ultimate_fallback_file = "icon.png"
            if os.path.exists(ultimate_fallback_file):
                 loaded_fallback_icon = QIcon(ultimate_fallback_file)
                 if not loaded_fallback_icon.isNull():
                     icon = loaded_fallback_icon

            if icon.isNull():
                ultimate_fallback_icon = style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
                if not ultimate_fallback_icon.isNull():
                    icon = ultimate_fallback_icon
        except Exception:
            pass # give up if this fails

    if size and not icon.isNull():
        try:
            qsize = QSize(size, size) if isinstance(size, int) else size
            pixmap = icon.pixmap(qsize)
            if not pixmap.isNull():
                return QIcon(pixmap)
            else:
                return icon # return original if pixmap failed
        except Exception as e_resize:
            print(f"Warning: Error resizing icon: {e_resize}")
            return icon

    return icon if not icon.isNull() else QIcon()


# settings dialog class
class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.parent_window = parent
        self.setWindowTitle(f"Settings - {APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.new_hotkey_value = None

        self.current_watch_folder = self.settings.value(SETTINGS_WATCH_FOLDER, "")
        self.current_target_folder_cam = self.settings.value(SETTINGS_TARGET_FOLDER_CAM, "")
        self.current_target_folder_print = self.settings.value(SETTINGS_MODELS_FOLDER, "")
        self.current_hotkey = self.settings.value(SETTINGS_HOTKEY, DEFAULT_HOTKEY)
        self.current_archive_enabled = self.settings.value(SETTINGS_ARCHIVE_ENABLED, DEFAULT_ARCHIVE_ENABLED, type=bool)
        self.current_live_notify_enabled = self.settings.value(SETTINGS_LIVE_NOTIFY_ENABLED,
                                                               DEFAULT_LIVE_NOTIFY_ENABLED, type=bool)
        self.current_notify_debounce = self.settings.value(SETTINGS_NOTIFICATION_DEBOUNCE_SECS,
                                                           DEFAULT_NOTIFICATION_DEBOUNCE_SECS, type=int)
        self.current_auto_send_enabled = self.settings.value(SETTINGS_AUTO_SEND_ENABLED, DEFAULT_AUTO_SEND_ENABLED,
                                                             type=bool)
        self.current_duplicate_action = self.settings.value(SETTINGS_DUPLICATE_CHECK_ACTION,
                                                            DEFAULT_DUPLICATE_CHECK_ACTION)
        self.current_auto_duplicate_action = self.settings.value(SETTINGS_AUTO_DUPLICATE_ACTION,
                                                                 DEFAULT_AUTO_DUPLICATE_ACTION)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(15, 15, 15, 15);
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        folder_label = QLabel("Folder Configuration")
        folder_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        form_layout.addRow(folder_label)

        self.watch_folder_edit = QLineEdit(self.current_watch_folder);
        self.watch_folder_edit.setReadOnly(True)
        watch_folder_button = QPushButton("Browse...");
        watch_folder_button.clicked.connect(self.browse_watch_folder)
        watch_layout = QHBoxLayout(); watch_layout.setSpacing(6);
        watch_layout.addWidget(self.watch_folder_edit); watch_layout.addWidget(watch_folder_button)
        form_layout.addRow("Watch Folder:", watch_layout)

        self.target_folder_cam_edit = QLineEdit(self.current_target_folder_cam);
        self.target_folder_cam_edit.setReadOnly(True)
        target_cam_button = QPushButton("Browse...");
        target_cam_button.clicked.connect(self.browse_target_cam_folder)
        target_cam_layout = QHBoxLayout(); target_cam_layout.setSpacing(6);
        target_cam_layout.addWidget(self.target_folder_cam_edit); target_cam_layout.addWidget(target_cam_button)
        form_layout.addRow("Target Folder (CAM):", target_cam_layout)

        self.target_folder_print_edit = QLineEdit(self.current_target_folder_print);
        self.target_folder_print_edit.setReadOnly(True)
        target_print_button = QPushButton("Browse...");
        target_print_button.clicked.connect(self.browse_target_print_folder)
        target_print_layout = QHBoxLayout(); target_print_layout.setSpacing(6);
        target_print_layout.addWidget(self.target_folder_print_edit); target_print_layout.addWidget(target_print_button)
        form_layout.addRow("Target Folder (Print):", target_print_layout)

        automation_label = QLabel("Automation & Workflow")
        automation_label.setStyleSheet("font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        form_layout.addRow(automation_label)

        self.hotkey_edit = QLineEdit(self.current_hotkey)
        self.hotkey_edit.setPlaceholderText(f"e.g., {DEFAULT_HOTKEY}")
        if not KEYBOARD_AVAILABLE:
            self.hotkey_edit.setDisabled(True);
            self.hotkey_edit.setToolTip("Keyboard library not available")
        form_layout.addRow("Manual Scan Hotkey:", self.hotkey_edit)

        self.live_notify_enabled_checkbox = QCheckBox("Enable Live Notification Popups")
        self.live_notify_enabled_checkbox.setChecked(self.current_live_notify_enabled)
        notify_tooltip = "Show a popup notification with actions when specific files\n(*cad.stl, *model*.stl, .constructionInfo)\nare created or modified in the Watch Folder."
        if not WATCHDOG_AVAILABLE:
            self.live_notify_enabled_checkbox.setDisabled(True)
            self.live_notify_enabled_checkbox.setToolTip("Notifications disabled: 'watchdog' library not available.")
        else:
            self.live_notify_enabled_checkbox.setToolTip(notify_tooltip)
        form_layout.addRow("Real-time:", self.live_notify_enabled_checkbox)

        self.debounce_edit = QLineEdit(str(self.current_notify_debounce))
        self.debounce_edit.setValidator(QIntValidator(5, 3600))
        self.debounce_edit.setToolTip("Minimum time (seconds) between notifications for the *same* project folder.")
        debounce_layout = QHBoxLayout()
        debounce_layout.addWidget(self.debounce_edit)
        debounce_layout.addWidget(QLabel("seconds"))
        debounce_layout.addStretch()
        form_layout.addRow("Notify Cooldown:", debounce_layout)
        self.debounce_edit.setEnabled(self.current_live_notify_enabled and WATCHDOG_AVAILABLE)
        self.live_notify_enabled_checkbox.stateChanged.connect(
            lambda state: self.debounce_edit.setEnabled(state == Qt.CheckState.Checked.value and WATCHDOG_AVAILABLE)
        )

        self.auto_send_enabled_checkbox = QCheckBox("Enable Automatic Sending")
        self.auto_send_enabled_checkbox.setChecked(self.current_auto_send_enabled)
        auto_send_tooltip = ("Automatically send files to Target folders (CAM/Print)\n"
                             "when required files (.info + *cad.stl for CAM, *model*.stl for Print)\n"
                             "are detected by the file watcher (once per project per day).") # clear explanation
        if not WATCHDOG_AVAILABLE:
            self.auto_send_enabled_checkbox.setDisabled(True)
            self.auto_send_enabled_checkbox.setToolTip("Auto-Send disabled: 'watchdog' library not available.")
        else:
            self.auto_send_enabled_checkbox.setToolTip(auto_send_tooltip)
        self.auto_send_enabled_checkbox.stateChanged.connect(self.update_auto_duplicate_enabled_state)
        form_layout.addRow("", self.auto_send_enabled_checkbox)

        file_options_label = QLabel("File Handling")
        file_options_label.setStyleSheet("font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        form_layout.addRow(file_options_label)

        self.archive_enabled_checkbox = QCheckBox("Archive previous days' files in Target Folders")
        self.archive_enabled_checkbox.setChecked(self.current_archive_enabled)
        self.archive_enabled_checkbox.setToolTip(
            "If checked, before files are copied to a Target Folder,\n"
            "the application checks that folder for any files modified *before today*.\n"
            "Such files are MOVED into a YYYY/MM/DD subfolder within that Target Folder,\n"
            "based on their last modification date.\n\n"
            "If unchecked, no automatic archiving occurs.")
        form_layout.addRow("Archiving:", self.archive_enabled_checkbox)

        self.duplicate_action_combo = QComboBox()
        self.duplicate_action_combo.addItem("Ask User", "ask")
        self.duplicate_action_combo.addItem("Overwrite", "overwrite")
        self.duplicate_action_combo.addItem("Skip", "skip")
        self.duplicate_action_combo.setToolTip(
            "Action for duplicate files when using\nMANUAL 'Send to CAM' / 'Send to Print' buttons.")
        index = self.duplicate_action_combo.findData(self.current_duplicate_action)
        if index != -1: self.duplicate_action_combo.setCurrentIndex(index)
        else: self.duplicate_action_combo.setCurrentIndex(0) # Default to 'Ask'
        form_layout.addRow("Duplicates (Manual Send):", self.duplicate_action_combo)

        self.auto_duplicate_action_combo = QComboBox()
        self.auto_duplicate_action_combo.addItem("Skip Automatically", "skip")
        self.auto_duplicate_action_combo.addItem("Overwrite Automatically", "overwrite")
        self.auto_duplicate_action_combo.addItem("Use Manual Setting (Popup)", "manual")
        self.auto_duplicate_action_combo.setToolTip(
            "Action for duplicate files during AUTOMATIC operations\n(Auto-Send or Triggered File Updates).\n'Use Manual Setting' may show a popup based on the setting above.")
        auto_dup_index = self.auto_duplicate_action_combo.findData(self.current_auto_duplicate_action)
        if auto_dup_index != -1: self.auto_duplicate_action_combo.setCurrentIndex(auto_dup_index)
        else: self.auto_duplicate_action_combo.setCurrentIndex(2) # Default to 'manual'
        form_layout.addRow("Duplicates (Auto Send):", self.auto_duplicate_action_combo)
        self.update_auto_duplicate_enabled_state() # Set initial enabled state


        layout.addLayout(form_layout)
        layout.addStretch(1)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setStyleSheet(NEON_VOID_STYLE)

    def update_auto_duplicate_enabled_state(self):
        """Enable/disable the auto-duplicate setting based on Auto-Send and Watchdog status."""
        is_enabled = self.auto_send_enabled_checkbox.isChecked() and WATCHDOG_AVAILABLE
        self.auto_duplicate_action_combo.setEnabled(is_enabled)
        if not WATCHDOG_AVAILABLE:
             self.auto_duplicate_action_combo.setToolTip("Requires 'watchdog' library and 'Enable Automatic Sending'.")
        elif not self.auto_send_enabled_checkbox.isChecked():
             self.auto_duplicate_action_combo.setToolTip("Requires 'Enable Automatic Sending' to be checked.")
        else:
             self.auto_duplicate_action_combo.setToolTip(
                "Action for duplicate files during AUTOMATIC operations\n(Auto-Send or Triggered File Updates).\n'Use Manual Setting' may show a popup based on the setting above.")


    def browse_watch_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Watch Folder",
                                                  self.watch_folder_edit.text() or os.path.expanduser("~"))
        if folder: self.watch_folder_edit.setText(os.path.normpath(folder))

    def browse_target_cam_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder (for CAM files)",
                                                  self.target_folder_cam_edit.text() or os.path.expanduser("~"))
        if folder: self.target_folder_cam_edit.setText(os.path.normpath(folder))

    def browse_target_print_folder(self):
        start_dir = self.target_folder_print_edit.text() or self.target_folder_cam_edit.text() or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder (for Print files)", start_dir)
        if folder: self.target_folder_print_edit.setText(os.path.normpath(folder))

    def validate_and_accept(self):
        watch_folder = self.watch_folder_edit.text().strip()
        target_folder_cam = self.target_folder_cam_edit.text().strip()
        target_folder_print = self.target_folder_print_edit.text().strip()
        archive_enabled = self.archive_enabled_checkbox.isChecked()
        live_notify_enabled = self.live_notify_enabled_checkbox.isChecked()
        hotkey = self.hotkey_edit.text().strip().lower()
        try:
            notify_debounce = int(self.debounce_edit.text())
            if notify_debounce < 5: notify_debounce = 5
        except ValueError:
            notify_debounce = DEFAULT_NOTIFICATION_DEBOUNCE_SECS
        auto_send_enabled = self.auto_send_enabled_checkbox.isChecked()
        duplicate_action = self.duplicate_action_combo.currentData()
        auto_duplicate_action = self.auto_duplicate_action_combo.currentData()

        errors = []
        if not watch_folder:
            errors.append("Watch Folder cannot be empty.")
        elif not os.path.isdir(watch_folder):
            errors.append(f"Watch Folder does not exist:\n{watch_folder}")

        if not target_folder_cam: errors.append("Target Folder (CAM) cannot be empty.")

        if auto_send_enabled and not target_folder_print:
            warning_msg = ("Warning: Auto-Send is enabled, but the Target (Print) folder is not set. "
                           "Automatic sending of print files will be disabled.")
            print(warning_msg) # Log this warning

        if KEYBOARD_AVAILABLE:
            if not hotkey:
                errors.append("Hotkey cannot be empty.")
            elif hotkey != self.current_hotkey:
                try:
                    keyboard.parse_hotkey(hotkey)
                except ValueError as e_hotkey:
                    errors.append(f"Invalid hotkey format: '{hotkey}'.\nExamples: 'ctrl+alt+f7', 'shift+space'.\nError: {e_hotkey}")
                except Exception as e_parse: # Catch other potential parsing errors
                     errors.append(f"Error validating hotkey '{hotkey}': {e_parse}")


        if errors:
            QMessageBox.warning(self, "Validation Error", "\n\n".join(errors));
            return

        self.settings.setValue(SETTINGS_WATCH_FOLDER, watch_folder)
        self.settings.setValue(SETTINGS_TARGET_FOLDER_CAM, target_folder_cam)
        self.settings.setValue(SETTINGS_MODELS_FOLDER, target_folder_print)
        self.settings.setValue(SETTINGS_ARCHIVE_ENABLED, archive_enabled)
        self.settings.setValue(SETTINGS_LIVE_NOTIFY_ENABLED, live_notify_enabled)
        self.settings.setValue(SETTINGS_NOTIFICATION_DEBOUNCE_SECS, notify_debounce)
        self.settings.setValue(SETTINGS_AUTO_SEND_ENABLED, auto_send_enabled)
        self.settings.setValue(SETTINGS_DUPLICATE_CHECK_ACTION, duplicate_action)
        self.settings.setValue(SETTINGS_AUTO_DUPLICATE_ACTION, auto_duplicate_action) # Save new setting

        if KEYBOARD_AVAILABLE:
            if hotkey != self.current_hotkey:
                self.new_hotkey_value = hotkey # signal main window to update listener
            self.settings.setValue(SETTINGS_HOTKEY, hotkey)

        self.settings.sync() # write changes to disk/registry
        self.accept() # close the dialog successfully


# stl viewer dialog class
if VTK_AVAILABLE:
    class StlViewerDialog(QDialog):
        def __init__(self, stl_files_dict, project_name="STL Viewer", parent=None):
            super().__init__(parent)
            self.stl_files_dict = stl_files_dict # Expected format: {display_name: filepath}
            self.project_name = project_name
            self.current_actor = None
            self.renderer = None
            self.render_window = None
            self.interactor = None
            self.axes_widget = None

            self.setWindowTitle(f"{self.project_name}")
            self.setMinimumSize(600, 500)
            self.setGeometry(150, 150, 800, 700)

            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(5, 5, 5, 5)
            self.main_layout.setSpacing(5)

            self.controls_layout = QHBoxLayout()
            self.controls_layout.setContentsMargins(5, 5, 5, 0)
            self.file_combo = QComboBox(self)
            self.file_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            initial_load_path = None

            if len(self.stl_files_dict) > 1:
                self.controls_layout.addWidget(QLabel("Display:"))
                sorted_items = sorted(self.stl_files_dict.items(), key=lambda item: (
                    0 if item[0].lower().startswith("[cad]") else 1, # CAD files first
                    item[0].lower() # Then sort alphabetically by display name
                ))
                for display_name, filepath in sorted_items:
                    self.file_combo.addItem(display_name, userData=filepath)
                self.file_combo.currentIndexChanged.connect(self.on_file_selected)
                self.controls_layout.addWidget(self.file_combo)
                self.main_layout.addLayout(self.controls_layout)
                initial_load_path = self.file_combo.currentData() # Load the first item (likely a CAD file if present)
            elif len(self.stl_files_dict) == 1:
                initial_load_path = list(self.stl_files_dict.values())[0]
                display_name = list(self.stl_files_dict.keys())[0]
                self.setWindowTitle(f"{self.project_name} - {display_name}")
            else:
                error_label = QLabel("Error: No valid STL files provided.")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_layout.addWidget(error_label)
                self.setup_vtk() # Still setup VTK basics to show background
                self.status_label = QLabel("No STL files found for this project.")
                self.status_label.setObjectName("viewerStatusLabel")
                self.main_layout.addWidget(self.status_label)
                self.setStyleSheet(NEON_VOID_STYLE)
                return # Exit constructor if no files

            self.vtkWidget = QVTKRenderWindowInteractor(self)
            self.main_layout.addWidget(self.vtkWidget, 1)

            self.status_label = QLabel("Initializing VTK...")
            self.status_label.setObjectName("viewerStatusLabel")
            self.main_layout.addWidget(self.status_label)

            self.setup_vtk()

            if initial_load_path:
                QTimer.singleShot(100, lambda: self.load_stl(initial_load_path))
            else:
                self.status_label.setText("No STL file selected or found.")

            self.setStyleSheet(NEON_VOID_STYLE)

        def setup_vtk(self):
            """Configures the VTK rendering pipeline."""
            if not hasattr(self, 'vtkWidget') or self.vtkWidget is None:
                if QVTKRenderWindowInteractor:
                    self.vtkWidget = QVTKRenderWindowInteractor(self)
                    if self.main_layout.indexOf(self.vtkWidget) == -1:
                        self.main_layout.insertWidget(1, self.vtkWidget, 1) # Insert before status label
                else:
                    print("VTK Setup skipped: QVTKRenderWindowInteractor not available.")
                    if hasattr(self, 'status_label'):
                         self.status_label.setText("VTK Rendering N/A")
                    return

            self.render_window = self.vtkWidget.GetRenderWindow()
            if not self.render_window:
                 print("VTK Setup Error: Failed to get RenderWindow from QVTK widget.")
                 if hasattr(self, 'status_label'):
                      self.status_label.setText("VTK Init Error")
                 return

            self.renderer = vtk.vtkRenderer()
            self.renderer.SetBackground(*VIEWER_BACKGROUND_COLOR)
            self.render_window.AddRenderer(self.renderer)
            self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

            if not self.interactor:
                 print("VTK Setup Error: Failed to get Interactor from RenderWindow.")
                 if hasattr(self, 'status_label'):
                      self.status_label.setText("VTK Init Error")
                 if self.renderer: self.render_window.RemoveRenderer(self.renderer); self.renderer = None
                 return


            style = vtk.vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(style)

            if VIEWER_AXES_ENABLED:
                try:
                    axes = vtk.vtkAxesActor()
                    self.axes_widget = vtk.vtkOrientationMarkerWidget()
                    self.axes_widget.SetOutlineColor(0.9300, 0.5700, 0.1300)
                    self.axes_widget.SetOrientationMarker(axes)
                    self.axes_widget.SetInteractor(self.interactor)
                    self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2) # Bottom-left corner
                    self.axes_widget.SetEnabled(1)
                    self.axes_widget.InteractiveOff() # Don't let user drag the axes
                except AttributeError as e_axes_attr:
                     print(f"VTK Warning: Could not create axes widget (VTK version issue?): {e_axes_attr}")
                     self.axes_widget = None
                except Exception as e_axes:
                    print(f"Error setting up VTK axes: {e_axes}")
                    self.axes_widget = None

            if self.interactor:
                 self.interactor.Initialize()

        def load_stl(self, filepath):
            """Loads and displays the specified STL file."""
            if not self.renderer or not self.render_window:
                self.status_label.setText("Error: VTK Renderer not initialized.")
                return

            if not filepath or not os.path.exists(filepath):
                self.status_label.setText(f"Error: File not found '{os.path.basename(filepath)}'")
                if self.current_actor:
                    self.renderer.RemoveActor(self.current_actor)
                    self.current_actor = None
                self.render_window.Render() # Render empty scene
                return

            current_display_name = os.path.basename(filepath) # fallback to just filename
            found_display_name = False
            if hasattr(self, 'file_combo') and self.file_combo.count() > 0:
                for i in range(self.file_combo.count()):
                    if self.file_combo.itemData(i) == filepath:
                        current_display_name = self.file_combo.itemText(i)
                        found_display_name = True
                        break
            if not found_display_name: # Maybe only one file, check dict
                 for d_name, f_path in self.stl_files_dict.items():
                     if f_path == filepath:
                         current_display_name = d_name
                         break


            self.status_label.setText(f"Loading {current_display_name}...")
            QCoreApplication.processEvents() # Allow UI to update

            try:
                reader = vtk.vtkSTLReader()
                reader.SetFileName(filepath)
                reader.UpdateInformation() # Check if file is readable first
                reader.Update() # Actual data reading

                if reader.GetErrorCode() != 0:
                     error_code = reader.GetErrorCode()
                     msg = f"VTK STL Reader Error (Code: {error_code}) reading '{current_display_name}'."
                     print(msg)
                     self.status_label.setText(f"Error: {msg}")
                     if self.current_actor:
                         self.renderer.RemoveActor(self.current_actor)
                         self.current_actor = None
                     self.render_window.Render()
                     return


                polydata = reader.GetOutput()
                if not polydata or polydata.GetNumberOfPoints() == 0:
                    msg = f"Failed to read geometry from '{current_display_name}' (empty or invalid)."
                    self.status_label.setText(f"Error: {msg}")
                    if self.current_actor:
                        self.renderer.RemoveActor(self.current_actor)
                        self.current_actor = None
                    self.render_window.Render()
                    return

                mapper_input_connection = reader.GetOutputPort()


                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(mapper_input_connection)

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(*VIEWER_MODEL_COLOR)
                actor.GetProperty().SetInterpolationToGouraud()


                if self.current_actor:
                    self.renderer.RemoveActor(self.current_actor)

                self.renderer.AddActor(actor)
                self.current_actor = actor
                self.renderer.ResetCamera()
                self.render_window.Render()

                self.status_label.setText(f"Displaying: {current_display_name}")
                self.setWindowTitle(f"{self.project_name} - {current_display_name}")

            except Exception as e:
                error_msg = f"Failed to load/render STL '{current_display_name}': {e}"
                print(f"STL Load Error: {error_msg}")
                self.status_label.setText(f"Error: {error_msg}")
                if self.current_actor:
                    self.renderer.RemoveActor(self.current_actor)
                    self.current_actor = None
                if self.render_window: self.render_window.Render()

        def on_file_selected(self, index):
            """Handles selection change in the QComboBox."""
            if hasattr(self, 'file_combo'):
                filepath = self.file_combo.itemData(index)
                if filepath:
                    self.load_stl(filepath)

        def closeEvent(self, event):
            """Clean up VTK resources on close."""
            print("Closing STL Viewer Dialog...")
            if self.interactor:
                 try: self.interactor.Disable()
                 except Exception as e: print(f"Error disabling interactor: {e}")
            if self.axes_widget:
                 try: self.axes_widget.SetInteractor(None); self.axes_widget.Off(); self.axes_widget = None
                 except Exception as e: print(f"Error cleaning axes widget: {e}")
            if self.renderer:
                 try: self.renderer.RemoveAllViewProps()
                 except Exception as e: print(f"Error removing view props: {e}")
            if self.render_window:
                 try:
                     if self.renderer: self.render_window.RemoveRenderer(self.renderer)
                 except Exception as e: print(f"Error removing renderer: {e}")

            self.current_actor = None
            self.renderer = None

            super().closeEvent(event)

# notification dialog popup class
class NotificationDialog(QDialog):
    def __init__(self, item_data, main_window_ref, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.main_window = main_window_ref
        self.setWindowTitle(f"{APP_NAME} - File Update")
        self.setModal(False) # Non-modal
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        patient = self.item_data.get('patient', 'Unknown Patient')
        work_type = self.item_data.get('work_type', 'N/A')
        teeth = self.item_data.get('teeth', '?')
        cam_icon, info_icon, print_icon = self.item_data.get("status_icons", ("?", "?", "?"))
        folder_name = os.path.basename(self.item_data.get('folder_path', 'N/A'))
        num_cad = len(self.item_data.get('cad_stl_paths', []))
        num_print = len(self.item_data.get('model_stl_paths', []))
        timestamp = self.item_data.get("last_modified_timestamp", time.time())
        time_ago = get_relative_time(timestamp)


        info_text = (
            f"<h3 style='color:#00E5E5; margin-bottom: 5px;'>{patient}</h3>"
            f"<b>Work:</b> {work_type} ({teeth})<br>"
            f"<b>Folder:</b> ...{os.sep}{folder_name}<br>"
            f"<b>Status:</b> {cam_icon}CAM ({num_cad}) {info_icon}Info {print_icon}Print ({num_print})<br>"
            f"<i style='font-size: 9pt; color: #909095;'>File(s) updated {time_ago}. Choose an action:</i>"
        )
        self.info_label = QLabel(info_text)
        self.info_label.setObjectName("notificationInfoLabel")
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        action_button_layout = QHBoxLayout()
        action_button_layout.setSpacing(10)
        icon_size = 16

        self.preview_button = QPushButton("3D Preview")
        self.preview_button.setObjectName("notifyPreviewButton")
        preview_icon = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_FileDialogDetailedView, size=icon_size)
        if not preview_icon.isNull(): self.preview_button.setIcon(preview_icon); self.preview_button.setIconSize(QSize(icon_size, icon_size))
        can_preview = VTK_AVAILABLE and (self.item_data.get('has_cad') or self.item_data.get('has_models') or self.item_data.get('other_stl_paths'))
        self.preview_button.setEnabled(can_preview)
        preview_tooltip = "Open 3D Viewer for available STL files" if can_preview else ("Enable VTK for 3D Preview" if not VTK_AVAILABLE else "No STLs found to preview")
        self.preview_button.setToolTip(preview_tooltip)
        self.preview_button.clicked.connect(self.do_preview)
        action_button_layout.addWidget(self.preview_button)

        self.send_cam_button = QPushButton("Send to CAM")
        self.send_cam_button.setObjectName("notifySendCamButton")
        cam_icon_btn = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_DriveNetIcon, size=icon_size)
        if not cam_icon_btn.isNull(): self.send_cam_button.setIcon(cam_icon_btn); self.send_cam_button.setIconSize(QSize(icon_size, icon_size))
        can_send_cam = self.item_data.get('has_cad') and self.item_data.get('has_info') and bool(self.main_window.target_folder_cam)
        cam_tooltip = f"Copy CAM files ({num_cad} *cad.stl + *.info) to Target:\n{shorten_path(self.main_window.target_folder_cam)}" if can_send_cam else ("Target (CAM) folder or required files missing" if bool(self.main_window.target_folder_cam) else "Target (CAM) folder not set")
        self.send_cam_button.setEnabled(can_send_cam)
        self.send_cam_button.setToolTip(cam_tooltip)
        self.send_cam_button.clicked.connect(self.do_send_cam)
        action_button_layout.addWidget(self.send_cam_button)

        self.send_print_button = QPushButton("Send to Print")
        self.send_print_button.setObjectName("notifySendPrintButton")
        print_icon_btn = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_DriveHDIcon, size=icon_size)
        if not print_icon_btn.isNull(): self.send_print_button.setIcon(print_icon_btn); self.send_print_button.setIconSize(QSize(icon_size, icon_size))
        can_send_print = self.item_data.get('has_models') and bool(self.main_window.target_folder_print)
        print_tooltip = f"Copy Model/Die files ({num_print} *model*.stl) to Target:\n{shorten_path(self.main_window.target_folder_print)}" if can_send_print else ("Target (Print) folder or Model/Die files missing" if bool(self.main_window.target_folder_print) else "Target (Print) folder not set")
        self.send_print_button.setEnabled(can_send_print)
        self.send_print_button.setToolTip(print_tooltip)
        self.send_print_button.clicked.connect(self.do_send_print)
        action_button_layout.addWidget(self.send_print_button)

        layout.addLayout(action_button_layout)

        open_folder_layout = QHBoxLayout()
        open_folder_layout.setSpacing(10)
        open_folder_layout.setContentsMargins(0, 8, 0, 0)

        open_folder_icon_size = 16
        open_folder_icon = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_DirOpenIcon, size=open_folder_icon_size)

        self.open_cam_target_button = QPushButton("Open CAM Target")
        self.open_cam_target_button.setObjectName("notifyOpenCamFolderButton")
        if not open_folder_icon.isNull(): self.open_cam_target_button.setIcon(open_folder_icon); self.open_cam_target_button.setIconSize(QSize(open_folder_icon_size, open_folder_icon_size))
        can_open_cam_target = bool(self.main_window.target_folder_cam)
        self.open_cam_target_button.setEnabled(can_open_cam_target)
        cam_target_tooltip = f"Open: {shorten_path(self.main_window.target_folder_cam)}" if can_open_cam_target else "Target (CAM) folder not set"
        self.open_cam_target_button.setToolTip(cam_target_tooltip)
        self.open_cam_target_button.clicked.connect(self.do_open_cam_target)
        open_folder_layout.addWidget(self.open_cam_target_button)

        self.open_print_target_button = QPushButton("Open Print Target")
        self.open_print_target_button.setObjectName("notifyOpenPrintFolderButton")
        if not open_folder_icon.isNull(): self.open_print_target_button.setIcon(open_folder_icon); self.open_print_target_button.setIconSize(QSize(open_folder_icon_size, open_folder_icon_size))
        can_open_print_target = bool(self.main_window.target_folder_print)
        self.open_print_target_button.setEnabled(can_open_print_target)
        print_target_tooltip = f"Open: {shorten_path(self.main_window.target_folder_print)}" if can_open_print_target else "Target (Print) folder not set"
        self.open_print_target_button.setToolTip(print_target_tooltip)
        self.open_print_target_button.clicked.connect(self.do_open_print_target)
        open_folder_layout.addWidget(self.open_print_target_button)

        open_folder_layout.addStretch()
        layout.addLayout(open_folder_layout)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        close_button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button_box.rejected.connect(self.reject) # Close button triggers reject
        layout.addWidget(close_button_box)

        self.setWindowIcon(get_icon("icon.png", fallback_pixmap=QStyle.StandardPixmap.SP_MessageBoxInformation, size=32))
        self.setStyleSheet(NEON_VOID_STYLE)

        self.position_dialog()

        self.activateWindow()
        self.raise_()

    def position_dialog(self):
         """Positions the notification dialog, e.g., bottom right."""
         try:
             screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
             dialog_size = self.sizeHint() # Get preferred size
             margin = 15 # Margin from screen edges
             x = screen_geometry.width() - dialog_size.width() - margin
             y = screen_geometry.height() - dialog_size.height() - margin
             self.move(x, y)
         except Exception as e:
             print(f"Error positioning notification dialog: {e}")
             if self.parent():
                 parent_rect = self.parent().geometry()
                 self.move(parent_rect.center() - self.rect().center())

    # action methods for notification buttons
    # notification button actions - call main window funcs

    def do_preview(self):
        if self.main_window:
            self.main_window.show_stl_viewer_for_project(self.item_data)
        # DO NOT CLOSE the dialog - allow other actions

    def do_send_cam(self):
        if self.main_window:
            # Call main window's send function, passing is_auto=True
            # so it uses the automatic duplicate handling setting.
            success = self.main_window.send_cam_for_project(self.item_data, is_auto=True)
            if success:
                self.send_cam_button.setText("Sent CAM ✓")
                self.send_cam_button.setEnabled(False)
            else:
                 self._reset_send_cam_button() # Re-enable if sending failed
        # DO NOT CLOSE the dialog

    def _reset_send_cam_button(self):
        """Resets the Send CAM button text and enabled state."""
        self.send_cam_button.setText("Send to CAM")
        can_send_cam = self.item_data.get('has_cad') and self.item_data.get('has_info') and bool(self.main_window.target_folder_cam)
        self.send_cam_button.setEnabled(can_send_cam)

    def do_send_print(self):
        if self.main_window:
            # Pass is_auto=True for silent duplicate check based on auto setting
            success = self.main_window.send_print_for_project(self.item_data, is_auto=True)
            if success:
                self.send_print_button.setText("Sent Print ✓")
                self.send_print_button.setEnabled(False)
            else:
                self._reset_send_print_button() # Re-enable if sending failed
        # DO NOT CLOSE the dialog

    def _reset_send_print_button(self):
        """Resets the Send Print button text and enabled state."""
        self.send_print_button.setText("Send to Print")
        can_send_print = self.item_data.get('has_models') and bool(self.main_window.target_folder_print)
        self.send_print_button.setEnabled(can_send_print)

    def do_open_cam_target(self):
        """Opens the CAM target folder."""
        if self.main_window and self.main_window.target_folder_cam:
            self.main_window.open_folder_in_explorer(self.main_window.target_folder_cam)
        # DO NOT CLOSE the dialog

    def do_open_print_target(self):
        """Opens the Print target folder."""
        if self.main_window and self.main_window.target_folder_print:
            self.main_window.open_folder_in_explorer(self.main_window.target_folder_print)
        # DO NOT CLOSE the dialog

    def reject(self):
        """Handles closing the dialog (user clicked Close or 'X' button)."""
        # Remove the 'stay on top' hint when closing manually
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show() # Need to show again briefly after changing flags for it to take effect? Seems weird.
        super().reject()


# the main window class
class MainWindow(QMainWindow):
    last_failed_items = [] # maybe for retry later? (not used now)
    current_stl_viewer = None # reference to the viewer dialog if open
    active_notification_dialog = None # reference to the notification popup if open
    recently_notified_projects = {} # track last notify time per folder path {folder_path: timestamp}
    auto_send_status = {} # track auto-sends today {folder_path: {"cam_sent": bool, "print_sent": bool, "date": "YYYY-MM-DD"}}

    class DuplicateAction:
        ASK = 0
        OVERWRITE = 1
        SKIP = 2
        CANCEL = 3 # User cancelled the whole multi-file operation from the dialog

    current_multi_duplicate_choice = DuplicateAction.ASK # default to ask for each file initially

    def __init__(self, hotkey_emitter, watchdog_emitter):
        super().__init__()
        self.app = QApplication.instance()
        self.hotkey_signal_emitter = hotkey_emitter
        self.watchdog_signal_emitter = watchdog_emitter
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.listener_thread = None
        self.is_listener_intentionally_stopped = False
        self.is_operation_running = False

        self.fs_observer = None
        self.fs_event_handler = None

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, 1050, 800)

        self.setWindowIcon(get_icon("icon.png", fallback_pixmap=QStyle.StandardPixmap.SP_ComputerIcon, size=32))

        self.load_app_settings()
        self.load_auto_send_status() # load status from json file
        self.init_ui()
        self.init_tray_icon()
        self.apply_styles()

        if KEYBOARD_AVAILABLE and self.hotkey_signal_emitter:
            self.hotkey_signal_emitter.hotkey_pressed.connect(self.handle_hotkey_press)
        if WATCHDOG_AVAILABLE and self.watchdog_signal_emitter:
            self.watchdog_signal_emitter.file_change_detected.connect(self.handle_filesystem_change)

        self.check_folders_exist()
        self.start_hotkey_listener()
        self.start_file_watcher()

        if not KEYBOARD_AVAILABLE:
            QTimer.singleShot(100, lambda: self.show_library_warning("Keyboard", "keyboard", "Global hotkeys disabled.",
                                                                     "May require admin rights."))
        if not VTK_AVAILABLE:
            QTimer.singleShot(150, lambda: self.show_library_warning("VTK", "vtk", "STL Viewer feature disabled.",
                                                                     "Ensure vtk includes Qt support."))
        if not WATCHDOG_AVAILABLE:
            QTimer.singleShot(200, lambda: self.show_library_warning("Watchdog", "watchdog",
                                                                     "Real-time File Notifications & Auto-Send disabled.",
                                                                     "Install via: pip install watchdog"))

    def show_library_warning(self, lib_name, install_name, consequence, note=""):
        """Generic warning popup for missing optional libraries."""
        msgBox = QMessageBox(self);
        msgBox.setIcon(QMessageBox.Icon.Warning);
        msgBox.setWindowTitle(f"{lib_name} Library Issue")
        msgBox.setText(f"Python '{lib_name}' library not found or failed to load.\n{consequence}")
        info = f"Try installing using: pip install {install_name}"
        if note: info += f"\nNote: {note}"
        msgBox.setInformativeText(info)
        msgBox.setStandardButtons(QMessageBox.StandardButton.Ok);
        msgBox.setStyleSheet(NEON_VOID_STYLE); # use app style
        msgBox.exec()

    def load_app_settings(self):
        """Loads all settings from QSettings into instance variables."""
        self.watch_folder = self.settings.value(SETTINGS_WATCH_FOLDER, "")
        self.target_folder_cam = self.settings.value(SETTINGS_TARGET_FOLDER_CAM, "")
        self.target_folder_print = self.settings.value(SETTINGS_MODELS_FOLDER, "")
        self.hotkey_combo = self.settings.value(SETTINGS_HOTKEY, DEFAULT_HOTKEY)
        self.archive_enabled = self.settings.value(SETTINGS_ARCHIVE_ENABLED, DEFAULT_ARCHIVE_ENABLED, type=bool)
        self.live_notify_enabled = self.settings.value(SETTINGS_LIVE_NOTIFY_ENABLED, DEFAULT_LIVE_NOTIFY_ENABLED,
                                                       type=bool)
        self.notify_debounce_secs = self.settings.value(SETTINGS_NOTIFICATION_DEBOUNCE_SECS,
                                                        DEFAULT_NOTIFICATION_DEBOUNCE_SECS, type=int)
        self.auto_send_enabled = self.settings.value(SETTINGS_AUTO_SEND_ENABLED, DEFAULT_AUTO_SEND_ENABLED, type=bool)
        self.duplicate_check_action_setting = self.settings.value(SETTINGS_DUPLICATE_CHECK_ACTION,
                                                                  DEFAULT_DUPLICATE_CHECK_ACTION)
        self.auto_duplicate_action_setting = self.settings.value(SETTINGS_AUTO_DUPLICATE_ACTION,
                                                                DEFAULT_AUTO_DUPLICATE_ACTION)


    def reload_settings_and_update_ui(self):
        """Reloads settings after changes, updates UI elements, and restarts listeners/watchers if needed."""
        old_hotkey = self.hotkey_combo
        old_live_notify_enabled = self.live_notify_enabled
        old_auto_send_enabled = self.auto_send_enabled
        old_watch_folder = self.watch_folder
        old_notify_debounce = self.notify_debounce_secs

        self.load_app_settings()

        self.update_status_bar()
        self.update_hotkey_ui_elements()
        self.update_button_state()

        watcher_settings_changed = (
                self.live_notify_enabled != old_live_notify_enabled or
                self.auto_send_enabled != old_auto_send_enabled or
                self.watch_folder != old_watch_folder or
                self.notify_debounce_secs != old_notify_debounce # Debounce change also requires restart/update logic
        )

        if watcher_settings_changed:
            print("[Settings] Watcher-relevant settings changed, restarting watcher...")
            self.stop_file_watcher()
            self.start_file_watcher() # Restarts with new settings
        else:
            print("[Settings] Watcher settings unchanged, not restarting.")

        self.check_folders_exist() # Re-check folders after potential changes

    # manage autosend status persistence
    def load_auto_send_status(self):
        """Loads the auto-send status from a JSON file (for today only)."""
        today_str = datetime.date.today().isoformat()
        self.auto_send_status = {} # Start fresh
        if os.path.exists(AUTO_SEND_STATUS_FILE):
            try:
                with open(AUTO_SEND_STATUS_FILE, 'r') as f:
                    loaded_status = json.load(f)
                    self.auto_send_status = {
                        k: v for k, v in loaded_status.items()
                        if isinstance(v, dict) and v.get("date") == today_str
                    }
                    print(f"[Status] Loaded auto-send status for {len(self.auto_send_status)} projects today.")
            except (json.JSONDecodeError, IOError, TypeError) as e:
                print(f"[Status] Error loading auto-send status file ({AUTO_SEND_STATUS_FILE}): {e}. Resetting status.")
                self.auto_send_status = {}
            except Exception as e: # Catch other unexpected errors
                print(f"[Status] Unexpected error loading auto-send status: {e}. Resetting status.")
                self.auto_send_status = {}
        else:
             print(f"[Status] Auto-send status file not found ({AUTO_SEND_STATUS_FILE}). Starting fresh.")
             self.auto_send_status = {}


    def save_auto_send_status(self):
        """Saves the current auto-send status (today's entries) to a JSON file."""
        try:
            today_str = datetime.date.today().isoformat()
            current_status = {k: v for k, v in self.auto_send_status.items() if isinstance(v, dict) and v.get("date") == today_str}

            with open(AUTO_SEND_STATUS_FILE, 'w') as f:
                json.dump(current_status, f, indent=2)
        except IOError as e:
            print(f"[Status] Error saving auto-send status file ({AUTO_SEND_STATUS_FILE}): {e}")
        except Exception as e: # Catch other unexpected errors
             print(f"[Status] Unexpected error saving auto-send status: {e}")


    def update_auto_send_status(self, folder_path, sent_type):
        """Marks a project (by folder path) as auto-sent for 'cam' or 'print' today."""
        if not folder_path: return # Need a valid path
        folder_path_norm = os.path.normpath(folder_path)
        today_str = datetime.date.today().isoformat()

        if folder_path_norm not in self.auto_send_status or not isinstance(self.auto_send_status[folder_path_norm], dict) or self.auto_send_status[folder_path_norm].get("date") != today_str:
            self.auto_send_status[folder_path_norm] = {"cam_sent": False, "print_sent": False, "date": today_str}

        updated = False
        if sent_type == "cam" and not self.auto_send_status[folder_path_norm].get("cam_sent", False):
            self.auto_send_status[folder_path_norm]["cam_sent"] = True
            updated = True
        elif sent_type == "print" and not self.auto_send_status[folder_path_norm].get("print_sent", False):
            self.auto_send_status[folder_path_norm]["print_sent"] = True
            updated = True

        self.auto_send_status[folder_path_norm]["date"] = today_str

        if updated:
            print(f"[Status] Marked '{os.path.basename(folder_path_norm)}' as auto-sent for '{sent_type}' today.")
            self.save_auto_send_status() # Save immediately after update


    def has_been_auto_sent(self, folder_path, sent_type):
        """Checks if a project (by folder path) has already been auto-sent for 'cam' or 'print' today."""
        if not folder_path: return False
        folder_path_norm = os.path.normpath(folder_path)
        today_str = datetime.date.today().isoformat()
        status = self.auto_send_status.get(folder_path_norm)

        if not status or not isinstance(status, dict) or status.get("date") != today_str:
            return False

        if sent_type == "cam":
            return status.get("cam_sent", False)
        elif sent_type == "print":
            return status.get("print_sent", False)

        return False # Unknown sent_type


    def init_ui(self):
        """Sets up the main window UI elements."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        scan_action_menu = QAction("Scan Watch Folder", self); scan_action_menu.triggered.connect(self.scan_and_show)
        settings_action_menu = QAction("Settings...", self); settings_action_menu.triggered.connect(self.open_settings_window)
        open_target_cam_action = QAction("Open Target Folder (CAM)", self)
        open_target_cam_action.triggered.connect(lambda: self.open_folder_in_explorer(self.target_folder_cam))
        open_target_cam_action.setEnabled(bool(self.target_folder_cam))
        self.target_folder_cam_action_ref = open_target_cam_action
        open_target_print_action = QAction("Open Target Folder (Print)", self)
        open_target_print_action.triggered.connect(lambda: self.open_folder_in_explorer(self.target_folder_print))
        open_target_print_action.setEnabled(bool(self.target_folder_print))
        self.target_folder_print_action_ref = open_target_print_action
        exit_action_menu = QAction("Quit", self); exit_action_menu.triggered.connect(self.quit_application)
        file_menu.addAction(scan_action_menu); file_menu.addAction(settings_action_menu); file_menu.addSeparator()
        file_menu.addAction(open_target_cam_action); file_menu.addAction(open_target_print_action); file_menu.addSeparator()
        file_menu.addAction(exit_action_menu)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self); about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        self.info_label = QLabel("Initializing...")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["Time", "Patient", "Work Type", "Teeth / Arch", "Files"])
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Allow multi-select
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setWordWrap(False) # Keep rows compact
        self.table_widget.setShowGrid(False) # Cleaner look
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_widget.itemDoubleClicked.connect(self.handle_table_double_click)
        self.table_widget.setToolTip("Double-click row to view STLs (if VTK available). Right-click for actions.")

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive) # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Patient
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Work Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Teeth
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # Files Status
        self.table_widget.setColumnWidth(0, 100) # Time width
        header.setMinimumSectionSize(150) # Min width for stretch columns
        self.table_widget.setColumnWidth(3, 150) # Teeth width
        self.table_widget.setColumnWidth(4, 75) # Files status width
        self.table_widget.setSortingEnabled(True)
        self.table_widget.sortByColumn(0, Qt.SortOrder.DescendingOrder) # Sort by time initially


        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        icon_size = 18

        scan_icon = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_BrowserReload, size=icon_size)
        self.scan_button = QPushButton("Scan")
        if not scan_icon.isNull(): self.scan_button.setIcon(scan_icon); self.scan_button.setIconSize(QSize(icon_size, icon_size))
        self.scan_button.clicked.connect(self.scan_and_show)
        button_layout.addWidget(self.scan_button)

        button_layout.addStretch(1)

        send_cam_icon = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_DriveNetIcon, size=icon_size)
        self.send_cam_button = QPushButton("Send to CAM")
        self.send_cam_button.setObjectName("sendCamButton")
        if not send_cam_icon.isNull(): self.send_cam_button.setIcon(send_cam_icon); self.send_cam_button.setIconSize(QSize(icon_size, icon_size))
        self.send_cam_button.setToolTip(f"Copy selected projects' CAM files (*.info, ALL *cad.stl) to Target")
        self.send_cam_button.clicked.connect(self.process_selected_cam_info)
        self.send_cam_button.setEnabled(False)
        button_layout.addWidget(self.send_cam_button)

        send_print_icon = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_DriveHDIcon, size=icon_size)
        self.send_print_button = QPushButton("Send to Print")
        self.send_print_button.setObjectName("sendPrintButton")
        if not send_print_icon.isNull(): self.send_print_button.setIcon(send_print_icon); self.send_print_button.setIconSize(QSize(icon_size, icon_size))
        self.send_print_button.setToolTip(f"Copy selected projects' Print files (*model*.stl) to Target")
        self.send_print_button.clicked.connect(self.process_selected_print_files)
        self.send_print_button.setEnabled(False)
        button_layout.addWidget(self.send_print_button)

        button_layout.addSpacing(15)

        open_folder_icon = get_icon(file_path=None, fallback_pixmap=QStyle.StandardPixmap.SP_DirOpenIcon, size=icon_size - 2)

        self.open_cam_folder_button = QPushButton("Open CAM Target")
        self.open_cam_folder_button.setObjectName("openCamFolderButton")
        if not open_folder_icon.isNull(): self.open_cam_folder_button.setIcon(open_folder_icon); self.open_cam_folder_button.setIconSize(QSize(icon_size-2, icon_size-2))
        self.open_cam_folder_button.setToolTip("Open Target Folder (CAM)")
        self.open_cam_folder_button.clicked.connect(lambda: self.open_folder_in_explorer(self.target_folder_cam))
        self.open_cam_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_cam_folder_button)

        self.open_print_folder_button = QPushButton("Open Print Target")
        self.open_print_folder_button.setObjectName("openPrintFolderButton")
        if not open_folder_icon.isNull(): self.open_print_folder_button.setIcon(open_folder_icon); self.open_print_folder_button.setIconSize(QSize(icon_size-2, icon_size-2))
        self.open_print_folder_button.setToolTip("Open Target Folder (Print)")
        self.open_print_folder_button.clicked.connect(lambda: self.open_folder_in_explorer(self.target_folder_print))
        self.open_print_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_print_folder_button)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.clicked.connect(self.open_settings_window)
        button_layout.addWidget(self.settings_button)

        layout.addLayout(button_layout)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.watch_status_label = QLabel(); self.watch_status_label.setObjectName("statusBarLabel")
        self.cam_target_status_label = QLabel(); self.cam_target_status_label.setObjectName("statusBarLabel")
        self.print_target_status_label = QLabel(); self.print_target_status_label.setObjectName("statusBarLabel")
        self.archive_status_label = QLabel(); self.archive_status_label.setObjectName("statusBarLabel")
        self.live_notify_status_label = QLabel(); self.live_notify_status_label.setObjectName("statusBarLabel")
        self.auto_send_status_label = QLabel(); self.auto_send_status_label.setObjectName("statusBarLabel")
        self.auto_dup_status_label = QLabel(); self.auto_dup_status_label.setObjectName("statusBarLabel") # Label for AutoDup status
        self.hotkey_status_label = QLabel(); self.hotkey_status_label.setObjectName("statusBarLabel")
        self.statusBar.addPermanentWidget(self.watch_status_label)
        self.statusBar.addPermanentWidget(self.cam_target_status_label)
        self.statusBar.addPermanentWidget(self.print_target_status_label)
        self.statusBar.addPermanentWidget(self.archive_status_label)
        self.statusBar.addPermanentWidget(self.live_notify_status_label)
        self.statusBar.addPermanentWidget(self.auto_send_status_label)
        self.statusBar.addPermanentWidget(self.auto_dup_status_label) # Add the new status label
        self.statusBar.addPermanentWidget(self.hotkey_status_label)
        self.update_status_bar()

        self.table_widget.itemSelectionChanged.connect(self.update_button_state)
        self.update_hotkey_ui_elements() # Set initial info label text
        self.update_button_state() # Set initial button states

    def apply_styles(self):
        """Applies the main stylesheet (NEON_VOID_STYLE)."""
        self.setStyleSheet(NEON_VOID_STYLE)

    def init_tray_icon(self):
        """Sets up the system tray icon and menu."""
        tray_icon_obj = get_icon("icon.png", fallback_pixmap=QStyle.StandardPixmap.SP_ComputerIcon)
        if tray_icon_obj.isNull():
            print("Warning: Could not load tray icon (icon.png missing and fallback failed?).")
            self.tray_icon = None;
            return

        self.tray_icon = QSystemTrayIcon(tray_icon_obj, self)
        self.tray_icon.setToolTip(APP_NAME)

        tray_menu = QMenu()
        show_action = QAction("Show Window", self); show_action.triggered.connect(self.show_window)
        self.scan_tray_action = QAction("Scan Now", self); self.scan_tray_action.triggered.connect(self.scan_and_show)
        settings_action = QAction("Settings...", self); settings_action.triggered.connect(self.open_settings_window)
        quit_action = QAction("Quit", self); quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(show_action); tray_menu.addAction(self.scan_tray_action); tray_menu.addSeparator()
        tray_menu.addAction(settings_action); tray_menu.addSeparator(); tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        self.update_hotkey_ui_elements() # Update tooltip based on hotkey status

    def show_about_dialog(self):
        """Displays the About dialog (Updated for v3.17.0 features)."""
        about_text = f"""
            <h2 style='color:#00E5E5;'>{APP_NAME} v{APP_VERSION}</h2>
            <p>Automated dental project file scanner, notifier, and sender with STL viewer.</p>
            <p><b>Author:</b> zer0ltrnce (<a style='color:#00A0A0;' href='mailto:zerotlrnce@gmail.com'>zerotlrnce@gmail.com</a>)<br/>
               GitHub: <a style='color:#00A0A0;' href='https://github.com/zer0ltrnce'>github.com/zer0ltrnce</a><br/>
               Original Concept: David Kamarauli (<a style='color:#00A0A0;' href='https://smiledesigner.us'>smiledesigner.us</a>)<br/>
               Instagram: <a style='color:#00A0A0;' href='https://www.instagram.com/davidkamaraulli'>@davidkamaraulli</a>
            </p>
            <p><b>How it works:</b>
            <ul style='margin-left: 0px; padding-left: 20px;'>
                <li>Scans the 'Watch Folder' for projects modified <b>today</b> (manually via Scan/Hotkey, or triggered by file changes).</li>
                <li>Displays found projects in the table, recognizing Full Arch cases.</li>
                <li><b>File Change Detection (if 'watchdog' installed):</b>
                   <ul style='margin-left: 0px; padding-left: 20px;'>
                       <li>Detects changes to specific files: <code>*.constructionInfo</code>, <code>*cad.stl</code>, <code>*model*.stl</code>.</li>
                       <li><b>Live Notifications (if enabled):</b> When a relevant file is saved/modified, a popup appears (after cooldown: {self.notify_debounce_secs}s) offering quick actions (Preview, Send, Open). Only one popup at a time.</li>
                       <li><b>Automatic Sending (if enabled):</b> When required files are detected, they are <b>automatically sent</b> to the corresponding Target Folder (<b>once per project per day</b>).</li>
                   </ul>
                </li>
                {"" if WATCHDOG_AVAILABLE else "<li style='color:#FFD700;'><i>(Real-time features disabled: 'watchdog' library missing)</i></li>"}
                <li><b>Send to CAM:</b> Copies ONLY <code>*.constructionInfo</code> and <b>ALL</b> <code>*cad.stl</code> files found in the project folder.</li>
                <li><b>Send to Print:</b> Copies ONLY <code>*model*.stl</code> files (e.g., model.stl, modelbase.stl).</li>
                <li><b>Duplicate Files:</b>
                    <ul style='margin-left: 0px; padding-left: 20px;'>
                        <li>Manual Send: Action ({self.duplicate_check_action_setting.capitalize()}) configured in Settings.</li>
                        <li>Auto Send/Triggers: Separate setting ({self.auto_duplicate_action_setting.capitalize()}) for automatic handling to avoid intrusive popups.</li>
                     </ul>
                 </li>
                 <li><b>Double-Click Row:</b> Opens 3D viewer (VTK required) for associated STLs (shows actual filenames).</li>
                <li><b>Right-Click Row & Buttons:</b> Offers Send, Open Folder actions.</li>
                <li><b>Archiving (if enabled):</b> Moves older files from Target root to <code>YYYY/MM/DD</code> subfolders before copying new files.</li>
                <li><b>Menu Bar & Main Buttons:</b> Use 'File' menu or buttons ( <img src=':/qt-project.org/styles/commonstyle/images/diropen-16.png' height=14 width=14> Open CAM/Print Target ) to open target folders directly.</li>
                <li><b>Hotkey (Current: {self.hotkey_combo.upper() if KEYBOARD_AVAILABLE else 'N/A'}):</b> Triggers a new manual scan. <i style='color: #909095;'>(May require admin rights)</i></li>
            </ul>
            </p>
            <p style='font-size: 8pt; color: #808085;'>Built with Python {sys.version_info.major}.{sys.version_info.minor}, PyQt6{', VTK 9+' if VTK_AVAILABLE else ''}{', Watchdog' if WATCHDOG_AVAILABLE else ''}{', Keyboard' if KEYBOARD_AVAILABLE else ''}.</p>
            """
        try:
            icon_pixmap = get_icon("icon.png", fallback_pixmap=QStyle.StandardPixmap.SP_MessageBoxInformation,
                                   size=64).pixmap(64, 64)
            msg_box = QMessageBox(self);
            msg_box.setWindowTitle(f"About {APP_NAME}");
            msg_box.setTextFormat(Qt.TextFormat.RichText);
            msg_box.setText(about_text)
            msg_box.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction | Qt.TextInteractionFlag.LinksAccessibleByMouse); # Enable links
            if not icon_pixmap.isNull(): msg_box.setIconPixmap(icon_pixmap)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setStyleSheet(NEON_VOID_STYLE);
            msg_box.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not display About information.\n{e}")

    def open_settings_window(self):
        """Opens the Settings dialog and handles applying changes."""
        if self.active_notification_dialog and self.active_notification_dialog.isVisible():
            print("[Settings] Closing active notification dialog before opening settings.")
            try:
                self.active_notification_dialog.reject(); self.active_notification_dialog = None
            except Exception: pass

        self.stop_hotkey_listener(intentional=True)
        self.stop_file_watcher()

        dialog = SettingsDialog(self.settings, self)
        result = dialog.exec()
        hotkey_actually_changed = False
        if result == QDialog.DialogCode.Accepted:
            if KEYBOARD_AVAILABLE and dialog.new_hotkey_value is not None and self.hotkey_combo != dialog.new_hotkey_value:
                hotkey_actually_changed = True
                print(f"[Settings] Hotkey changed from '{self.hotkey_combo}' to '{dialog.new_hotkey_value}'.")

            self.reload_settings_and_update_ui() # This reloads all settings from storage

            self.start_hotkey_listener(force_restart=hotkey_actually_changed)
            if not self.fs_observer and (self.live_notify_enabled or self.auto_send_enabled):
                 print("[Settings] Restarting file watcher after settings close (was stopped).")
                 self.start_file_watcher()

        else: # User cancelled settings dialog
             print("[Settings] Settings cancelled, restarting listeners/watchers if they were active.")
             self.start_hotkey_listener() # Restarts if needed based on old settings
             self.start_file_watcher() # Restarts if needed based on old settings


    def show_window(self):
        """Shows and brings the main window to the front."""
        if self.isHidden() or self.isMinimized(): self.showNormal()
        self.activateWindow();
        self.raise_()

    def hide_to_tray(self):
        """Hides the window to the system tray (if tray icon exists)."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
        else: # If no tray icon, maybe just minimize? Or show warning?
            print("Warning: No tray icon available, cannot hide to tray.")

    def on_tray_icon_activated(self, reason):
        """Handles single/double clicks on the tray icon."""
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def update_status_bar(self):
        """Updates the text in the status bar labels based on current settings."""
        watch_display = shorten_path(self.watch_folder) if self.watch_folder else "N/A"
        cam_target_display = shorten_path(self.target_folder_cam) if self.target_folder_cam else "N/A"
        print_target_display = shorten_path(self.target_folder_print) if self.target_folder_print else "N/A"

        archive_status = "ON" if self.archive_enabled else "OFF"
        archive_display = f"💾 Archive: {archive_status}"

        hotkey_info = self.hotkey_combo.upper() if KEYBOARD_AVAILABLE else "N/A"
        hotkey_display = f"⚡ Hotkey: {hotkey_info}"

        notify_status = "OFF"
        if self.live_notify_enabled:
            notify_status = f"ON ({self.notify_debounce_secs}s)" if WATCHDOG_AVAILABLE else "OFF (No Watchdog)"
        live_notify_display = f"🔔 Notify: {notify_status}"

        auto_send_status_str = "OFF"
        if self.auto_send_enabled:
            auto_send_status_str = "ON" if WATCHDOG_AVAILABLE else "OFF (No Watchdog)"
        auto_send_display = f"🤖 AutoSend: {auto_send_status_str}"

        auto_dup_status = "N/A"
        if WATCHDOG_AVAILABLE and self.auto_send_enabled:
             auto_dup_status = self.auto_duplicate_action_setting.capitalize()
        auto_dup_display = f"⚙️AutoDup: {auto_dup_status}"


        self.watch_status_label.setText(f"👁️ Watch: {watch_display}")
        self.watch_status_label.setToolTip(self.watch_folder if self.watch_folder else "Watch folder not set")

        self.cam_target_status_label.setText(f"➡️ CAM: {cam_target_display}")
        self.cam_target_status_label.setToolTip(self.target_folder_cam if self.target_folder_cam else "Target (CAM) folder not set")

        self.print_target_status_label.setText(f"🖨️ Print: {print_target_display}")
        self.print_target_status_label.setToolTip(self.target_folder_print if self.target_folder_print else "Target (Print) folder not set")

        self.archive_status_label.setText(archive_display)
        self.archive_status_label.setToolTip("Archive old files in Target folders before copy" if self.archive_enabled else "Automatic archiving disabled")

        self.live_notify_status_label.setText(live_notify_display)
        notify_tooltip = "Live file change notifications disabled."
        if self.live_notify_enabled: notify_tooltip = f"Show popup on file change (Cooldown: {self.notify_debounce_secs}s)" if WATCHDOG_AVAILABLE else "Live notifications disabled (requires 'watchdog')"
        self.live_notify_status_label.setToolTip(notify_tooltip)

        self.auto_send_status_label.setText(auto_send_display)
        autosend_tooltip = "Automatic file sending disabled."
        if self.auto_send_enabled: autosend_tooltip = "Automatically send files once per day on change" if WATCHDOG_AVAILABLE else "Auto-send disabled (requires 'watchdog')"
        self.auto_send_status_label.setToolTip(autosend_tooltip)

        self.auto_dup_status_label.setText(auto_dup_display)
        autodup_tooltip = "Automatic duplicate handling setting (for Auto-Send/Triggers)."
        if not (WATCHDOG_AVAILABLE and self.auto_send_enabled): autodup_tooltip = "N/A (Requires Watchdog and Auto-Send enabled)"
        self.auto_dup_status_label.setToolTip(autodup_tooltip + f"\nCurrent: {self.auto_duplicate_action_setting.capitalize()}")

        self.hotkey_status_label.setText(hotkey_display)
        hotkey_tooltip = "Global hotkey disabled (requires 'keyboard' library)."
        if KEYBOARD_AVAILABLE: hotkey_tooltip = f"Press {self.hotkey_combo.upper()} to trigger manual scan"
        self.hotkey_status_label.setToolTip(hotkey_tooltip)

        can_open_cam_target = bool(self.target_folder_cam)
        can_open_print_target = bool(self.target_folder_print)
        if hasattr(self, 'target_folder_cam_action_ref'): self.target_folder_cam_action_ref.setEnabled(can_open_cam_target)
        if hasattr(self, 'target_folder_print_action_ref'): self.target_folder_print_action_ref.setEnabled(can_open_print_target)

        if hasattr(self, 'open_cam_folder_button'): self.open_cam_folder_button.setEnabled(can_open_cam_target and not self.is_operation_running)
        if hasattr(self, 'open_print_folder_button'): self.open_print_folder_button.setEnabled(can_open_print_target and not self.is_operation_running)


    def update_hotkey_ui_elements(self):
        """Updates UI elements related to scanning (info label, tooltips) based on hotkey and watcher status."""
        hotkey_upper = self.hotkey_combo.upper() if KEYBOARD_AVAILABLE else "N/A"
        tooltip_text = f"Scan Watch Folder ({hotkey_upper})" if KEYBOARD_AVAILABLE else "Scan Watch Folder (Hotkey disabled)"
        scan_label = f"Press {hotkey_upper} or click Scan" if KEYBOARD_AVAILABLE else "Click Scan"

        watcher_status = []
        if WATCHDOG_AVAILABLE:
            if self.live_notify_enabled: watcher_status.append(f"Notifications ON ({self.notify_debounce_secs}s)")
            if self.auto_send_enabled: watcher_status.append("Auto-Send ON (Once/Day)")
            if not watcher_status: watcher_status.append("Real-time OFF")
        else:
            if self.live_notify_enabled or self.auto_send_enabled:
                watcher_status.append("(Real-time features require 'watchdog')") # warning if enabled but lib missing
            else:
                 watcher_status.append("(Real-time OFF)")
        watcher_info = f"({', '.join(watcher_status)})"

        viewer_info = "(Double-click row to view STLs)" if VTK_AVAILABLE else "(STL Viewer disabled)"

        if hasattr(self, 'info_label'):
            if not self.table_widget or self.table_widget.rowCount() == 0:
                 self.info_label.setText(f"Ready. {scan_label} to find projects. {watcher_info} {viewer_info}")

        if hasattr(self, 'scan_button'):
            self.scan_button.setToolTip(tooltip_text)
        if hasattr(self, 'scan_tray_action') and self.scan_tray_action:
            self.scan_tray_action.setText(f"Scan Now ({hotkey_upper})" if KEYBOARD_AVAILABLE else "Scan Now")
        self.update_status_bar() # Ensure status bar is also updated

    def check_folders_exist(self):
        """Checks if essential folders (watch, target) are set and valid. Updates status bar."""
        error_messages = []
        warning_messages = []
        valid_watch = False
        valid_target_cam = False
        valid_target_print = False # Optional unless auto-send or print actions used

        if not self.watch_folder: error_messages.append("Watch folder missing")
        elif not os.path.isdir(self.watch_folder): error_messages.append(f"Watch folder invalid: {shorten_path(self.watch_folder)}")
        else: valid_watch = True

        if not self.target_folder_cam: error_messages.append("Target (CAM) folder missing")
        else:
            valid_target_cam = True
            if not os.path.isdir(self.target_folder_cam): warning_messages.append(f"Target (CAM) folder will be created: {shorten_path(self.target_folder_cam)}")

        if not self.target_folder_print:
            if self.auto_send_enabled: error_messages.append("Target (Print) missing (needed for Auto-Send)")
            else: warning_messages.append("Target (Print) folder not set ('Send to Print' disabled)")
        else:
            valid_target_print = True
            if not os.path.isdir(self.target_folder_print): warning_messages.append(f"Target (Print) folder will be created: {shorten_path(self.target_folder_print)}")

        is_config_ok_for_scan = valid_watch
        self.update_status_bar() # Reflect current status

        status_msg = ""
        all_msgs = error_messages + warning_messages
        if all_msgs:
            prefix = " | CONFIG ERROR: " if error_messages else " | Config Warning: "
            status_msg = prefix + ", ".join(all_msgs)
            self.statusBar.showMessage(status_msg, 10000 if error_messages else 5000)
        else:
             self.statusBar.clearMessage()


        self.update_button_state() # Enable/disable buttons based on validity
        return is_config_ok_for_scan

    def handle_hotkey_press(self):
        """Handles the signal from the HotkeyListener thread."""
        if not self.is_listener_intentionally_stopped and not self.is_operation_running:
            print(f"Hotkey '{self.hotkey_combo}' detected, triggering scan...")
            self.show_window() # Bring window to front
            QTimer.singleShot(50, self.scan_and_show) # Delay slightly to ensure window shows first
        else:
            reason = "operation running" if self.is_operation_running else "listener intentionally stopped"
            print(f"Hotkey '{self.hotkey_combo}' ignored: {reason}")

    # filesystem change handler
    def handle_filesystem_change(self, changed_path):
        """Handles the signal from Watchdog when a relevant file changes."""
        print(f"[Watcher Trigger] Received signal for path: {changed_path}")
        if self.is_operation_running:
            print("[Watcher Trigger] Ignored: Another operation is running.")
            return
        if not WATCHDOG_AVAILABLE:
            print("[Watcher Trigger] Ignored: Watchdog library not available.")
            return

        try:
            folder_path = os.path.dirname(os.path.abspath(changed_path))
            folder_path_norm = os.path.normpath(folder_path)
            if not folder_path_norm or folder_path_norm == '.':
                print(f"[Watcher Trigger] Ignoring file change in invalid/root path: {changed_path}")
                return
            if not folder_path_norm.startswith(os.path.normpath(self.watch_folder)):
                 print(f"[Watcher Trigger] Ignored: Change detected outside watch folder: {folder_path_norm}")
                 return

        except Exception as e:
            print(f"[Watcher Trigger] Could not get folder path for change: {changed_path}. Error: {e}")
            return

        if not self.live_notify_enabled and not self.auto_send_enabled:
            return

        now = time.time()
        notification_debounce_passed = True
        folder_display_name = os.path.basename(folder_path_norm)

        if self.live_notify_enabled:
            last_notify_time = self.recently_notified_projects.get(folder_path_norm, 0)
            elapsed = now - last_notify_time
            if elapsed < self.notify_debounce_secs:
                notification_debounce_passed = False
                print(f"[Watcher Trigger] Notification debounce active for '{folder_display_name}'. {elapsed:.1f}s < {self.notify_debounce_secs}s")
            else:
                print(f"[Watcher Trigger] Notification debounce passed for '{folder_display_name}'.")
                pass # We will update the timestamp in the processing function

        print(f"[Watcher Trigger] Scheduling processing for '{folder_display_name}'...")
        QTimer.singleShot(750, lambda: self._process_change_trigger(folder_path_norm, notification_debounce_passed))

    def _process_change_trigger(self, folder_path_norm, notification_debounce_passed):
        """Scans the specific folder and decides whether to notify or auto-send."""
        folder_display_name = os.path.basename(folder_path_norm)
        print(f"[Watcher Process] Processing trigger for: {folder_display_name}")

        if self.is_operation_running:
            print(f"[Watcher Process] Skipped processing '{folder_display_name}': Another operation is running.")
            return

        found_projects = scan_directory(self.watch_folder, target_folder=folder_path_norm)

        if not found_projects:
            print(f"[Watcher Process] Scan found no project data in '{folder_display_name}'. Cannot process trigger.")
            return

        item_data = found_projects[0]
        patient_name = item_data.get('patient', folder_display_name) # Use folder name as fallback

        can_auto_send_cam = False
        can_auto_send_print = False
        can_notify = False

        cam_ready = item_data.get('has_cad', False) and item_data.get('has_info', False)
        cam_target_ok = bool(self.target_folder_cam)
        already_sent_cam = self.has_been_auto_sent(folder_path_norm, "cam")
        if self.auto_send_enabled and cam_ready and cam_target_ok and not already_sent_cam:
            can_auto_send_cam = True
        elif self.auto_send_enabled:
             reasons = []
             if not cam_ready: reasons.append("CAM files not ready")
             if not cam_target_ok: reasons.append("CAM target not set")
             if already_sent_cam: reasons.append("Already sent CAM today")
             if reasons: print(f"[Watcher Process] Cannot Auto-Send CAM for '{patient_name}': {', '.join(reasons)}")


        print_ready = item_data.get('has_models', False)
        print_target_ok = bool(self.target_folder_print)
        already_sent_print = self.has_been_auto_sent(folder_path_norm, "print")
        if self.auto_send_enabled and print_ready and print_target_ok and not already_sent_print:
            can_auto_send_print = True
        elif self.auto_send_enabled:
             reasons = []
             if not print_ready: reasons.append("Print files not ready")
             if not print_target_ok: reasons.append("Print target not set")
             if already_sent_print: reasons.append("Already sent Print today")
             if reasons: print(f"[Watcher Process] Cannot Auto-Send Print for '{patient_name}': {', '.join(reasons)}")


        popup_active = self.active_notification_dialog and self.active_notification_dialog.isVisible()
        if self.live_notify_enabled and notification_debounce_passed and not popup_active:
            can_notify = True
        elif self.live_notify_enabled:
            reasons = []
            if not notification_debounce_passed: reasons.append("Debounce active")
            if popup_active: reasons.append("Another popup active")
            if reasons: print(f"[Watcher Process] Cannot Notify for '{patient_name}': {', '.join(reasons)}")

        action_taken_this_trigger = False

        if can_auto_send_cam:
            print(f"[Watcher Process] Auto-sending CAM for: {patient_name}")
            self.statusBar.showMessage(f"🤖 Auto-sending CAM: {patient_name}...", 5000)
            QCoreApplication.processEvents()
            success = self.send_cam_for_project(item_data, is_auto=True) # is_auto=True uses auto duplicate setting
            if success:
                self.update_auto_send_status(folder_path_norm, "cam") # Mark as sent *after* success
                action_taken_this_trigger = True
            self.statusBar.clearMessage() # Clear status bar after action

        if can_auto_send_print:
            print(f"[Watcher Process] Auto-sending Print for: {patient_name}")
            self.statusBar.showMessage(f"🤖 Auto-sending Print: {patient_name}...", 5000)
            QCoreApplication.processEvents()
            success = self.send_print_for_project(item_data, is_auto=True) # is_auto=True
            if success:
                self.update_auto_send_status(folder_path_norm, "print")
                action_taken_this_trigger = True
            self.statusBar.clearMessage()

        if can_notify and not action_taken_this_trigger:
            print(f"[Watcher Process] Showing notification for project: {patient_name}")
            self.recently_notified_projects[folder_path_norm] = time.time()

            self.active_notification_dialog = NotificationDialog(item_data, self, parent=self)
            self.active_notification_dialog.finished.connect(self._notification_dialog_closed)
            self.active_notification_dialog.show()

        elif can_notify and action_taken_this_trigger:
            print(f"[Watcher Process] Auto-send completed for '{patient_name}'. Notification skipped for this trigger.")

        elif not can_notify and not can_auto_send_cam and not can_auto_send_print:
             print(f"[Watcher Process] No action taken for '{patient_name}' on this trigger (check logs above for reasons).")


    def _notification_dialog_closed(self, result_code):
        """Callback when the notification dialog is closed (clears reference)."""
        sender_dialog = self.sender()
        if sender_dialog == self.active_notification_dialog:
             print("[Notification] Dialog closed.")
             self.active_notification_dialog = None
        try:
             if sender_dialog: sender_dialog.finished.disconnect(self._notification_dialog_closed)
        except TypeError: pass # already disconnected
        except Exception as e:
            print(f"Error disconnecting notification finished signal: {e}")

    # manual/hotkey scan function
    def scan_and_show(self):
        """Performs the full directory scan and populates the table."""
        if self.is_operation_running:
            print("Scan skipped: Another operation is already running.")
            self.statusBar.showMessage("Scan skipped: Operation in progress.", 3000)
            return
        if not self.check_folders_exist(): # check_folders_exist shows its own message
            return

        self.is_operation_running = True
        self.update_button_state() # Disable buttons during scan
        self.statusBar.showMessage(f"Scanning '{shorten_path(self.watch_folder)}' for projects modified today...", 0) # Persistent message
        self.info_label.setText(f"Scanning '{shorten_path(self.watch_folder)}'...")
        QCoreApplication.processEvents() # Update UI

        self.table_widget.setSortingEnabled(False) # Disable sorting during population
        self.table_widget.setRowCount(0)

        found_files_data = []
        scan_error = None
        start_time = time.time()
        try:
            found_files_data = scan_directory(self.watch_folder)
        except Exception as e:
            scan_error = e
            print(f"Scan Error: {e}")
            QMessageBox.critical(self, "Scan Error", f"An unexpected error occurred during scan:\n{e}")
        finally:
            end_time = time.time()
            scan_duration = end_time - start_time
            print(f"Scan finished in {scan_duration:.2f} seconds.")

            if found_files_data:
                count = len(found_files_data);
                plural_s = "s" if count != 1 else ""
                viewer_info = "(Double-click row to view STLs)" if VTK_AVAILABLE else "(STL Viewer disabled)"
                self.info_label.setText(f"Found {count} project{plural_s} modified today. {viewer_info}")
                self.statusBar.showMessage(f"Scan complete: Found {count} project{plural_s}. ({scan_duration:.2f}s)", 5000) # Timed message

                self.table_widget.setUpdatesEnabled(False) # Batch update start
                try:
                    self.table_widget.setRowCount(count) # Pre-allocate rows
                    for row, item_data in enumerate(found_files_data):
                        timestamp_for_sort = int(item_data["last_modified_timestamp"])
                        relative_time_str = get_relative_time(item_data["last_modified_timestamp"])
                        item_time = QTableWidgetItem(relative_time_str)
                        item_time.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        item_time.setData(Qt.ItemDataRole.UserRole + 1, timestamp_for_sort) # Store timestamp for sorting
                        item_time.setData(Qt.ItemDataRole.UserRole, item_data)

                        item_patient = QTableWidgetItem(item_data["patient"])
                        item_patient.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                        item_work = QTableWidgetItem(item_data["work_type"])
                        item_work.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                        item_teeth = QTableWidgetItem(item_data["teeth"])
                        if "Full Arch" in item_data["teeth"]:
                             item_teeth.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        else:
                             item_teeth.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)


                        item_status = QTableWidgetItem(item_data["file_status"])
                        item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        icons = item_data.get("status_icons", ("?", "?", "?"))
                        if all(i == "✓" for i in icons): item_status.setForeground(QColor("#00FF7F")) # Green (all ok)
                        elif any(i == "✓" for i in icons): item_status.setForeground(QColor("#FFD700")) # Yellow (partial)
                        else: item_status.setForeground(QColor("#FF4D4D")) # Red (none ok)

                        self.table_widget.setItem(row, 0, item_time)
                        self.table_widget.setItem(row, 1, item_patient)
                        self.table_widget.setItem(row, 2, item_work)
                        self.table_widget.setItem(row, 3, item_teeth)
                        self.table_widget.setItem(row, 4, item_status)

                        tooltip_text = self.generate_row_tooltip(item_data)
                        item_time.setToolTip(tooltip_text) # Apply tooltip to first cell, spans row

                finally:
                    self.table_widget.setUpdatesEnabled(True) # Batch update end
                    self.table_widget.setSortingEnabled(True) # Re-enable sorting
                    self.table_widget.sortByColumn(0, Qt.SortOrder.DescendingOrder)

            elif not scan_error: # Scan finished ok, but no files found
                self.info_label.setText(
                    f"No projects modified today found in '{shorten_path(self.watch_folder)}'.")
                self.statusBar.showMessage(f"Scan complete: No projects found modified today. ({scan_duration:.2f}s)", 5000)
            else: # Scan failed
                 self.info_label.setText("Scan failed. Check error messages.")
                 self.statusBar.showMessage(f"Scan failed! ({scan_duration:.1f}s)", 5000)


            self.is_operation_running = False # Operation finished
            self.update_button_state() # Re-enable buttons

    def generate_row_tooltip(self, item_data):
        """Generates rich text tooltip for a table row."""
        tooltip_lines = []
        pd = item_data.get('parsed_data')
        exact_time = datetime.datetime.fromtimestamp(item_data['last_modified_timestamp'])
        exact_time_str = exact_time.strftime('%Y-%m-%d %H:%M:%S')
        relative_time_str = get_relative_time(item_data['last_modified_timestamp'])

        tooltip_lines.append(f"<b style='color:#00E5E5;'>{item_data.get('patient','?')}</b>")
        if pd and pd.get('practice'): tooltip_lines.append(f"Practice: {pd.get('practice')}")
        tooltip_lines.append(f"Work: {item_data.get('work_type','N/A')} ({item_data.get('teeth','?')})")
        tooltip_lines.append(f"Last Change (Today): {exact_time_str} ({relative_time_str})")
        tooltip_lines.append("---")
        tooltip_lines.append(f"Folder: ...{os.sep}{os.path.basename(item_data.get('folder_path','?'))}")
        project_file = os.path.basename(item_data['project_path']) if item_data.get('project_path') else 'N/A'
        tooltip_lines.append(f"Project File: {project_file}")
        tooltip_lines.append("---")
        info_name = os.path.basename(item_data['info_path']) if item_data.get('info_path') else 'N/A'
        cad_stl_paths = item_data.get('cad_stl_paths', [])
        cad_stl_names = [os.path.basename(p) for p in cad_stl_paths if p]
        model_stl_paths = item_data.get('model_stl_paths', [])
        model_stl_names = [os.path.basename(p) for p in model_stl_paths if p]

        has_cad = item_data.get("has_cad", False)
        has_info = item_data.get("has_info", False)
        has_models = item_data.get("has_models", False)
        cad_status = "<span style='color:#00FF7F;'>✓</span>" if has_cad else "<span style='color:#FF4D4D;'>✗</span>"
        info_status = "<span style='color:#00FF7F;'>✓</span>" if has_info else "<span style='color:#FF4D4D;'>✗</span>"
        model_status = "<span style='color:#00FF7F;'>✓</span>" if has_models else "<span style='color:#FF4D4D;'>✗</span>"

        tooltip_lines.append(f"CAM Files: {cad_status}CAD ({len(cad_stl_names)}) {info_status}Info ({info_name})")
        tooltip_lines.append(f"Print Files: {model_status}Model ({len(model_stl_names)})")

        if cad_stl_names:
           tooltip_lines.append("  <b>CAD STLs:</b>")
           for i, name in enumerate(cad_stl_names):
               if i < 4: tooltip_lines.append(f"   - {name}")
               elif i == 4: tooltip_lines.append("   - ... (and others)"); break

        if model_stl_names:
           tooltip_lines.append("  <b>Model STLs:</b>")
           for i, name in enumerate(model_stl_names):
               if i < 4: tooltip_lines.append(f"   - {name}")
               elif i == 4: tooltip_lines.append("   - ... (and others)"); break


        has_any_stl = bool(cad_stl_paths or model_stl_paths or item_data.get('other_stl_paths'))
        if VTK_AVAILABLE and has_any_stl:
            tooltip_lines.append("---")
            tooltip_lines.append("<i style='color:#00A0A0;'>Double-click row to view STLs</i>")
        elif not VTK_AVAILABLE and has_any_stl:
             tooltip_lines.append("---")
             tooltip_lines.append("<i style='color:#FFA500;'>STL Viewer disabled (VTK missing)</i>")


        return "<br>".join(tooltip_lines).replace("\n", "<br>")


    # show the stl viewer method
    def show_stl_viewer_for_project(self, item_data):
        """Opens the STL viewer dialog for the given project data."""
        if not item_data or self.is_operation_running: return
        if not VTK_AVAILABLE:
            self.statusBar.showMessage("STL Viewer disabled: VTK library not found.", 4000)
            return

        stl_files_to_view = {}
        project_folder = item_data.get('folder_path', '')

        cad_paths = item_data.get('cad_stl_paths', [])
        for path in cad_paths:
            if path and os.path.exists(path):
                rel_path = os.path.relpath(path, project_folder) if project_folder else os.path.basename(path)
                display_name = f"[CAD] {rel_path}"
                counter = 1; original_display_name = display_name
                while display_name in stl_files_to_view: display_name = f"{original_display_name} ({counter})"; counter += 1
                stl_files_to_view[display_name] = path

        model_paths = item_data.get('model_stl_paths', [])
        for path in model_paths:
            if path and os.path.exists(path):
                rel_path = os.path.relpath(path, project_folder) if project_folder else os.path.basename(path)
                display_name = f"[Model] {rel_path}"
                counter = 1; original_display_name = display_name
                while display_name in stl_files_to_view: base, ext = os.path.splitext(original_display_name); display_name = f"{base} ({counter}){ext}"; counter += 1
                stl_files_to_view[display_name] = path

        other_paths = item_data.get('other_stl_paths', [])
        for path in other_paths:
            if path and os.path.exists(path):
                rel_path = os.path.relpath(path, project_folder) if project_folder else os.path.basename(path)
                display_name = f"[Other] {rel_path}"
                counter = 1; original_display_name = display_name
                while display_name in stl_files_to_view: base, ext = os.path.splitext(original_display_name); display_name = f"{base} ({counter}){ext}"; counter += 1
                stl_files_to_view[display_name] = path

        if not stl_files_to_view:
            QMessageBox.information(self, "No STL Files",
                                    f"No viewable STL files were found associated with project:\n{item_data.get('patient', 'Unknown')}")
            return

        self.stop_hotkey_listener(intentional=False); # False = temporarily stopped
        self.stop_file_watcher() # Stop watcher too

        try:
            project_display_name = item_data.get('patient', 'STL Viewer')
            if self.current_stl_viewer and self.current_stl_viewer.isVisible():
                print("Closing existing STL viewer before opening new one.")
                try: self.current_stl_viewer.close(); self.current_stl_viewer.deleteLater()
                except Exception: pass
                QCoreApplication.processEvents() # Allow cleanup

            self.current_stl_viewer = StlViewerDialog(stl_files_to_view, project_display_name, self)
            self.current_stl_viewer.finished.connect(self._handle_viewer_closed) # Connect signal to restart listeners
            self.current_stl_viewer.show()
        except Exception as e_viewer:
            QMessageBox.critical(self, "Viewer Launch Error", f"Failed to open the STL viewer:\n{e_viewer}")
            self.start_hotkey_listener();
            self.start_file_watcher()

    def handle_table_double_click(self, item):
        """Opens the STL viewer when a table row is double-clicked."""
        if not item: return
        row = item.row();
        item0 = self.table_widget.item(row, 0)
        item_data = item0.data(Qt.ItemDataRole.UserRole) if item0 else None
        if item_data:
            self.show_stl_viewer_for_project(item_data)
        else:
            QMessageBox.warning(self, "Error", "Could not retrieve data for the selected row.")

    def _handle_viewer_closed(self, result_code):
        """Callback when the STL viewer dialog is closed. Restarts listeners."""
        print("STL Viewer closed, restarting listeners/watchers...")
        self.current_stl_viewer = None
        QTimer.singleShot(50, self.start_hotkey_listener)
        QTimer.singleShot(60, self.start_file_watcher)

    # handle table context menu (right click)
    def show_table_context_menu(self, point):
        """Shows the right-click context menu for a table row."""
        if self.is_operation_running: return

        if self.active_notification_dialog and self.active_notification_dialog.isVisible():
            print("[Context Menu] Closing active notification dialog.")
            try: self.active_notification_dialog.reject(); self.active_notification_dialog = None
            except Exception: pass

        self.stop_hotkey_listener(intentional=False);
        self.stop_file_watcher()

        try:
            index = self.table_widget.indexAt(point)
            if not index.isValid():
                print("[Context Menu] Invalid index.")
                self.start_hotkey_listener(); self.start_file_watcher(); return

            row = index.row();
            item_data = None
            item0 = self.table_widget.item(row, 0) # Get item from first column
            if item0: item_data = item0.data(Qt.ItemDataRole.UserRole) # Retrieve stored dict

            if not item_data:
                print(f"[Context Menu] No data found for row {row}.")
                self.start_hotkey_listener(); self.start_file_watcher(); return

            menu = QMenu(self);
            menu.setStyleSheet(NEON_VOID_STYLE) # Apply theme to menu

            action_send_print = QAction("Send Models to Print", self)
            can_send_print = item_data.get('has_models', False) and bool(self.target_folder_print)
            num_models = len(item_data.get('model_stl_paths', []))
            action_send_print.setText(f"Send to Print ({num_models} *model*.stl)...")
            action_send_print.setEnabled(can_send_print)
            if can_send_print:
                action_send_print.setToolTip(f"Copy {num_models} model file(s) to:\n{shorten_path(self.target_folder_print)}")
                action_send_print.triggered.connect(partial(self.send_print_for_project, item_data, is_auto=False))
            else:
                reason = "Target (Print) folder not set" if not self.target_folder_print else "No model files found"
                action_send_print.setToolTip(f"Cannot send to print: {reason}.")
            menu.addAction(action_send_print)

            action_send_cam = QAction("Send Project to CAM", self)
            has_cad = item_data.get('has_cad', False)
            has_info = item_data.get('has_info', False)
            has_required_files = has_cad and has_info
            can_send_cam = has_required_files and bool(self.target_folder_cam)
            num_cad_stls = len(item_data.get('cad_stl_paths', []))
            num_info = 1 if item_data.get('info_path') and os.path.exists(item_data['info_path']) else 0
            num_files = num_cad_stls + num_info

            action_send_cam.setText(f"Send to CAM ({num_files} files)...")
            action_send_cam.setEnabled(can_send_cam)
            if can_send_cam:
                action_send_cam.setToolTip(f"Copy {num_files} file(s) (ALL *cad.stl, *.info) to:\n{shorten_path(self.target_folder_cam)}")
                action_send_cam.triggered.connect(partial(self.send_cam_for_project, item_data, is_auto=False)) # is_auto=False
            else:
                reason = "Target (CAM) folder not set" if not self.target_folder_cam else \
                         ("Missing required Info file" if has_cad and not has_info else \
                          ("Missing required CAD file(s)" if not has_cad and has_info else \
                           "Missing required CAD file(s) and Info file"))
                action_send_cam.setToolTip(f"Cannot send to CAM: {reason}.")
            menu.addAction(action_send_cam)

            menu.addSeparator()

            if VTK_AVAILABLE:
                action_preview = QAction("3D Preview STLs...", self)
                can_preview = item_data.get('has_cad') or item_data.get('has_models') or item_data.get('other_stl_paths')
                action_preview.setEnabled(can_preview)
                action_preview.setToolTip("Open 3D viewer for available STLs" if can_preview else "No STLs found to preview")
                if can_preview:
                    action_preview.triggered.connect(partial(self.show_stl_viewer_for_project, item_data))
                menu.addAction(action_preview)
                menu.addSeparator()


            action_open_folder = QAction("Open Project Folder...", self)
            folder_path = item_data.get('folder_path')
            can_open = bool(folder_path) and os.path.isdir(folder_path)
            action_open_folder.setEnabled(can_open)
            action_open_folder.setToolTip(f"Open source folder:\n{folder_path}" if can_open else "Source folder path unknown or invalid")
            if can_open: action_open_folder.triggered.connect(partial(self.open_folder_in_explorer, folder_path))
            menu.addAction(action_open_folder)

            action_open_target_cam = QAction("Open Target Folder (CAM)", self)
            can_open_target_cam = bool(self.target_folder_cam)
            action_open_target_cam.setEnabled(can_open_target_cam)
            action_open_target_cam.setToolTip(f"Open: {shorten_path(self.target_folder_cam)}" if can_open_target_cam else "Target (CAM) folder not set")
            if can_open_target_cam: action_open_target_cam.triggered.connect(lambda: self.open_folder_in_explorer(self.target_folder_cam))
            menu.addAction(action_open_target_cam)

            action_open_target_print = QAction("Open Target Folder (Print)", self)
            can_open_target_print = bool(self.target_folder_print)
            action_open_target_print.setEnabled(can_open_target_print)
            action_open_target_print.setToolTip(f"Open: {shorten_path(self.target_folder_print)}" if can_open_target_print else "Target (Print) folder not set")
            if can_open_target_print: action_open_target_print.triggered.connect(lambda: self.open_folder_in_explorer(self.target_folder_print))
            menu.addAction(action_open_target_print)


            menu.aboutToHide.connect(self._handle_menu_closed)
            menu.exec(self.table_widget.viewport().mapToGlobal(point))

        except Exception as e_menu:
            QMessageBox.critical(self, "Menu Error",
                                 f"A Python error occurred while creating the context menu:\n{e_menu}")
            self.start_hotkey_listener();
            self.start_file_watcher()

    def _handle_menu_closed(self):
        """Restarts listeners after the context menu is hidden."""
        sender = self.sender()
        if isinstance(sender, QMenu):
            try: sender.aboutToHide.disconnect(self._handle_menu_closed)
            except TypeError: pass # Already disconnected
        print("[Context Menu] Closed, restarting listeners.")
        QTimer.singleShot(10, self.start_hotkey_listener)
        QTimer.singleShot(20, self.start_file_watcher)


    # archiving logic implementation
    def trigger_archive_if_needed(self, target_folder, folder_type_name):
        """Checks if archiving is enabled and needed for today, then runs it."""
        archive_stats = {"moved": 0, "errors": 0}
        if not self.archive_enabled:
            return archive_stats
        if not target_folder or not os.path.isdir(target_folder):
             print(f"Archiving skipped for {folder_type_name}: Target folder invalid or not set ('{target_folder}')")
             return archive_stats

        if folder_type_name == "CAM": settings_key = SETTINGS_LAST_ARCHIVE_DATE_CAM
        elif folder_type_name == "Print": settings_key = SETTINGS_LAST_ARCHIVE_DATE_PRINT
        else:
             print(f"Warning: Unknown folder type '{folder_type_name}' for archiving.")
             return archive_stats # Unknown type, cannot archive

        today_str = datetime.date.today().isoformat()
        last_archive_date = self.settings.value(settings_key, "")

        if last_archive_date == today_str:
             return archive_stats # Already archived today

        print(f"Archiving check needed for {folder_type_name} folder...")
        self.statusBar.showMessage(f"Checking for old files to archive in {folder_type_name} folder...", 0)
        QCoreApplication.processEvents()

        try:
            archive_stats = self.archive_old_files_in_target(target_folder)
            moved = archive_stats.get("moved", 0)
            errors = archive_stats.get("errors", 0)
            print(f"Archiving for {folder_type_name} complete: Moved {moved} files, Errors: {errors}.")
            if errors == 0:
                self.settings.setValue(settings_key, today_str)
                self.settings.sync()
                print(f"Updated last archive date for {folder_type_name} to {today_str}.")
            else:
                print(f"Archive errors occurred in {folder_type_name}, not updating last archive date.")
                QMessageBox.warning(self, "Archive Error", f"Archiving for {folder_type_name} encountered {errors} error(s). Check logs. Last archive date not updated.")

        except Exception as e:
            QMessageBox.warning(self, "Archive Error",
                                f"An unexpected error occurred during archiving in {folder_type_name} folder:\n{e}")
            print(f"Unexpected archive error for {folder_type_name}: {e}")
        finally:
            self.statusBar.clearMessage()

        return archive_stats

    def archive_old_files_in_target(self, target_folder):
        """Moves files modified *before* today from target_folder root into YYYY/MM/DD subfolders."""
        stats = {"moved": 0, "errors": 0}
        today_date = datetime.date.today()
        files_to_archive = []
        try:
            for filename in os.listdir(target_folder):
                source_path = os.path.join(target_folder, filename)
                if not os.path.isfile(source_path):
                    continue
                try:
                    mtime_ts = os.path.getmtime(source_path)
                    mod_date = datetime.date.fromtimestamp(mtime_ts)
                    if mod_date < today_date:
                        archive_subfolder_rel_path = mod_date.strftime('%Y' + os.sep + '%m' + os.sep + '%d')
                        archive_subfolder_abs_path = os.path.join(target_folder, archive_subfolder_rel_path)
                        files_to_archive.append({
                            'name': filename,
                            'path': source_path,
                            'archive_dir': archive_subfolder_abs_path,
                            'mod_date': mod_date # Store for logging if needed
                            })
                except FileNotFoundError:
                     continue # File gone, skip
                except Exception as e_stat:
                     stats["errors"] += 1
                     print(f"Error stating file for archive '{source_path}': {e_stat}")
        except Exception as e_list:
             stats["errors"] += 1
             print(f"Error listing directory for archive '{target_folder}': {e_list}")
             return stats # Cannot proceed if listing failed

        if not files_to_archive:
             return stats # Nothing to do

        print(f"Archiving {len(files_to_archive)} file(s) in {shorten_path(target_folder)}...")
        for file_info in files_to_archive:
            filename = file_info['name']; source_path = file_info['path']
            archive_dir = file_info['archive_dir']; final_dest_path = os.path.join(archive_dir, filename)
            try:
                os.makedirs(archive_dir, exist_ok=True)
                print(f"  Moving '{filename}' -> '{os.path.relpath(archive_dir, target_folder)}{os.sep}'")
                shutil.move(source_path, final_dest_path) # Use shutil.move for cross-filesystem compatibility
                stats["moved"] += 1
            except FileNotFoundError:
                 print(f"  Skipping move, source file gone: {filename}")
                 pass # Source file disappeared before move
            except PermissionError as pe:
                 stats["errors"] += 1
                 print(f"  Permission error moving '{filename}' to archive: {pe}")
            except Exception as e_move:
                 stats["errors"] += 1
                 print(f"  Error moving file '{filename}' to archive: {e_move}")

        return stats

    # core file operations (copying)
    def _copy_file_to_target(self, source_path, destination_folder, operation_stats,
                             is_multi_operation=False, is_auto_operation=False):
        """Copies a single file, handling duplicates based on settings. Updates operation_stats dict.
           Returns True on success/skip, False on error/cancel."""
        if not source_path or not os.path.exists(source_path):
            source_name = os.path.basename(source_path) if source_path else "N/A"
            err_msg = f"Source file not found: {source_name}"
            operation_stats["errors"].append({"file": source_name, "error": err_msg})
            print(f"Copy Error: {err_msg}")
            return False

        filename = os.path.basename(source_path)
        final_dest_path = os.path.join(destination_folder, filename)
        copy_action = self.DuplicateAction.OVERWRITE # Default assumes overwrite if no check needed

        if os.path.exists(final_dest_path):
            determined_action = False
            effective_duplicate_setting = self.duplicate_check_action_setting # Default to manual setting

            if is_auto_operation:
                effective_duplicate_setting = self.auto_duplicate_action_setting
                if effective_duplicate_setting == 'skip':
                    copy_action = self.DuplicateAction.SKIP
                    determined_action = True
                elif effective_duplicate_setting == 'overwrite':
                    copy_action = self.DuplicateAction.OVERWRITE
                    determined_action = True
                elif effective_duplicate_setting == 'manual':
                    effective_duplicate_setting = self.duplicate_check_action_setting
                else: # Should not happen with combo box
                     print(f"Warning: Unknown auto_duplicate setting '{effective_duplicate_setting}', defaulting to 'ask'.")
                     effective_duplicate_setting = 'ask'


            if not determined_action:
                if is_multi_operation and effective_duplicate_setting != 'ask':
                    if effective_duplicate_setting == 'skip': copy_action = self.DuplicateAction.SKIP
                    elif effective_duplicate_setting == 'overwrite': copy_action = self.DuplicateAction.OVERWRITE
                else:
                    if self.current_multi_duplicate_choice == self.DuplicateAction.ASK:
                         ask_all_option = is_multi_operation or (is_auto_operation and effective_duplicate_setting == 'ask')
                         choice = self.ask_duplicate_action(filename, destination_folder, ask_for_all=ask_all_option)
                         if choice == self.DuplicateAction.CANCEL:
                             operation_stats["cancelled"] = True; return False
                         if ask_all_option: self.current_multi_duplicate_choice = choice
                         copy_action = choice
                    else: # Apply the choice made previously in this multi-file operation
                         copy_action = self.current_multi_duplicate_choice


            if copy_action == self.DuplicateAction.SKIP:
                skip_msg = f"Skipping duplicate file{' (Auto)' if is_auto_operation and self.auto_duplicate_action_setting == 'skip' else ''}: {filename}"
                print(skip_msg)
                operation_stats["skipped"] = operation_stats.get("skipped", 0) + 1
                return True # Skipped successfully

            elif copy_action == self.DuplicateAction.CANCEL:
                print(f"User cancelled operation due to duplicate: {filename}")
                operation_stats["cancelled"] = True
                return False # Cancelled

            elif copy_action == self.DuplicateAction.OVERWRITE:
                 if (is_auto_operation and self.auto_duplicate_action_setting == 'overwrite') or \
                    (not is_auto_operation and self.duplicate_check_action_setting == 'overwrite'):
                     print(f"Overwriting duplicate file (Setting): {filename}")
                 pass # Proceed to copy below

        try:
            shutil.copy2(source_path, final_dest_path) # copy2 preserves metadata (like modification time)
            operation_stats["copied"] = operation_stats.get("copied", 0) + 1
            return True # Copied successfully
        except Exception as e:
            err_msg = f"Failed copying file '{filename}': {e}"
            operation_stats["errors"].append({"file": filename, "error": str(e)})
            print(f"Copy Error: {err_msg}")
            return False # Copy failed


    def ask_duplicate_action(self, filename, target_folder, ask_for_all=False):
        """Shows a dialog asking the user what to do with a duplicate file. Returns DuplicateAction enum."""
        self.stop_hotkey_listener(intentional=False)
        self.stop_file_watcher()

        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.setWindowTitle("Duplicate File Detected")
        msgBox.setText(f"The file '<b style='color:#00E5E5;'>{filename}</b>' already exists in the target folder:\n{shorten_path(target_folder)}")
        msgBox.setInformativeText("What would you like to do?")
        msgBox.setStyleSheet(NEON_VOID_STYLE) # Apply theme

        overwrite_button = msgBox.addButton("Overwrite", QMessageBox.ButtonRole.YesRole)
        skip_button = msgBox.addButton("Skip", QMessageBox.ButtonRole.NoRole)

        if ask_for_all:
            overwrite_all_button = msgBox.addButton("Overwrite All", QMessageBox.ButtonRole.AcceptRole)
            skip_all_button = msgBox.addButton("Skip All", QMessageBox.ButtonRole.RejectRole)
            cancel_button = msgBox.addButton("Cancel Operation", QMessageBox.ButtonRole.DestructiveRole)
            msgBox.setDefaultButton(skip_button) # Default to skip for multi-file
        else:
            cancel_button = msgBox.addButton("Cancel", QMessageBox.ButtonRole.DestructiveRole)
            msgBox.setDefaultButton(overwrite_button) # Default to overwrite for single file

        msgBox.exec()
        clicked_button = msgBox.clickedButton()

        result = self.DuplicateAction.CANCEL # Default to cancel if dialog closed unexpectedly

        if clicked_button == overwrite_button: result = self.DuplicateAction.OVERWRITE
        elif clicked_button == skip_button: result = self.DuplicateAction.SKIP
        elif ask_for_all and clicked_button == overwrite_all_button: result = self.DuplicateAction.OVERWRITE # Treat 'All' as the choice for this file too
        elif ask_for_all and clicked_button == skip_all_button: result = self.DuplicateAction.SKIP
        elif clicked_button == cancel_button: result = self.DuplicateAction.CANCEL

        QTimer.singleShot(10, self.start_hotkey_listener)
        QTimer.singleShot(20, self.start_file_watcher)
        return result


    # single project actions (from context menu or notification)
    def send_cam_for_project(self, item_data, is_auto=False):
        """Handles sending CAM files (*.info, ALL *cad.stl) for a single project.
           Uses auto-duplicate setting if is_auto=True. Returns True on success, False on failure/cancel."""
        if not isinstance(item_data, dict):
            print("[Send CAM Single] Error: Invalid item_data provided.")
            return False
        if self.is_operation_running and not is_auto: # Allow auto-send even if manual op running? No, safer to block.
             print("[Send CAM Single] Skipped: Another operation is already running.")
             if not is_auto: self.statusBar.showMessage("Operation already in progress.", 3000)
             return False

        self.is_operation_running = True; self.update_button_state() # Block other actions
        operation_successful = False
        display_name = f"{item_data.get('patient', 'Unknown')} [{item_data.get('base_name', '?')}]"
        print(f"[Send CAM Single] Starting for: {display_name} (is_auto={is_auto})")

        if not self.target_folder_cam:
            msg = "Target (CAM) folder is not configured."
            if not is_auto: self.show_config_error_message(msg)
            else: print(f"Auto-Send CAM skipped for {display_name}: {msg}")
            self.is_operation_running = False; self.update_button_state(); return False
        if not self.check_or_create_folder(self.target_folder_cam, "Target (CAM)"):
            msg = "Target (CAM) folder creation cancelled or failed."
            if not is_auto: QMessageBox.warning(self, "Folder Error", msg)
            else: print(f"Send CAM skipped for {display_name}: {msg}")
            self.is_operation_running = False; self.update_button_state(); return False

        info_path = item_data.get('info_path');
        cad_stl_paths = [p for p in item_data.get('cad_stl_paths', []) if p and os.path.exists(p)] # Existing paths
        info_exists = info_path and os.path.exists(info_path);
        cad_exists = bool(cad_stl_paths)

        if not info_exists or not cad_exists:
            msg = "Missing required files (at least one *cad.stl and .constructionInfo)."
            if not is_auto: QMessageBox.warning(self, "Missing Files", f"Cannot perform Send to CAM for {display_name}.\n{msg}")
            else: print(f"Send CAM skipped for {display_name}: {msg}")
            self.is_operation_running = False; self.update_button_state(); return False

        self.stop_hotkey_listener(intentional=True); self.stop_file_watcher() # Stop during copy
        archive_stats = self.trigger_archive_if_needed(self.target_folder_cam, "CAM") # Archive *before* copying

        files_to_process = ([info_path] if info_exists else []) + cad_stl_paths
        operation_stats = {"copied": 0, "skipped": 0, "errors": [], "project_name": display_name, "cancelled": False}

        if not is_auto: self.info_label.setText(f"Sending to CAM: {display_name}..."); QCoreApplication.processEvents()

        process_ok = True
        try:
            self.current_multi_duplicate_choice = self.DuplicateAction.ASK # Reset just in case

            for i, source_path in enumerate(files_to_process):
                progress_msg = f"Sending CAM ({i + 1}/{len(files_to_process)}): {os.path.basename(source_path)}..."
                if not is_auto: self.statusBar.showMessage(progress_msg, 0); QCoreApplication.processEvents()

                if not self._copy_file_to_target(source_path, self.target_folder_cam, operation_stats,
                                                 is_multi_operation=False, is_auto_operation=is_auto):
                    if operation_stats.get("cancelled", False):
                        print(f"Send to CAM cancelled by user for project {display_name}.")
                        process_ok = False; break # Stop processing this project
                    else: # Actual copy error
                        process_ok = False;
                        break

            if process_ok:
                 operation_successful = True

        except Exception as e:
            operation_stats["errors"].append({"file": "Process Error", "error": f"Unexpected error: {e}"});
            print(f"Error during single CAM copy for {display_name}: {e}")
            operation_successful = False
        finally:
            if not is_auto:
                self.update_hotkey_ui_elements(); self.statusBar.clearMessage()
                self.show_copy_summary("Send to CAM", [operation_stats], self.target_folder_cam, archive_stats=archive_stats)
            else:
                if operation_successful: print(f"Auto-Send CAM successful for {display_name}: {operation_stats['copied']} copied, {operation_stats['skipped']} skipped.")
                elif operation_stats.get("cancelled"): print(f"Auto-Send CAM cancelled for {display_name} due to duplicate handling.")
                else: print(f"Auto-Send CAM failed for {display_name}. Errors: {len(operation_stats['errors'])}. Check logs.")

            self.is_operation_running = False; self.update_button_state() # Re-enable buttons
            self.start_hotkey_listener(); self.start_file_watcher() # Restart listeners

        return operation_successful

    def send_print_for_project(self, item_data, is_auto=False):
        """Handles sending Print files (*model*.stl) for a single project.
           Uses auto-duplicate setting if is_auto=True. Returns True on success, False on failure/cancel."""
        if not isinstance(item_data, dict):
             print("[Send Print Single] Error: Invalid item_data provided.")
             return False
        if self.is_operation_running and not is_auto:
             print("[Send Print Single] Skipped: Another operation is already running.")
             if not is_auto: self.statusBar.showMessage("Operation already in progress.", 3000)
             return False

        self.is_operation_running = True; self.update_button_state()
        operation_successful = False
        display_name = f"{item_data.get('patient', 'Unknown')} [{item_data.get('base_name', '?')}]"
        print(f"[Send Print Single] Starting for: {display_name} (is_auto={is_auto})")

        if not self.target_folder_print:
            msg = "Target (Print) folder is not configured."
            if not is_auto: self.show_config_error_message(msg)
            else: print(f"Auto-Send Print skipped for {display_name}: {msg}")
            self.is_operation_running = False; self.update_button_state(); return False
        if not self.check_or_create_folder(self.target_folder_print, "Target (Print)"):
             msg = "Target (Print) folder creation cancelled or failed."
             if not is_auto: QMessageBox.warning(self, "Folder Error", msg)
             else: print(f"Send Print skipped for {display_name}: {msg}")
             self.is_operation_running = False; self.update_button_state(); return False


        model_stl_paths = [p for p in item_data.get('model_stl_paths', []) if p and os.path.exists(p)]
        if not model_stl_paths:
            msg = "No existing model files (*model*.stl) found to send to print."
            if not is_auto: QMessageBox.information(self, "No Model Files", f"{msg}\nProject: {display_name}")
            else: print(f"Send Print skipped for {display_name}: {msg}")
            self.is_operation_running = False; self.update_button_state(); return False

        self.stop_hotkey_listener(intentional=True); self.stop_file_watcher()
        archive_stats = self.trigger_archive_if_needed(self.target_folder_print, "Print")
        operation_stats = {"project_name": display_name, "copied": 0, "skipped": 0, "errors": [], "cancelled": False}

        if not is_auto: self.info_label.setText(f"Sending to Print: {display_name}..."); QCoreApplication.processEvents()

        process_ok = True
        try:
            self.current_multi_duplicate_choice = self.DuplicateAction.ASK # Reset

            for i, source_path in enumerate(model_stl_paths):
                progress_msg = f"Sending Print ({i + 1}/{len(model_stl_paths)}): {os.path.basename(source_path)}..."
                if not is_auto: self.statusBar.showMessage(progress_msg, 0); QCoreApplication.processEvents()

                if not self._copy_file_to_target(source_path, self.target_folder_print, operation_stats,
                                                 is_multi_operation=False, is_auto_operation=is_auto):
                    if operation_stats.get("cancelled", False):
                        print(f"Send to Print cancelled by user for project {display_name}.")
                        process_ok = False; break
                    else: # Copy error
                        process_ok = False;
                        break

            if process_ok:
                 operation_successful = True

        except Exception as e:
            operation_stats["errors"].append({"file": "Process Error", "error": f"Unexpected error: {e}"});
            print(f"Error during single Print copy for {display_name}: {e}")
            operation_successful = False
        finally:
            if not is_auto:
                self.update_hotkey_ui_elements(); self.statusBar.clearMessage()
                self.show_copy_summary("Send to Print", [operation_stats], self.target_folder_print, archive_stats=archive_stats)
            else:
                if operation_successful: print(f"Auto-Send Print successful for {display_name}: {operation_stats['copied']} copied, {operation_stats['skipped']} skipped.")
                elif operation_stats.get("cancelled"): print(f"Auto-Send Print cancelled for {display_name} due to duplicate handling.")
                else: print(f"Auto-Send Print failed for {display_name}. Errors: {len(operation_stats['errors'])}. Check logs.")

            self.is_operation_running = False; self.update_button_state()
            self.start_hotkey_listener(); self.start_file_watcher()

        return operation_successful


    # multi-project actions (from main window buttons)
    def process_selected_cam_info(self):
        """Handles the 'Send to CAM' button action for multiple selected rows.
           Copies ONLY *.info and ALL *cad.stl files."""
        if self.is_operation_running:
             self.statusBar.showMessage("Operation already in progress.", 3000)
             return
        selected_items = self.table_widget.selectionModel().selectedRows()
        if not selected_items:
             self.statusBar.showMessage("No projects selected.", 3000)
             return

        selected_rows_data = []
        for index in sorted([item.row() for item in selected_items]):
             item0 = self.table_widget.item(index, 0)
             if item0:
                  data = item0.data(Qt.ItemDataRole.UserRole)
                  if data: selected_rows_data.append(data)

        if not selected_rows_data:
             self.statusBar.showMessage("Could not retrieve data for selected rows.", 3000)
             return

        if not self.target_folder_cam: self.show_config_error_message("Target (CAM) folder is not configured."); return
        if not self.check_or_create_folder(self.target_folder_cam, "Target (CAM)"): return

        self.is_operation_running = True; self.update_button_state() # Block UI
        self.stop_hotkey_listener(intentional=True); self.stop_file_watcher() # Stop listeners
        archive_stats = self.trigger_archive_if_needed(self.target_folder_cam, "CAM") # Archive first
        all_operation_stats = []; skipped_projects_info = []
        self.current_multi_duplicate_choice = self.DuplicateAction.ASK # Reset choice for this operation
        operation_cancelled_globally = False
        total_projects_to_process = len(selected_rows_data)

        plural_s = "s" if total_projects_to_process != 1 else ""
        self.info_label.setText(f"Sending to CAM for {total_projects_to_process} selected project{plural_s}..."); QCoreApplication.processEvents()
        print(f"[Send CAM Multi] Starting for {total_projects_to_process} projects...")

        try:
            for idx, item_data in enumerate(selected_rows_data):
                if operation_cancelled_globally: break # Stop if user cancelled the whole batch

                current_project_num = idx + 1;
                display_name = f"{item_data.get('patient', 'Unknown')} [{item_data.get('base_name', '?')}]"
                project_folder = item_data.get('folder_path', 'N/A')
                print(f"[Send CAM Multi] Processing project {current_project_num}/{total_projects_to_process}: {display_name}")

                info_path = item_data.get('info_path');
                cad_stl_paths = [p for p in item_data.get('cad_stl_paths', []) if p and os.path.exists(p)]
                info_exists = info_path and os.path.exists(info_path);
                cad_exists = bool(cad_stl_paths)

                if not info_exists or not cad_exists:
                    reason = ("Missing .info" if not info_exists else "") + \
                             (" & " if not info_exists and not cad_exists else "") + \
                             ("Missing *cad.stl" if not cad_exists else "")
                    print(f"  Skipping {display_name}: {reason}")
                    skipped_projects_info.append({"name": display_name, "reason": reason}); continue

                files_to_process = ([info_path] if info_exists else []) + cad_stl_paths
                project_stats = {"project_name": display_name, "copied": 0, "skipped": 0, "errors": [], "cancelled": False}
                self.statusBar.showMessage(f"Sending CAM ({current_project_num}/{total_projects_to_process}): {display_name}...", 0); QCoreApplication.processEvents()

                process_ok_for_project = True
                for file_idx, source_path in enumerate(files_to_process):
                    file_progress_msg = f"Sending CAM ({current_project_num}/{total_projects_to_process}) File {file_idx+1}/{len(files_to_process)}: {os.path.basename(source_path)}"
                    self.statusBar.showMessage(file_progress_msg, 0); QCoreApplication.processEvents()

                    if not self._copy_file_to_target(source_path, self.target_folder_cam, project_stats,
                                                     is_multi_operation=True, is_auto_operation=False):
                        if project_stats.get("cancelled", False):
                            operation_cancelled_globally = True
                            print(f"Multi-Send CAM cancelled globally by user at project {display_name}.")
                            process_ok_for_project = False; break # Stop processing this project and the entire batch
                        else: # Actual copy error
                            process_ok_for_project = False;
                            print(f"  Error copying file {os.path.basename(source_path)} for {display_name}. Stopping this project.")
                            break # Stop processing files for *this* project on error

                if not (operation_cancelled_globally and project_stats.get("cancelled", False)):
                     all_operation_stats.append(project_stats)


        except Exception as e:
             err_msg = f"Unexpected error during Multi Send to CAM: {e}"
             print(err_msg)
             all_operation_stats.append({"project_name": "Multi Send Error", "copied": 0, "skipped": 0, "errors": [{"file": "Process Error", "error": err_msg}]})
             operation_cancelled_globally = True # Treat as cancelled to be safe

        finally:
            print(f"[Send CAM Multi] Finished processing {total_projects_to_process} projects.")
            self.update_hotkey_ui_elements(); self.statusBar.clearMessage()
            self.show_copy_summary("Multi Send to CAM", all_operation_stats, self.target_folder_cam, skipped_projects_info, archive_stats, operation_cancelled_globally)
            self.is_operation_running = False; self.update_button_state() # Re-enable UI
            self.start_hotkey_listener(); self.start_file_watcher() # Restart listeners


    def process_selected_print_files(self):
        """Handles the 'Send to Print' button action for multiple selected rows.
           Copies ONLY *model*.stl files."""
        if self.is_operation_running:
             self.statusBar.showMessage("Operation already in progress.", 3000)
             return
        selected_items = self.table_widget.selectionModel().selectedRows()
        if not selected_items:
             self.statusBar.showMessage("No projects selected.", 3000)
             return

        selected_rows_data = []
        for index in sorted([item.row() for item in selected_items]):
             item0 = self.table_widget.item(index, 0)
             if item0:
                  data = item0.data(Qt.ItemDataRole.UserRole)
                  if data: selected_rows_data.append(data)

        if not selected_rows_data:
             self.statusBar.showMessage("Could not retrieve data for selected rows.", 3000)
             return

        if not self.target_folder_print: self.show_config_error_message("Target (Print) folder is not configured."); return
        if not self.check_or_create_folder(self.target_folder_print, "Target (Print)"): return

        self.is_operation_running = True; self.update_button_state()
        self.stop_hotkey_listener(intentional=True); self.stop_file_watcher()
        archive_stats = self.trigger_archive_if_needed(self.target_folder_print, "Print")
        all_operation_stats = []; skipped_projects_info = []
        self.current_multi_duplicate_choice = self.DuplicateAction.ASK
        operation_cancelled_globally = False
        total_projects_to_process = len(selected_rows_data)

        plural_s = "s" if total_projects_to_process != 1 else ""
        self.info_label.setText(f"Sending to Print for {total_projects_to_process} selected project{plural_s}..."); QCoreApplication.processEvents()
        print(f"[Send Print Multi] Starting for {total_projects_to_process} projects...")

        try:
            for idx, item_data in enumerate(selected_rows_data):
                if operation_cancelled_globally: break

                current_project_num = idx + 1;
                display_name = f"{item_data.get('patient', 'Unknown')} [{item_data.get('base_name', '?')}]"
                print(f"[Send Print Multi] Processing project {current_project_num}/{total_projects_to_process}: {display_name}")

                model_stl_paths = [p for p in item_data.get('model_stl_paths', []) if p and os.path.exists(p)]
                if not model_stl_paths:
                    reason = "No model files (*model*.stl) found"
                    print(f"  Skipping {display_name}: {reason}")
                    skipped_projects_info.append({"name": display_name, "reason": reason}); continue

                files_to_process = model_stl_paths
                project_stats = {"project_name": display_name, "copied": 0, "skipped": 0, "errors": [], "cancelled": False}
                self.statusBar.showMessage(f"Sending Print ({current_project_num}/{total_projects_to_process}): {display_name}...", 0); QCoreApplication.processEvents()

                process_ok_for_project = True
                for file_idx, source_path in enumerate(files_to_process):
                    file_progress_msg = f"Sending Print ({current_project_num}/{total_projects_to_process}) File {file_idx+1}/{len(files_to_process)}: {os.path.basename(source_path)}"
                    self.statusBar.showMessage(file_progress_msg, 0); QCoreApplication.processEvents()

                    if not self._copy_file_to_target(source_path, self.target_folder_print, project_stats,
                                                     is_multi_operation=True, is_auto_operation=False):
                        if project_stats.get("cancelled", False):
                            operation_cancelled_globally = True
                            print(f"Multi-Send Print cancelled globally by user at project {display_name}.")
                            process_ok_for_project = False; break
                        else: # Copy error
                            process_ok_for_project = False;
                            print(f"  Error copying file {os.path.basename(source_path)} for {display_name}. Stopping this project.")
                            break # Stop this project on error

                if not (operation_cancelled_globally and project_stats.get("cancelled", False)):
                     all_operation_stats.append(project_stats)

        except Exception as e:
            err_msg = f"Unexpected error during Multi Send to Print: {e}"
            print(err_msg)
            all_operation_stats.append({"project_name": "Multi Send Error", "copied": 0, "skipped": 0, "errors": [{"file": "Process Error", "error": err_msg}]})
            operation_cancelled_globally = True

        finally:
            print(f"[Send Print Multi] Finished processing {total_projects_to_process} projects.")
            self.update_hotkey_ui_elements(); self.statusBar.clearMessage()
            self.show_copy_summary("Multi Send to Print", all_operation_stats, self.target_folder_print, skipped_projects_info, archive_stats, operation_cancelled_globally)
            self.is_operation_running = False; self.update_button_state()
            self.start_hotkey_listener(); self.start_file_watcher()


    def open_folder_in_explorer(self, folder_path):
        """Opens the specified folder path in the default file explorer."""
        if not folder_path:
             QMessageBox.warning(self, "Error", "Folder path is not set.")
             return
        norm_path = os.path.normpath(folder_path)
        if not os.path.isdir(norm_path):
             QMessageBox.warning(self, "Error", f"Cannot open folder path:\n{norm_path}\nIt might not exist or is invalid.")
             return

        try:
            url_string = QUrl.fromLocalFile(norm_path).toString()
            if sys.platform == 'win32' and not url_string.startswith('file:///'):
                 url_string = 'file:///' + url_string.lstrip('file:/')

            url = QUrl(url_string)

            print(f"Attempting to open folder: {norm_path} (URL: {url.toString()})")
            if not QDesktopServices.openUrl(url):
                print(f"QDesktopServices.openUrl failed for {norm_path}. Trying OS-specific fallback...")
                try:
                    if sys.platform == 'win32':
                        os.startfile(norm_path)
                    elif sys.platform == 'darwin': # macOS
                        os.system(f'open "{norm_path}"')
                    else: # Linux/other POSIX
                        os.system(f'xdg-open "{norm_path}"')
                except Exception as e_fallback:
                     print(f"OS-specific fallback failed: {e_fallback}")
                     QMessageBox.warning(self, "Error", f"Could not open the folder using system commands:\n{e_fallback}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred while trying to open the folder:\n{e}")

    def copy_to_clipboard(self, text):
        """Copies the given text to the system clipboard."""
        try:
            clipboard = QGuiApplication.clipboard();
            if clipboard:
                clipboard.setText(text);
                display_text = text.replace('\n', ' ').replace('\r', '') # Make it single line for status bar
                self.statusBar.showMessage(f"Copied: {display_text[:50]}{'...' if len(display_text)>50 else ''}", 3000)
            else:
                self.statusBar.showMessage("Error: Could not access clipboard.", 3000)
        except Exception as e:
            self.statusBar.showMessage(f"Clipboard Error: {e}", 3000)

    def update_button_state(self):
        """Enables/disables main action buttons based on selection, config, AND operation status."""
        has_selection = self.table_widget.selectionModel().hasSelection()
        config_ok_for_scan = bool(self.watch_folder and os.path.isdir(self.watch_folder))
        config_ok_for_cam_send = bool(self.target_folder_cam) # Target existence checked later
        config_ok_for_print_send = bool(self.target_folder_print) # Target existence checked later

        can_scan = config_ok_for_scan and not self.is_operation_running
        can_send_cam = has_selection and config_ok_for_cam_send and not self.is_operation_running
        can_send_print = has_selection and config_ok_for_print_send and not self.is_operation_running
        can_open_settings = not self.is_operation_running
        can_open_cam_target_btn = config_ok_for_cam_send and not self.is_operation_running
        can_open_print_target_btn = config_ok_for_print_send and not self.is_operation_running

        if hasattr(self, 'scan_button'):
            self.scan_button.setEnabled(can_scan)
            tooltip = ""
            if self.is_operation_running: tooltip = "Cannot Scan: Operation in progress."
            elif not config_ok_for_scan: tooltip = "Cannot Scan: Watch folder not configured correctly."
            else:
                hotkey_upper = self.hotkey_combo.upper() if KEYBOARD_AVAILABLE else "N/A"
                tooltip = (f"Scan Watch Folder ({hotkey_upper})" if KEYBOARD_AVAILABLE else "Scan Watch Folder (Hotkey disabled)")
            self.scan_button.setToolTip(tooltip)

        if hasattr(self, 'send_cam_button'):
            self.send_cam_button.setEnabled(can_send_cam)
            tooltip = ""
            if self.is_operation_running: tooltip = "Cannot Send: Another operation is in progress."
            elif not config_ok_for_cam_send: tooltip = "Cannot Send: Target (CAM) folder not configured."
            elif not has_selection: tooltip = "Select one or more rows to enable Send to CAM."
            else:
                tooltip = f"Copy selected projects' CAM files (*.info, ALL *cad.stl) to:\n{shorten_path(self.target_folder_cam)}"
                if self.archive_enabled: tooltip += "\n(Will archive old files if enabled)"
                tooltip += f"\n(Manual duplicate action: {self.duplicate_check_action_setting.capitalize()})"
            self.send_cam_button.setToolTip(tooltip)

        if hasattr(self, 'send_print_button'):
            self.send_print_button.setEnabled(can_send_print)
            tooltip = ""
            if self.is_operation_running: tooltip = "Cannot Send: Another operation is in progress."
            elif not config_ok_for_print_send: tooltip = "Cannot Send: Target (Print) folder not configured."
            elif not has_selection: tooltip = "Select one or more rows to enable Send to Print."
            else:
                tooltip = f"Copy selected projects' Print files (*model*.stl) to:\n{shorten_path(self.target_folder_print)}"
                if self.archive_enabled: tooltip += "\n(Will archive old files if enabled)"
                tooltip += f"\n(Manual duplicate action: {self.duplicate_check_action_setting.capitalize()})"
            self.send_print_button.setToolTip(tooltip)

        if hasattr(self, 'open_cam_folder_button'):
            self.open_cam_folder_button.setEnabled(can_open_cam_target_btn)
            tooltip = ""
            if self.is_operation_running: tooltip = "Cannot open: Operation in progress."
            elif not config_ok_for_cam_send: tooltip = "Target (CAM) folder not set."
            else: tooltip = f"Open Target Folder (CAM):\n{self.target_folder_cam}"
            self.open_cam_folder_button.setToolTip(tooltip)

        if hasattr(self, 'open_print_folder_button'):
            self.open_print_folder_button.setEnabled(can_open_print_target_btn)
            tooltip = ""
            if self.is_operation_running: tooltip = "Cannot open: Operation in progress."
            elif not config_ok_for_print_send: tooltip = "Target (Print) folder not set."
            else: tooltip = f"Open Target Folder (Print):\n{self.target_folder_print}"
            self.open_print_folder_button.setToolTip(tooltip)

        if hasattr(self, 'settings_button'):
            self.settings_button.setEnabled(can_open_settings)
            self.settings_button.setToolTip("Open Settings" if can_open_settings else "Cannot open Settings: Operation in progress.")


    def check_or_create_folder(self, folder_path, folder_desc):
        """Checks if a folder exists. If not, asks user if they want to create it. Returns True if folder exists or was created, False otherwise."""
        if os.path.isdir(folder_path): return True

        reply = QMessageBox.question(self, f"Create {folder_desc} Folder?",
                                     f"The {folder_desc} folder does not exist:\n{folder_path}\n\nCreate it now?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.Yes) # Default to Yes

        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.makedirs(folder_path, exist_ok=True) # exist_ok=True is safe
                print(f"Created folder: {folder_path}")
                self.statusBar.showMessage(f"Created folder: {shorten_path(folder_path)}", 3000)
                return True
            except OSError as e:
                QMessageBox.critical(self, "Error Creating Folder", f"Could not create {folder_desc} folder:\n{e}");
                print(f"Error creating folder {folder_path}: {e}")
                return False
        else:
            print(f"User cancelled creation of {folder_desc} folder: {folder_path}")
            return False


    def show_config_error_message(self, message):
        """Shows a standardized error message box for configuration issues."""
        msgBox = QMessageBox(self);
        msgBox.setIcon(QMessageBox.Icon.Critical);
        msgBox.setWindowTitle("Configuration Error")
        msgBox.setText(message);
        msgBox.setInformativeText("Please check folder paths in Settings (⚙️).")
        msgBox.setStandardButtons(QMessageBox.StandardButton.Ok);
        msgBox.setStyleSheet(NEON_VOID_STYLE); # Apply style
        msgBox.exec()

    # show copy summary message box
    def show_copy_summary(self, operation_name, copy_results_list, target_folder_path, skipped_list=None,
                          archive_stats=None, operation_cancelled=False):
        """Displays a summary message box after copy/archive operations."""
        if skipped_list is None: skipped_list = []
        if archive_stats is None: archive_stats = {"moved": 0, "errors": 0}

        total_copied = sum(r.get("copied", 0) for r in copy_results_list)
        total_files_skipped_duplicate = sum(r.get("skipped", 0) for r in copy_results_list)
        total_copy_errors = sum(len(r.get("errors", [])) for r in copy_results_list)
        total_projects_processed = len(copy_results_list) # Number of projects attempted
        total_projects_with_copy_errors = sum(1 for r in copy_results_list if r.get("errors"))
        total_projects_skipped_config = len(skipped_list) # Projects skipped *before* copy attempt
        total_projects_cancelled_explicitly = sum(1 for r in copy_results_list if r.get("cancelled", False))

        total_archived = archive_stats.get("moved", 0)
        total_archive_errors = archive_stats.get("errors", 0)

        title = f"{operation_name} Result"; icon = QMessageBox.Icon.Information
        summary_lines = []

        if operation_cancelled:
             icon = QMessageBox.Icon.Warning; title = f"{operation_name} Cancelled"
             summary_lines.append(f"<b style='color:#FFD700;'>Operation cancelled by user.</b>"); summary_lines.append("")
        elif total_copy_errors > 0 or total_archive_errors > 0:
             icon = QMessageBox.Icon.Warning; title = f"{operation_name} Completed with Errors"
        elif total_projects_skipped_config > 0 or total_projects_cancelled_explicitly > 0 or total_files_skipped_duplicate > 0:
             icon = QMessageBox.Icon.Warning; title = f"{operation_name} Completed with Skips/Cancellations"
        elif total_copied == 0 and total_archived == 0 and total_projects_processed == 0 and total_projects_skipped_config == 0 and not operation_cancelled:
             icon = QMessageBox.Icon.Information; title = f"{operation_name}: No Action";
             summary_lines.append("No eligible projects selected or no files needed action.")


        if self.archive_enabled and (total_archived > 0 or total_archive_errors > 0):
            archive_line = f"Archiving: <b style='color:#00E5E5;'>Moved {total_archived} old file{'s' if total_archived != 1 else ''}</b>"
            if total_archive_errors > 0:
                 archive_line += f" <b style='color:#FF4D4D;'>({total_archive_errors} error{'s' if total_archive_errors != 1 else ''})</b>."
            else:
                 archive_line += "."
            summary_lines.append(archive_line)
            if target_folder_path and total_archived > 0:
                summary_lines.append(f"into date folders within: {shorten_path(target_folder_path, 3)}")
            summary_lines.append("")

        processed_ok_count = sum(1 for r in copy_results_list if not r.get("errors") and not r.get("cancelled", False))
        if total_copied > 0:
            summary_lines.append(f"<b style='color:#00FF7F;'>Copied {total_copied} file{'s' if total_copied != 1 else ''}</b> across {processed_ok_count} project{'s' if processed_ok_count != 1 else ''}.")
            if target_folder_path: summary_lines.append(f"Target: {shorten_path(target_folder_path, 3)}")
            summary_lines.append("")

        if total_files_skipped_duplicate > 0:
            summary_lines.append(f"<b style='color:#FFD700;'>Skipped {total_files_skipped_duplicate} duplicate file{'s' if total_files_skipped_duplicate != 1 else ''}</b> based on user choice or settings.")
            summary_lines.append("")

        if skipped_list:
            summary_lines.append(f"<b style='color:#FFD700;'>Skipped {len(skipped_list)} project{'s' if len(skipped_list) != 1 else ''}</b> (Missing files/config):")
            for i, skip_info in enumerate(skipped_list):
                if i < 5: summary_lines.append(f"- {skip_info['name']} ({skip_info['reason']})")
                elif i == 5: summary_lines.append("- ... (and others)"); break
            summary_lines.append("")

        if total_projects_cancelled_explicitly > 0 and not operation_cancelled: # Don't show if whole op cancelled
             summary_lines.append(f"<b style='color:#FFD700;'>Cancelled processing for {total_projects_cancelled_explicitly} project{'s' if total_projects_cancelled_explicitly != 1 else ''}</b> due to user choice.")
             for i, result in enumerate(r for r in copy_results_list if r.get("cancelled")):
                  if i < 5: summary_lines.append(f"- {result.get('project_name', 'Unknown')}")
                  elif i == 5: summary_lines.append("- ... (and others)"); break
             summary_lines.append("")


        if total_copy_errors > 0:
            summary_lines.append(f"<b style='color:#FF4D4D;'>Encountered {total_copy_errors} copy error{'s' if total_copy_errors != 1 else ''} across {total_projects_with_copy_errors} project{'s' if total_projects_with_copy_errors != 1 else ''}:</b>")
            error_count_display = 0
            for result in copy_results_list:
                if result.get("errors"):
                    proj_name = result.get("project_name", "Unknown Project")
                    for err_info in result["errors"]:
                        if error_count_display < 8:
                            file_info = f" (File: {err_info.get('file')})" if err_info.get('file') not in ["Process Error", "N/A"] else ""
                            err_text = err_info.get('error', 'N/A')
                            if len(err_text) > 100: err_text = err_text[:100] + "..."
                            summary_lines.append(f"- {proj_name}{file_info}: {err_text}")
                            error_count_display += 1
                        elif error_count_display == 8: summary_lines.append("- ... (more copy errors)"); error_count_display += 1; break
                    if error_count_display > 8: break
            summary_lines.append("")

        if total_archive_errors > 0 and not any("archive" in line.lower() and "error" in line.lower() for line in summary_lines):
            summary_lines.append(f"<b style='color:#FF4D4D;'>Note: {total_archive_errors} archive error{'s' if total_archive_errors != 1 else ''} occurred. Check logs.</b>"); summary_lines.append("")


        has_content = any(line.strip() and "No eligible projects" not in line for line in summary_lines)

        if has_content or icon != QMessageBox.Icon.Information:
            msg_box = QMessageBox(icon, title, "<br>".join(summary_lines).strip().replace("\n", "<br>"), QMessageBox.StandardButton.Ok, self)
            msg_box.setStyleSheet(NEON_VOID_STYLE); # Apply style
            msg_box.exec()

        if total_copy_errors == 0 and \
           total_projects_skipped_config == 0 and \
           total_files_skipped_duplicate == 0 and \
           total_archive_errors == 0 and \
           not operation_cancelled and \
           total_projects_cancelled_explicitly == 0 and \
           (total_copied > 0 or total_archived > 0): # Only clear if something was actually done
            self.table_widget.clearSelection()


    def handle_retry_click(self): # placeholder
        QMessageBox.information(self, "Retry Failed", "Automatic retry is not yet implemented.\nPlease re-select projects/files and try the operation again.", QMessageBox.StandardButton.Ok)
        self.last_failed_items = []

    # controlling the hotkey listener thread
    def start_hotkey_listener(self, force_restart=False):
        """Starts the background thread to listen for the global hotkey."""
        if not KEYBOARD_AVAILABLE:
            return
        if self.is_operation_running:
             return

        self.is_listener_intentionally_stopped = False # Assume we want it running now

        if self.listener_thread and self.listener_thread.is_alive():
            if force_restart:
                print("[Hotkey] Forcing restart of listener...")
                self.stop_hotkey_listener(intentional=False) # Stop temporarily
            else:
                return # Already running and no force restart

        if self.listener_thread and not self.listener_thread.is_alive():
             print("[Hotkey] Cleaning up dead listener thread reference.")
             self.listener_thread = None

        if not self.listener_thread:
            if not self.hotkey_combo:
                 print("[Hotkey] Listener not started: Hotkey combo is empty in settings.")
                 return

            print(f"[Hotkey] Starting listener thread for: {self.hotkey_combo}")
            try:
                self.listener_thread = HotkeyListener(self.hotkey_combo, self.hotkey_signal_emitter)
                self.listener_thread.start()
                print("[Hotkey] Listener thread started.")
            except ValueError as ve: # Catch specific hotkey parsing errors
                QMessageBox.critical(self, "Hotkey Error", f"Invalid hotkey format: '{self.hotkey_combo}'\n{ve}\n\nPlease change it in Settings.");
                self.listener_thread = None; print(f"[Hotkey] Listener start failed (ValueError): {ve}")
            except Exception as e: # Catch other errors (permissions etc)
                info_text = "\nCheck hotkey format & ensure no other app uses it.";
                if any(s in str(e).lower() for s in ["permission", "administrator", "root", "access denied", "sudo"]):
                     info_text += "\nThis often requires administrator/root privileges."
                QMessageBox.critical(self, "Hotkey Error", f"Failed to start listener for '{self.hotkey_combo}':\n{e}{info_text}");
                self.listener_thread = None; print(f"[Hotkey] Listener start failed (Exception): {e}")
        self.update_status_bar()


    def stop_hotkey_listener(self, intentional=True):
        """Stops the hotkey listener thread."""
        if intentional:
             self.is_listener_intentionally_stopped = True
             print("[Hotkey] Listener stop requested intentionally.")

        listener_was_running = self.listener_thread and self.listener_thread.is_alive()
        if listener_was_running:
            print(f"[Hotkey] Stopping listener thread ({self.hotkey_combo})...")
            try:
                self.listener_thread.stop(); # Calls stop() method in HotkeyListener class
                self.listener_thread.join(timeout=0.5); # Wait briefly for thread to exit
                if self.listener_thread.is_alive():
                     print("[Hotkey] Warning: Listener thread did not exit cleanly after stop request.")
                else: print("[Hotkey] Listener thread stopped.")
            except Exception as e: print(f"[Hotkey] Error stopping listener thread: {e}")
            finally: self.listener_thread = None # Clear reference regardless
        elif self.listener_thread: # Thread object exists but not alive
             self.listener_thread = None # Clear reference

        self.update_status_bar()


    # control the file system watcher thread
    def start_file_watcher(self):
        """Starts the watchdog file system observer thread if needed and configured."""
        should_start = WATCHDOG_AVAILABLE and (self.live_notify_enabled or self.auto_send_enabled)

        if not should_start:
            self.stop_file_watcher()
            return

        if self.fs_observer and self.fs_observer.is_alive():
            return
        if self.fs_observer and not self.fs_observer.is_alive():
             print("[Watcher] Cleaning up dead watcher observer reference.")
             self.fs_observer = None
             self.fs_event_handler = None


        if not self.watch_folder or not os.path.isdir(self.watch_folder):
            print(f"[Watcher] Not started: Watch folder is not set or invalid ('{self.watch_folder}').")
            return

        if not self.fs_observer:
            try:
                enabled_features = []
                if self.live_notify_enabled: enabled_features.append(f"Notifications({self.notify_debounce_secs}s)")
                if self.auto_send_enabled: enabled_features.append("Auto-Send")
                print(f"[Watcher] Starting file system watcher ({', '.join(enabled_features)}): {self.watch_folder}")

                self.fs_event_handler = WatcherEventHandler(self.watchdog_signal_emitter, self.watch_folder)
                self.fs_observer = Observer()
                self.fs_observer.schedule(self.fs_event_handler, self.watch_folder, recursive=True)
                self.fs_observer.start()
                if self.fs_observer.is_alive():
                     print("[Watcher] File system watcher started successfully.")
                else:
                    print("[Watcher] Error: File system watcher thread failed to start.")
                    self.fs_observer = None # Clear if failed to start
                    self.fs_event_handler = None
                    QMessageBox.critical(self, "Watcher Error", f"Failed to start file system watcher thread for:\n{self.watch_folder}")

            except Exception as e:
                 QMessageBox.critical(self, "Watcher Error", f"Failed to start file system watcher for '{self.watch_folder}':\n{e}")
                 print(f"Error starting file watcher: {e}")
                 self.fs_observer = None; self.fs_event_handler = None
            finally:
                 self.update_status_bar() # Update status regardless of success/failure


    def stop_file_watcher(self):
        """Stops the watchdog file system observer thread."""
        observer_was_running = self.fs_observer and self.fs_observer.is_alive()
        if observer_was_running:
            print("[Watcher] Stopping file system watcher...")
            try:
                self.fs_observer.stop(); # Request stop
                self.fs_observer.join(timeout=1.0) # Wait for thread to finish
                if self.fs_observer.is_alive():
                    print("[Watcher] Warning: File watcher thread did not stop gracefully after join.")
                else:
                    print("[Watcher] File system watcher stopped.")
            except Exception as e: print(f"[Watcher] Error stopping file watcher: {e}")
            finally:
                 self.fs_observer = None; self.fs_event_handler = None;
        elif self.fs_observer: # Observer object exists but not alive
             self.fs_observer = None; self.fs_event_handler = None;

        self.update_status_bar()


    # application exit handling
    def closeEvent(self, event):
        """Overrides the window close button (X) to hide to tray instead of quitting."""
        if self.is_operation_running:
            QMessageBox.warning(self, "Operation in Progress", "Cannot close or hide while an operation (scan/copy) is running.")
            event.ignore() # Prevent closing
        else:
            if self.active_notification_dialog and self.active_notification_dialog.isVisible():
                print("[Close Event] Closing active notification dialog.")
                try: self.active_notification_dialog.reject(); self.active_notification_dialog = None
                except Exception: pass
            if self.current_stl_viewer and self.current_stl_viewer.isVisible():
                 print("[Close Event] Closing active STL viewer.")
                 try: self.current_stl_viewer.close(); # Should trigger _handle_viewer_closed
                 except Exception: pass

            if self.tray_icon and self.tray_icon.isVisible():
                print("[Close Event] Hiding window to tray.")
                self.hide_to_tray()
                self.tray_icon.showMessage(APP_NAME, "Application is running in the background.", QSystemTrayIcon.MessageIcon.Information, 2000)
                event.ignore() # Prevent actual closing
            else:
                print("[Close Event] No tray icon, quitting application.")
                event.accept() # Allow closing -> triggers quit_application via aboutToQuit signal
                self.quit_application()


    def quit_application(self):
        """Handles the actual application quit process (from menu, tray, or closeEvent fallback)."""
        print("Quit application requested...")
        if self.is_operation_running:
            reply = QMessageBox.question(self, "Operation in Progress",
                                         "An operation (scan/copy) is currently running.\nAre you sure you want to quit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                print("Quit cancelled by user (operation running).")
                return # Don't quit

        print("Proceeding with application quit.")
        self.save_auto_send_status()
        self.stop_hotkey_listener(intentional=True)
        self.stop_file_watcher()
        if self.active_notification_dialog:
            try: print("Closing notification dialog on quit..."); self.active_notification_dialog.reject()
            except Exception as e: print(f"Error closing notification dialog on quit: {e}")
        if self.current_stl_viewer and self.current_stl_viewer.isVisible():
            try: print("Closing STL viewer on quit..."); self.current_stl_viewer.close()
            except Exception as e: print(f"Error closing STL viewer on quit: {e}")
        if self.tray_icon:
             print("Hiding tray icon..."); self.tray_icon.hide()

        print("Quitting QApplication instance...")
        app_instance = QApplication.instance()
        if app_instance:
             app_instance.quit()
        else: # Should not happen if run normally
             sys.exit(0)
