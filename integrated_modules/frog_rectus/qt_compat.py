"""Small Qt binding compatibility layer.

The normal Windows 10 and 11 source setup uses PySide6.  Windows 7 needs a
Python and Qt combination which still supports that operating system, so the
same source can fall back to PySide2 (Qt 5.15).  The rest of this project uses
only APIs shared by Qt 5 and Qt 6.
"""

import os
import sys


try:  # Preferred on supported current Windows versions.
    from PySide6 import QtCore, QtGui, QtWidgets
    QT_BINDING = "PySide6"
except ImportError:  # Windows 7 source installation: Python 3.8 + PySide2.
    from PySide2 import QtCore, QtGui, QtWidgets
    QT_BINDING = "PySide2"

    # Older modules in this application still import the PySide6 namespace.
    # Registering these aliases lets them use the selected Qt 5 binding without
    # duplicating a try/except block in every file.
    sys.modules.setdefault("PySide6", sys.modules["PySide2"])
    sys.modules.setdefault("PySide6.QtCore", QtCore)
    sys.modules.setdefault("PySide6.QtGui", QtGui)
    sys.modules.setdefault("PySide6.QtWidgets", QtWidgets)


Signal = QtCore.Signal
Qt = QtCore.Qt
QRectF = QtCore.QRectF
QPointF = QtCore.QPointF
QTimer = QtCore.QTimer
QSize = QtCore.QSize

QPainter = QtGui.QPainter
QPen = QtGui.QPen
QBrush = QtGui.QBrush
QColor = QtGui.QColor
QLinearGradient = QtGui.QLinearGradient
QFont = QtGui.QFont
QFontDatabase = QtGui.QFontDatabase
QPainterPath = QtGui.QPainterPath
QImage = QtGui.QImage
QDoubleValidator = QtGui.QDoubleValidator
QIcon = QtGui.QIcon

QApplication = QtWidgets.QApplication
QMainWindow = QtWidgets.QMainWindow
QStackedWidget = QtWidgets.QStackedWidget
QMessageBox = QtWidgets.QMessageBox
QScrollArea = QtWidgets.QScrollArea
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QGridLayout = QtWidgets.QGridLayout
QPushButton = QtWidgets.QPushButton
QLabel = QtWidgets.QLabel
QSizePolicy = QtWidgets.QSizePolicy
QFrame = QtWidgets.QFrame
QGroupBox = QtWidgets.QGroupBox
QComboBox = QtWidgets.QComboBox
QSplitter = QtWidgets.QSplitter
QTextEdit = QtWidgets.QTextEdit
QLineEdit = QtWidgets.QLineEdit
QFileDialog = QtWidgets.QFileDialog
QCheckBox = QtWidgets.QCheckBox
QTableWidget = QtWidgets.QTableWidget
QTableWidgetItem = QtWidgets.QTableWidgetItem
QHeaderView = QtWidgets.QHeaderView
QAbstractItemView = QtWidgets.QAbstractItemView
QTabWidget = QtWidgets.QTabWidget
QListWidget = QtWidgets.QListWidget
QTextBrowser = QtWidgets.QTextBrowser
QListWidgetItem = QtWidgets.QListWidgetItem
QSlider = QtWidgets.QSlider
QDoubleSpinBox = QtWidgets.QDoubleSpinBox


def ensure_application_font():
    """Register a Windows UI font if Qt reports an empty font database."""
    try:
        families = list(QFontDatabase.families())
    except TypeError:
        families = list(QFontDatabase().families())
    if families:
        return families[0]

    windows_root = (
        os.environ.get("SystemRoot")
        or os.environ.get("WINDIR")
        or r"C:\Windows"
    )
    for filename in ("segoeui.ttf", "arial.ttf", "tahoma.ttf"):
        path = os.path.join(windows_root, "Fonts", filename)
        if not os.path.isfile(path):
            continue
        font_id = QFontDatabase.addApplicationFont(path)
        if font_id >= 0:
            registered = QFontDatabase.applicationFontFamilies(font_id)
            if registered:
                return registered[0]
    return ""


def app_exec(app):
    """Run the Qt event loop with the spelling supported by the binding."""
    if hasattr(app, "exec"):
        return app.exec()
    return app.exec_()
