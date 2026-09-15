from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

import cleaner


class CleanPreviewDialog(QDialog):
    def __init__(self, result: cleaner.ScanResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.permanent = False
        self.selected_items: list[cleaner.FileItem] = []

        self.setWindowTitle(f"清理预览 - {result.title}")
        self.setMinimumSize(680, 480)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(self)

        header = QLabel(
            f"<b>{result.title}</b>：共扫描到 {result.count} 个文件，"
            f"合计 <b>{cleaner.human_size(result.total_size)}</b>"
        )
        layout.addWidget(header)

        if result.note:
            note = QLabel(result.note)
            note.setWordWrap(True)
            note.setStyleSheet("color: #777;")
            layout.addWidget(note)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["选择", "文件", "大小"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        for item in result.items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Unchecked)
            check.setData(Qt.ItemDataRole.UserRole, item)
            self.table.setItem(row, 0, check)

            name = QTableWidgetItem(item.path.name)
            name.setToolTip(str(item.path))
            self.table.setItem(row, 1, name)

            size = QTableWidgetItem(cleaner.human_size(item.size))
            size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, size)

        self.table.itemChanged.connect(self._update_total)

        controls = QHBoxLayout()
        select_all = QPushButton("全选")
        select_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        select_none = QPushButton("全不选")
        select_none.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        controls.addWidget(select_all)
        controls.addWidget(select_none)
        controls.addStretch(1)

        self.total_label = QLabel()
        font = QFont()
        font.setBold(True)
        self.total_label.setFont(font)
        controls.addWidget(self.total_label)
        layout.addLayout(controls)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        if cleaner.HAS_TRASH and not result.permanent_only:
            trash_btn = QPushButton("移到回收站")
            trash_btn.clicked.connect(lambda: self._accept(False))
            buttons.addWidget(trash_btn)
        permanent_btn = QPushButton("永久删除")
        permanent_btn.clicked.connect(lambda: self._accept(True))
        buttons.addWidget(permanent_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self._update_total()

    def _set_all(self, state):
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(state)
        self.table.blockSignals(False)
        self._update_total()

    def _update_total(self, *_):
        total = 0
        count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                total += data.size
                count += 1
        self.total_label.setText(f"已选 {count} 项，共 {cleaner.human_size(total)}")

    def _accept(self, permanent: bool):
        items = []
        for row in range(self.table.rowCount()):
            cell = self.table.item(row, 0)
            if cell.checkState() == Qt.CheckState.Checked:
                items.append(cell.data(Qt.ItemDataRole.UserRole))
        if not items:
            QMessageBox.information(self, "提示", "你还没有选择任何文件。")
            return
        total = sum(i.size for i in items)
        if permanent:
            answer = QMessageBox.warning(
                self,
                "确认永久删除",
                f"将永久删除 {len(items)} 个文件，共 {cleaner.human_size(total)}，无法恢复。\n确定继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.permanent = permanent
        self.selected_items = items
        self.accept()


class DiskUsageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("磁盘占用")
        self.setMinimumWidth(460)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(self)
        usage = cleaner.disk_usage()
        used = usage.used
        total = usage.total
        percent = int(used / total * 100) if total else 0

        title = QLabel(
            f"磁盘已用 <b>{cleaner.human_size(used)}</b> / {cleaner.human_size(total)}"
            f"（剩余 {cleaner.human_size(usage.free)}）"
        )
        layout.addWidget(title)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(percent)
        layout.addWidget(bar)

        layout.addWidget(QLabel("主目录下占用最大的文件夹："))
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["文件夹", "占用"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for name, size in cleaner.top_space_dirs():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(name))
            cell = QTableWidgetItem(cleaner.human_size(size))
            cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 1, cell)
        layout.addWidget(table, 1)

        close = QPushButton("关闭")
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)
