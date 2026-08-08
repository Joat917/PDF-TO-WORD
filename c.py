import os
import sys

from PyQt5.QtCore import (
    Qt, QThread, QTimer, QObject, QSize, pyqtSignal, pyqtSlot
)
from PyQt5.QtGui import QIcon, QColor, QBrush, QFontDatabase
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QToolButton, QButtonGroup, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QFileDialog, QFormLayout,
    QPushButton, QPlainTextEdit, QDialog, QMenu, QAbstractItemView,
    QMessageBox
)

from a import convert
from b import PDFConvertManager
from n import svg_data, SvgIconManager
import traceback
PRINT_ERROR = True  # 是否在控制台打印所有错误信息

# ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
ICON_FILES = {
    "settings": "settings.svg",
    "file_list": "list_ul.svg",
    "folder": "folder.svg",
    "description": "console.svg",
    "stop": "stop.svg",
    "delete": "trash.svg",
    "clear_all": "eraser.svg",
    "copy": "copy.svg",
    "refresh": "refresh.svg",
    "help": "help.svg",
    "convert": "convert.svg",
}
# get more icons from https://tabler-icons.io/

STATUS_TEXT = {
    "pending": "排队中",
    "running": "运行中",
    "success": "成功",
    "failed": "失败",
    "stopped": "已停止",
    "submitting": "提交中",
}

STATUS_COLOR = {
    "pending": QColor("#666666"),
    "running": QColor("#1e88e5"),
    "success": QColor("#2e7d32"),
    "failed": QColor("#c62828"),
    "stopped": QColor("#e65100"),
    "submitting": QColor("#888888"),
}

END_STATUS = {"success", "failed", "stopped"}


# 一个普通的支持拖放的 QWidget，用于接收文件或文件夹拖放
class DropWidget(QWidget):
    files_dropped = pyqtSignal(list)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()


