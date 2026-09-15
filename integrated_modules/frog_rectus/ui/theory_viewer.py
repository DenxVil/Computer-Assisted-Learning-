"""Responsive browser for theory and four practical settings."""

from ..qt_compat import (
    Signal, Qt, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextBrowser, QPushButton, QLabel, QSplitter, QListWidgetItem,
)
from ..theory import get_theory_titles, get_theory_content
from .style import (
    PRIMARY, BG_CARD, BORDER, INSTITUTION_TEXT, INSTITUTION_LABEL_STYLE,
)


class TheoryViewer(QWidget):
    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        back_button = QPushButton("Back to home")
        back_button.setProperty("secondary", True)
        back_button.setMaximumWidth(150)
        back_button.clicked.connect(self.go_back.emit)
        top.addWidget(back_button)
        title = QLabel("Theory and Practical Guidance")
        title.setProperty("heading", True)
        title.setWordWrap(True)
        top.addWidget(title, 1)
        institution = QLabel(INSTITUTION_TEXT)
        institution.setStyleSheet(INSTITUTION_LABEL_STYLE)
        institution.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(institution)
        layout.addLayout(top)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.topic_list = QListWidget()
        self.topic_list.setMinimumWidth(210)
        self.topic_list.setMaximumWidth(300)
        self.topic_list.setStyleSheet(f"""
            QListWidget {{
                background: {BG_CARD}; border: 1px solid {BORDER};
                border-radius: 8px; padding: 7px; font-size: 12px;
            }}
            QListWidget::item {{
                padding: 10px 7px; border-radius: 6px; margin: 2px 0;
            }}
            QListWidget::item:selected {{ background: {PRIMARY}; color: white; }}
            QListWidget::item:hover {{ background: #E3F2FD; }}
        """)
        for index, title_text in enumerate(get_theory_titles(), 1):
            self.topic_list.addItem(QListWidgetItem(f"{index}. {title_text}"))
        self.topic_list.currentRowChanged.connect(self.show_topic)
        self.splitter.addWidget(self.topic_list)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                background: white; border: 1px solid {BORDER};
                border-radius: 8px; padding: 18px; font-size: 14px;
            }}
        """)
        self.splitter.addWidget(self.browser)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setSizes([260, 900])
        layout.addWidget(self.splitter, 1)

        if self.topic_list.count():
            self.topic_list.setCurrentRow(0)

    def show_topic(self, index):
        self.browser.setHtml(get_theory_content(index))
        self.browser.verticalScrollBar().setValue(0)

    def resizeEvent(self, event):
        compact = self.width() < 760
        orientation = Qt.Vertical if compact else Qt.Horizontal
        if self.splitter.orientation() != orientation:
            self.splitter.setOrientation(orientation)
            if compact:
                self.setMinimumHeight(850)
                self.topic_list.setMinimumWidth(0)
                self.topic_list.setMaximumWidth(16777215)
                self.topic_list.setMaximumHeight(245)
                self.splitter.setSizes([230, 620])
            else:
                self.setMinimumHeight(0)
                self.topic_list.setMinimumWidth(210)
                self.topic_list.setMaximumWidth(300)
                self.topic_list.setMaximumHeight(16777215)
                self.splitter.setSizes([260, 900])
        super().resizeEvent(event)
