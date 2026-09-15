from __future__ import annotations

import sys

from PySide6.QtCore import QSettings, Qt, QThread, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QSystemTrayIcon,
    QVBoxLayout,
)

import cleaner
from dialogs import CleanPreviewDialog, DiskUsageDialog
from pet import Pet
from pet_art import SIZE_PRESETS

APP_NAME = "DesktopPet"


class ScanWorker(QThread):
    done = Signal(object)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            result = self.func()
        except Exception as exc:
            result = exc
        self.done.emit(result)


class BusyDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请稍候")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setFixedWidth(320)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(text))
        bar = QProgressBar()
        bar.setRange(0, 0)
        layout.addWidget(bar)


def make_paw_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#F5A623"))
    painter.drawEllipse(20, 26, 24, 22)
    for x, y in ((12, 18), (26, 10), (42, 12), (52, 24)):
        painter.drawEllipse(x, y, 14, 14)
    painter.end()
    return QIcon(pixmap)


class PetApp:
    def __init__(self, app: QApplication):
        self.app = app
        self.settings = QSettings("donutboy09", APP_NAME)
        species = self.settings.value("species", "cat", type=str)
        size = self.settings.value("size", "small", type=str)
        if size not in SIZE_PRESETS:
            size = "small"

        self.pet = Pet(species=species, size=size)
        self.pet.set_free_roam(self.settings.value("free_roam", True, type=bool))
        self._restore_position()
        self.pet.menu_requested.connect(self._show_pet_menu)
        self.pet.show()

        self.tray = QSystemTrayIcon(make_paw_icon(), app)
        self.tray.setToolTip("桌面宠物 - 右键和它互动")
        self.tray.setContextMenu(self._build_menu())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        self._worker = None
        self._busy = None

    def _restore_position(self):
        pos = self.settings.value("pos")
        if pos is not None:
            self.pet.move(pos)
        else:
            screen = self.app.primaryScreen().availableGeometry()
            self.pet.move(screen.right() - self.pet.width() - 40, screen.bottom() - self.pet.height() - 40)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.pet.setVisible(not self.pet.isVisible())

    def _build_menu(self) -> QMenu:
        menu = QMenu()

        header = menu.addAction(f"{'小猫' if self.pet.species == 'cat' else '小狗'} · 饱食度 {int(self.pet.hunger)}%")
        header.setEnabled(False)
        menu.addSeparator()

        menu.addAction("喂食", self._feed)
        menu.addAction("逗它玩", self.pet.trigger_happy)
        menu.addAction("睡觉 / 叫醒", self._toggle_sleep)
        freeze = menu.addAction("不动")
        freeze.setCheckable(True)
        freeze.setChecked(not self.pet.free_roam)
        freeze.triggered.connect(self._toggle_freeze)
        menu.addSeparator()

        menu.addAction("清理缓存", lambda: self._scan("cache", cleaner.scan_cache))
        menu.addAction("清理临时文件", lambda: self._scan("temp", cleaner.scan_temp))
        menu.addAction("清理下载文件夹", lambda: self._scan("downloads", cleaner.scan_downloads))
        menu.addAction("清空回收站", self._empty_trash)
        menu.addAction("清理桌面无用文件", lambda: self._scan("desktop", cleaner.scan_desktop_junk))
        menu.addAction("查看磁盘占用", self._show_disk_usage)
        menu.addSeparator()

        pet_menu = menu.addMenu("切换宠物")
        for key, label in (("cat", "小猫"), ("dog", "小狗")):
            action = pet_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.pet.species == key)
            action.triggered.connect(lambda _=False, k=key: self._set_species(k))

        size_menu = menu.addMenu("大小")
        for key, label in (("small", "小"), ("medium", "中"), ("large", "大")):
            action = size_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.pet.size_name == key)
            action.triggered.connect(lambda _=False, k=key: self._set_size(k))

        menu.addSeparator()
        menu.addAction("隐藏", lambda: self.pet.hide())
        menu.addAction("退出", self._quit)
        return menu

    def _show_pet_menu(self, pos):
        self._build_menu().exec(pos)

    def _refresh_tray_menu(self):
        self.tray.setContextMenu(self._build_menu())

    def _feed(self):
        self.pet.feed()
        self._refresh_tray_menu()

    def _toggle_sleep(self):
        self.pet.toggle_sleep()
        self._refresh_tray_menu()

    def _toggle_freeze(self, checked):
        self.pet.set_free_roam(not checked)
        self.settings.setValue("free_roam", self.pet.free_roam)
        self._refresh_tray_menu()

    def _set_size(self, size: str):
        self.pet.set_size(size)
        self.settings.setValue("size", size)
        self._refresh_tray_menu()

    def _set_species(self, species: str):
        self.pet.set_species(species)
        self.settings.setValue("species", species)
        self._refresh_tray_menu()

    def _show_disk_usage(self):
        DiskUsageDialog().exec()

    def _scan(self, key: str, func):
        if self._worker is not None and self._worker.isRunning():
            return
        self._busy = BusyDialog("正在扫描，请稍候…")
        self._busy.show()
        self._worker = ScanWorker(func)
        self._worker.done.connect(lambda result, k=key: self._on_scan_done(result))
        self._worker.start()

    def _on_scan_done(self, result):
        if self._busy is not None:
            self._busy.close()
            self._busy = None

        if isinstance(result, Exception):
            QMessageBox.critical(None, "扫描失败", str(result))
            return

        if result.count == 0:
            QMessageBox.information(None, result.title, f"没有找到可清理的文件。\n{result.note}")
            return

        dialog = CleanPreviewDialog(result)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        deleted, freed, errors = cleaner.delete_items(dialog.selected_items, permanent=dialog.permanent)
        message = f"已删除 {deleted} 个文件，释放 {cleaner.human_size(freed)}。"
        if errors:
            message += f"\n{len(errors)} 个文件删除失败。"
        QMessageBox.information(None, "清理完成", message)

    def _empty_trash(self):
        if cleaner.IS_WIN:
            answer = QMessageBox.warning(
                None,
                "清空回收站",
                "将永久清空 Windows 回收站，无法恢复。确定继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            ok, message = cleaner.empty_recycle_bin()
            QMessageBox.information(None, "回收站", message)
            return
        self._scan("trash", cleaner.scan_trash)

    def _quit(self):
        self.settings.setValue("pos", self.pet.pos())
        self.settings.setValue("species", self.pet.species)
        self.settings.setValue("size", self.pet.size_name)
        self.settings.setValue("free_roam", self.pet.free_roam)
        self.tray.hide()
        self.pet.close()
        self.app.quit()

    def run(self):
        self.app.exec()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    pet_app = PetApp(app)
    pet_app.run()


if __name__ == "__main__":
    main()