class FileListWidget(QListWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self._empty_hint = None

    def set_empty_hint(self, hint: QLabel):
        self._empty_hint = hint
        hint.setParent(self.viewport())
        hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._layout_hint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_hint()

    def _layout_hint(self):
        if self._empty_hint is not None:
            self._empty_hint.setGeometry(
                0, 0, self.viewport().width(), self.viewport().height()
            )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()


class LogDialog(QDialog):
    refresh_requested = pyqtSignal(str)

    def __init__(self, task_id, icons=None, parent=None):
        super().__init__(parent)
        self._task_id = task_id
        self._icons = icons or {}
        self.setWindowTitle(f"日志 - {task_id}")
        self.resize(600, 400)

        self._log_edit = QPlainTextEdit()
        self._log_edit.setReadOnly(True)
        self._log_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._log_edit.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

        copy_btn = QPushButton()
        if "copy" in self._icons:
            copy_btn.setIcon(self._icons["copy"])
        copy_btn.setToolTip("复制日志")
        copy_btn.clicked.connect(self._copy_log)

        refresh_btn = QPushButton()
        if "refresh" in self._icons:
            refresh_btn.setIcon(self._icons["refresh"])
        refresh_btn.setToolTip("刷新日志")
        refresh_btn.clicked.connect(
            lambda: self.refresh_requested.emit(self._task_id)
        )

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(refresh_btn)

        layout = QVBoxLayout()
        layout.addWidget(self._log_edit)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_log_ready(self, task_id, log):
        if task_id == self._task_id:
            self._log_edit.setPlainText(log)
            scrollbar = self._log_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def on_log_error(self, task_id, error):
        if task_id == self._task_id:
            self._log_edit.setPlainText(f"获取日志失败: {error}")
            scrollbar = self._log_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _copy_log(self):
        self._log_edit.copy()


class Worker(QObject):
    tasks_updated = pyqtSignal(list)
    task_submitted = pyqtSignal(str, str)
    task_submit_failed = pyqtSignal(str, str)
    task_stopped = pyqtSignal(str, bool)
    log_ready = pyqtSignal(str, str)
    log_error = pyqtSignal(str, str)
    worker_error = pyqtSignal(str)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._timer = None

    @pyqtSlot()
    def start(self):
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._poll_tasks)
        self._timer.start()

    @pyqtSlot(list)
    def submit_tasks(self, tasks):
        for task in tasks:
            try:
                task_id = self._manager.submit(
                    task["src_path"],
                    task.get("dest_path"),
                    task.get("password")
                )
                self.task_submitted.emit(task_id, task["src_path"])
            except Exception as e:
                if PRINT_ERROR: traceback.print_exc()
                self.task_submit_failed.emit(task["src_path"], str(e))

    @pyqtSlot(str)
    def stop_task(self, task_id):
        try:
            ok = self._manager.stop(task_id)
            self.task_stopped.emit(task_id, bool(ok))
        except Exception as e:
            if PRINT_ERROR: traceback.print_exc()
            self.worker_error.emit(f"停止任务失败: {e}")

    @pyqtSlot(str)
    def get_log(self, task_id):
        try:
            log = self._manager.get_log(task_id)
            self.log_ready.emit(task_id, log)
        except Exception as e:
            if PRINT_ERROR: traceback.print_exc()
            self.log_error.emit(task_id, str(e))

    @pyqtSlot()
    def shutdown(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        self.thread().quit()

    def _poll_tasks(self):
        try:
            tasks = self._manager.get_tasks()
            self.tasks_updated.emit(tasks)
        except Exception as e:
            if PRINT_ERROR: traceback.print_exc()
            self.worker_error.emit(f"轮询失败: {e}")


class MainWindow(QMainWindow):
    request_submit_tasks = pyqtSignal(list)
    request_stop_task = pyqtSignal(str)
    request_get_log = pyqtSignal(str)
    request_shutdown = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF To Word")
        self.resize(800, 500)

        self._icons = self._load_icons()
        self.setWindowIcon(self._icons["convert"])

        self._added_paths = set()          # normalized absolute path -> None
        self._src_path_to_row = {}         # normalized absolute path -> row
        self._task_id_to_row = {}          # task_id -> row
        self._log_dialog = None

        self._build_ui()
        self._create_worker_thread()
        self.show()

    # ---------- icons ----------
    def _load_icons(self):
        # icons = {}
        # for name, filename in ICON_FILES.items():
        #     path = os.path.join(ICON_DIR, filename)
        #     if not os.path.isfile(path):
        #         raise FileNotFoundError(f"缺少图标文件: {path}")
        #     icons[name] = QIcon(path)
        # return icons
        svg_data_mapped = {name:svg_data[filename] for name, filename in ICON_FILES.items()}
        return SvgIconManager(svg_data_mapped)


    # ---------- UI ----------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 左侧导航
        nav = QWidget()
        nav.setFixedWidth(64)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        nav_layout.setAlignment(Qt.AlignTop)

        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(self._icons["settings"])
        self.settings_btn.setIconSize(QSize(32, 32))
        self.settings_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.settings_btn.setCheckable(True)
        self.settings_btn.setToolTip("转换设置")
        self.settings_btn.setAutoRaise(True)

        self.files_btn = QToolButton()
        self.files_btn.setIcon(self._icons["file_list"])
        self.files_btn.setIconSize(QSize(32, 32))
        self.files_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.files_btn.setCheckable(True)
        self.files_btn.setChecked(True)
        self.files_btn.setToolTip("文件列表")
        self.files_btn.setAutoRaise(True)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_group.addButton(self.files_btn, 0)
        self._nav_group.addButton(self.settings_btn, 1)
        self._nav_group.buttonClicked.connect(self._on_nav_clicked)

        nav_layout.addWidget(self.files_btn)
        nav_layout.addWidget(self.settings_btn)

        # 右侧页面
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_files_page())
        self.stack.addWidget(self._create_settings_page())

        root_layout.addWidget(nav)
        root_layout.addWidget(self.stack, 1)

    def _create_settings_page(self):
        page = DropWidget()
        page.setAcceptDrops(True)
        page.files_dropped.connect(self._on_files_dropped)

        form = QFormLayout(page)
        form.setContentsMargins(20, 20, 20, 20)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("留空表示使用源文件目录")

        browse_btn = QToolButton()
        browse_btn.setIcon(self._icons["folder"])
        browse_btn.setToolTip("选择输出目录")
        browse_btn.clicked.connect(self._browse_output_dir)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(browse_btn)
        form.addRow("输出目录：", dir_layout)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("加密 PDF 的密码（可留空）")
        form.addRow("PDF 密码：", self.password_edit)

        return page

    def _create_files_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = FileListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(
            self._show_context_menu
        )
        self.list_widget.files_dropped.connect(self._on_files_dropped)

        self._empty_hint = QLabel("将 PDF 文件或文件夹拖拽到此处")
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setStyleSheet("color: #888888; font-size: 24px;")
        self._empty_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.list_widget.set_empty_hint(self._empty_hint)

        layout.addWidget(self.list_widget)
        return page

    def _browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_edit.setText(directory)

    def _on_nav_clicked(self, button):
        self.stack.setCurrentIndex(self._nav_group.id(button))

    # ---------- Worker 线程 ----------
    def _create_worker_thread(self):
        manager = PDFConvertManager(convert)
        self._worker = Worker(manager)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)

        # 主线程 -> Worker（QueuedConnection 显式指定）
        self.request_submit_tasks.connect(
            self._worker.submit_tasks, Qt.QueuedConnection
        )
        self.request_stop_task.connect(
            self._worker.stop_task, Qt.QueuedConnection
        )
        self.request_get_log.connect(
            self._worker.get_log, Qt.QueuedConnection
        )
        self.request_shutdown.connect(
            self._worker.shutdown, Qt.QueuedConnection
        )

        # Worker -> 主线程（QueuedConnection 显式指定）
        self._worker.tasks_updated.connect(
            self._on_tasks_updated, Qt.QueuedConnection
        )
        self._worker.task_submitted.connect(
            self._on_task_submitted, Qt.QueuedConnection
        )
        self._worker.task_submit_failed.connect(
            self._on_task_submit_failed, Qt.QueuedConnection
        )
        self._worker.task_stopped.connect(
            self._on_task_stopped, Qt.QueuedConnection
        )
        self._worker.worker_error.connect(
            self._on_worker_error, Qt.QueuedConnection
        )

        self._thread.started.connect(self._worker.start)
        self._thread.start()

    # ---------- 文件添加与提交 ----------
    def _on_files_dropped(self, paths):
        new_files = []
        for p in paths:
            if os.path.isdir(p):
                for root, _dirs, files in os.walk(p):
                    for name in files:
                        if name.lower().endswith(".pdf"):
                            new_files.append(os.path.join(root, name))
            elif os.path.isfile(p) and p.lower().endswith(".pdf"):
                new_files.append(p)

        added_any = False
        for path in new_files:
            norm = os.path.normcase(os.path.abspath(path))
            if norm in self._added_paths:
                continue
            self._added_paths.add(norm)
            self._add_item(norm, os.path.abspath(path))
            added_any = True

        if not added_any:
            self.statusBar().showMessage("未添加任何新 PDF 文件", 3000)

    def _add_item(self, norm, src_path):
        item = QListWidgetItem()
        data = {
            "norm": norm,
            "src": src_path,
            "task_id": None,
            "status": "submitting",
        }
        item.setData(Qt.UserRole, data)
        self.list_widget.addItem(item)
        row = self.list_widget.row(item)
        self._src_path_to_row[norm] = row
        self._refresh_item(item)
        self._update_empty_hint()

        dest_path = self._build_dest_path(src_path)
        password = self._get_password()
        self.request_submit_tasks.emit([
            {"src_path": src_path, "dest_path": dest_path, "password": password}
        ])

    def _build_dest_path(self, src_path):
        stem = os.path.splitext(os.path.basename(src_path))[0]
        output_dir = self.output_dir_edit.text().strip()
        if output_dir:
            return os.path.join(output_dir, stem + ".docx")
        return os.path.join(os.path.dirname(src_path), stem + ".docx")

    def _get_password(self):
        pwd = self.password_edit.text().strip()
        return pwd if pwd else None

    # ---------- Worker 信号处理 ----------
    def _on_tasks_updated(self, tasks):
        for task in tasks:
            tid = task.get("task_id")
            if not tid or tid not in self._task_id_to_row:
                continue
            row = self._task_id_to_row[tid]
            item = self.list_widget.item(row)
            if item is None:
                continue
            data = item.data(Qt.UserRole)
            if data is None:
                continue
            data["status"] = task.get("status", data.get("status", "unknown"))
            if task.get("exitcode") is not None:
                data["exitcode"] = task["exitcode"]
            else:
                data.pop("exitcode", None)
            item.setData(Qt.UserRole, data)
            self._refresh_item(item)

    def _on_task_submitted(self, task_id, src_path):
        norm = os.path.normcase(os.path.abspath(src_path))
        row = self._src_path_to_row.get(norm)
        if row is None:
            return
        item = self.list_widget.item(row)
        if item is None:
            return
        data = item.data(Qt.UserRole)
        data["task_id"] = task_id
        data["status"] = "pending"
        item.setData(Qt.UserRole, data)
        self._task_id_to_row[task_id] = row
        self._refresh_item(item)

    def _on_task_submit_failed(self, src_path, error):
        norm = os.path.normcase(os.path.abspath(src_path))
        row = self._src_path_to_row.get(norm)
        if row is None:
            return
        item = self.list_widget.item(row)
        if item is None:
            return
        data = item.data(Qt.UserRole)
        data["status"] = "failed"
        item.setData(Qt.UserRole, data)
        self._refresh_item(item)
        self.statusBar().showMessage(f"提交失败：{error}", 3000)

    def _on_task_stopped(self, task_id, success):
        if not success:
            self.statusBar().showMessage(f"停止失败：{task_id}", 3000)
        # 成功时状态由轮询更新

    def _on_worker_error(self, message):
        self.statusBar().showMessage(message, 5000)

    # ---------- UI 辅助 ----------
    def _refresh_item(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        src = data["src"]
        status = data.get("status", "unknown")
        status_text = STATUS_TEXT.get(status, status)
        item.setText(f"{os.path.basename(src)} — {status_text}")
        item.setForeground(QBrush(STATUS_COLOR.get(status, QColor("#000000"))))

        parts = [f"文件: {src}", f"状态: {status_text}"]
        tid = data.get("task_id")
        if tid:
            parts.append(f"task_id: {tid}")
        if data.get("exitcode") is not None:
            parts.append(f"exitcode: {data['exitcode']}")
        item.setToolTip("\n".join(parts))

    def _update_empty_hint(self):
        self._empty_hint.setVisible(self.list_widget.count() == 0)

    # ---------- 右键菜单 ----------
    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self)
        act_log = menu.addAction(self._icons["description"], "查看日志")
        act_stop = menu.addAction(self._icons["stop"], "停止任务")
        menu.addSeparator()
        act_remove = menu.addAction(self._icons["delete"], "移除选中")
        act_clear = menu.addAction(self._icons["clear_all"], "清空已完成")

        chosen = menu.exec_(self.list_widget.mapToGlobal(pos))
        if chosen == act_log:
            self._show_log()
        elif chosen == act_stop:
            self._stop_selected()
        elif chosen == act_remove:
            self._remove_selected()
        elif chosen == act_clear:
            self._clear_finished()

    def _show_log(self):
        for item in self.list_widget.selectedItems():
            data = item.data(Qt.UserRole)
            tid = data.get("task_id")
            if tid:
                self._open_log_dialog(tid)
                return

    def _stop_selected(self):
        for item in self.list_widget.selectedItems():
            data = item.data(Qt.UserRole)
            tid = data.get("task_id")
            status = data.get("status")
            if tid and status in ("pending", "running"):
                self.request_stop_task.emit(tid)

    def _remove_selected(self):
        rows = [
            self.list_widget.row(item)
            for item in self.list_widget.selectedItems()
        ]
        rows.sort(reverse=True)
        for row in rows:
            item = self.list_widget.takeItem(row)
            self._cleanup_item(item)
            del item
        self._update_empty_hint()

    def _clear_finished(self):
        rows = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            data = item.data(Qt.UserRole)
            if data.get("status") in END_STATUS:
                rows.append(row)
        for row in reversed(rows):
            item = self.list_widget.takeItem(row)
            self._cleanup_item(item)
            del item
        self._update_empty_hint()

    def _cleanup_item(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        norm = data.get("norm")
        tid = data.get("task_id")
        if norm and norm in self._added_paths:
            self._added_paths.remove(norm)
        if norm and norm in self._src_path_to_row:
            del self._src_path_to_row[norm]
        if tid and tid in self._task_id_to_row:
            del self._task_id_to_row[tid]

    # ---------- 日志对话框 ----------
    def _open_log_dialog(self, task_id):
        # 关闭旧的日志对话框
        if self._log_dialog is not None:
            self._log_dialog.close()

        dialog = LogDialog(task_id, self._icons, self)
        dialog.refresh_requested.connect(self._request_log)
        self._worker.log_ready.connect(dialog.on_log_ready, Qt.QueuedConnection)
        self._worker.log_error.connect(dialog.on_log_error, Qt.QueuedConnection)
        dialog.finished.connect(lambda: self._on_log_dialog_closed(dialog))

        self._log_dialog = dialog
        dialog.show()
        self.request_get_log.emit(task_id)

    def _request_log(self, task_id):
        self.request_get_log.emit(task_id)

    def _on_log_dialog_closed(self, dialog):
        if dialog is self._log_dialog:
            try:
                self._worker.log_ready.disconnect(dialog.on_log_ready)
            except TypeError:
                if PRINT_ERROR: traceback.print_exc()
                pass
            try:
                self._worker.log_error.disconnect(dialog.on_log_error)
            except TypeError:
                if PRINT_ERROR: traceback.print_exc()
                pass
            self._log_dialog = None
            dialog.deleteLater()

    # ---------- 关闭 ----------
    def closeEvent(self, event):
        self.request_shutdown.emit()
        if hasattr(self, "_thread"):
            self._thread.wait(5000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
    except FileNotFoundError as e:
        if PRINT_ERROR: traceback.print_exc()
        QMessageBox.critical(None, "启动失败", str(e))
        sys.exit(1)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
