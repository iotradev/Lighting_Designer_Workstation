# -*- coding: utf-8 -*-
"""备份管理器 - BackupManager"""
import sys, os, shutil, json, difflib, hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QGroupBox,
    QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QCheckBox, QTabWidget, QTextEdit,
    QListWidgetItem, QProgressBar, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QColor

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow


@dataclass
class BackupInfo:
    name: str
    path: Path
    timestamp: str
    size_bytes: int
    file_count: int


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def count_files(directory: Path) -> int:
    count = 0
    for _ in directory.rglob('*'):
        count += 1
    return count


def dir_size(directory: Path) -> int:
    total = 0
    for f in directory.rglob('*'):
        if f.is_file():
            total += f.stat().st_size
    return total


class DiffThread(QThread):
    """后台对比线程"""
    result_ready = Signal(str)

    def __init__(self, path_a: Path, path_b: Path):
        super().__init__()
        self.path_a = path_a
        self.path_b = path_b

    def run(self):
        try:
            files_a = {f.relative_to(self.path_a): f for f in self.path_a.rglob('*') if f.is_file()}
            files_b = {f.relative_to(self.path_b): f for f in self.path_b.rglob('*') if f.is_file()}

            all_keys = sorted(set(files_a.keys()) | set(files_b.keys()))
            lines = []

            for key in all_keys:
                in_a = key in files_a
                in_b = key in files_b
                if in_a and not in_b:
                    lines.append(f"  ➖ 删除: {key}")
                elif in_b and not in_a:
                    lines.append(f"  ➕ 新增: {key}")
                else:
                    try:
                        content_a = files_a[key].read_text(encoding='utf-8', errors='replace')
                        content_b = files_b[key].read_text(encoding='utf-8', errors='replace')
                        if content_a != content_b:
                            lines.append(f"  ✏️ 修改: {key}")
                            diff = list(difflib.unified_diff(
                                content_a.splitlines(), content_b.splitlines(),
                                fromfile=f"A/{key}", tofile=f"B/{key}", lineterm=''))
                            for d in diff[:20]:
                                lines.append(f"    {d}")
                            if len(diff) > 20:
                                lines.append(f"    ... ({len(diff) - 20} 行省略)")
                    except Exception:
                        sa = files_a[key].stat().st_size
                        sb = files_b[key].stat().st_size
                        if sa != sb:
                            lines.append(f"  ✏️ 修改(二进制): {key} ({format_size(sa)} -> {format_size(sb)})")

            if not lines:
                result = "两个备份完全相同。"
            else:
                result = f"发现 {len(lines)} 处差异:\n\n" + "\n".join(lines)

            self.result_ready.emit(result)
        except Exception as e:
            self.result_ready.emit(f"对比失败: {e}")


class BackupManagerWindow(BaseToolWindow):
    """备份管理器主窗口"""

    def __init__(self):
        super().__init__('BackupManager', '备份管理器', '1.0.0', 1100, 800)

        # Toolbar
        self.toolbar.addSeparator()
        self.toolbar.addAction("🔄 刷新列表", self._refresh_backups)
        self.toolbar.addAction("📦 创建备份", self._create_backup)

        # Paths
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.backups_dir = self.project_root / "Backups"
        self.backups_dir.mkdir(exist_ok=True)
        self.settings_file = self.backups_dir / "backup_settings.json"

        # Auto-backup settings
        self.auto_backup_enabled = False
        self.auto_backup_interval = 30  # minutes
        self.max_backups = 10
        self._load_settings()

        # Backup list
        self.backup_infos: list[BackupInfo] = []
        self._diff_thread = None

        # Build UI
        central = QWidget()
        main_layout = QHBoxLayout(central)

        # Left: backup list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(350)

        # Stats
        stats_group = QGroupBox("📊 备份统计")
        stats_layout = QHBoxLayout(stats_group)
        self.lbl_count = QLabel("总数: 0")
        self.lbl_total_size = QLabel("总大小: 0 B")
        self.lbl_latest = QLabel("最新: -")
        stats_layout.addWidget(self.lbl_count)
        stats_layout.addWidget(self.lbl_total_size)
        stats_layout.addWidget(self.lbl_latest)
        left_layout.addWidget(stats_group)

        # Backup table
        table_group = QGroupBox("📦 备份列表")
        tl = QVBoxLayout(table_group)
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels(["名称", "时间", "大小", "文件数", "路径"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.backup_table.currentCellChanged.connect(self._on_backup_selected)
        tl.addWidget(self.backup_table)

        # Action buttons
        btn_row1 = QHBoxLayout()
        btn_create = QPushButton("📦 创建备份")
        btn_create.clicked.connect(self._create_backup)
        btn_row1.addWidget(btn_create)
        btn_restore = QPushButton("♻️ 恢复选中")
        btn_restore.clicked.connect(self._restore_backup)
        btn_row1.addWidget(btn_restore)
        tl.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_delete = QPushButton("🗑️ 删除选中")
        btn_delete.clicked.connect(self._delete_backup)
        btn_row2.addWidget(btn_delete)
        btn_diff = QPushButton("🔍 对比选中")
        btn_diff.setToolTip("选中2个备份进行对比")
        btn_diff.clicked.connect(self._diff_backups)
        btn_row2.addWidget(btn_diff)
        tl.addLayout(btn_row2)

        left_layout.addWidget(table_group)

        # Right: settings + diff
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Auto-backup settings
        settings_group = QGroupBox("⚙️ 自动备份设置")
        sf = QFormLayout(settings_group)
        self.chk_auto = QCheckBox("启用自动备份")
        self.chk_auto.setChecked(self.auto_backup_enabled)
        self.chk_auto.toggled.connect(self._on_auto_toggled)
        sf.addRow(self.chk_auto)
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(5, 1440)
        self.spin_interval.setValue(self.auto_backup_interval)
        self.spin_interval.setSuffix(" 分钟")
        self.spin_interval.valueChanged.connect(self._on_interval_changed)
        sf.addRow("备份间隔:", self.spin_interval)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(1, 100)
        self.spin_max.setValue(self.max_backups)
        self.spin_max.valueChanged.connect(self._on_max_changed)
        sf.addRow("最大备份数:", self.spin_max)
        btn_save_settings = QPushButton("保存设置")
        btn_save_settings.clicked.connect(self._save_settings)
        sf.addRow(btn_save_settings)
        right_layout.addWidget(settings_group)

        # Diff output
        diff_group = QGroupBox("🔍 备份对比结果")
        dl = QVBoxLayout(diff_group)
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.diff_text.setFont(QFont("Consolas", 10))
        self.diff_text.setPlaceholderText('选中两个备份后点击"对比选中"查看差异...')
        dl.addWidget(self.diff_text)
        right_layout.addWidget(diff_group)

        # Info panel
        info_group = QGroupBox("📋 备份详情")
        il = QVBoxLayout(info_group)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        self.info_text.setFont(QFont("Microsoft YaHei", 9))
        il.addWidget(self.info_text)
        right_layout.addWidget(info_group)

        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 1)

        self.set_central_content(central)

        # Auto-backup timer
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._auto_backup)
        self._update_auto_timer()

        # Refresh
        self._refresh_backups()
        self.logger.info("备份管理器已就绪")

    def _load_settings(self):
        if self.settings_file.exists():
            try:
                data = json.loads(self.settings_file.read_text(encoding='utf-8'))
                self.auto_backup_enabled = data.get('enabled', False)
                self.auto_backup_interval = data.get('interval', 30)
                self.max_backups = data.get('max_count', 10)
            except Exception as e:
                self.logger.warning(f"备份设置文件损坏，使用默认设置: {e}")

    def _save_settings(self):
        data = {
            'enabled': self.auto_backup_enabled,
            'interval': self.auto_backup_interval,
            'max_count': self.max_backups
        }
        try:
            self.settings_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            self.logger.info("备份设置已保存")
            QMessageBox.information(self, "保存成功", "自动备份设置已保存。")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _update_auto_timer(self):
        if self.auto_backup_enabled:
            self._auto_timer.start(self.auto_backup_interval * 60 * 1000)
        else:
            self._auto_timer.stop()

    def _on_auto_toggled(self, checked):
        self.auto_backup_enabled = checked
        self._update_auto_timer()

    def _on_interval_changed(self, val):
        self.auto_backup_interval = val
        self._update_auto_timer()

    def _on_max_changed(self, val):
        self.max_backups = val

    def _refresh_backups(self):
        self.backup_infos.clear()
        if not self.backups_dir.exists():
            return
        for d in sorted(self.backups_dir.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith('backup_'):
                try:
                    ts = d.name.replace('backup_', '')
                    size = dir_size(d)
                    fc = count_files(d)
                    self.backup_infos.append(BackupInfo(
                        name=d.name, path=d,
                        timestamp=ts, size_bytes=size, file_count=fc
                    ))
                except Exception:
                    pass

        self.backup_table.setRowCount(len(self.backup_infos))
        for i, bi in enumerate(self.backup_infos):
            self.backup_table.setItem(i, 0, QTableWidgetItem(bi.name))
            ts_display = bi.timestamp.replace('_', ' ').replace('-', ':') if len(bi.timestamp) > 10 else bi.timestamp
            # Try to format nicely
            try:
                dt = datetime.strptime(bi.timestamp, "%Y%m%d_%H%M%S")
                ts_display = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            self.backup_table.setItem(i, 1, QTableWidgetItem(ts_display))
            self.backup_table.setItem(i, 2, QTableWidgetItem(format_size(bi.size_bytes)))
            self.backup_table.setItem(i, 3, QTableWidgetItem(str(bi.file_count)))
            self.backup_table.setItem(i, 4, QTableWidgetItem(str(bi.path)))

        # Stats
        total_size = sum(bi.size_bytes for bi in self.backup_infos)
        self.lbl_count.setText(f"总数: {len(self.backup_infos)}")
        self.lbl_total_size.setText(f"总大小: {format_size(total_size)}")
        if self.backup_infos:
            self.lbl_latest.setText(f"最新: {self.backup_infos[0].name}")
        else:
            self.lbl_latest.setText("最新: -")

        self._enforce_max_backups()
        self.logger.info(f"刷新备份列表: {len(self.backup_infos)} 个备份")

    def _create_backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{ts}"
        backup_path = self.backups_dir / backup_name
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            # Copy project files (exclude Backups dir, __pycache__, .git)
            exclude = {'Backups', '__pycache__', '.git', 'node_modules', '.idea'}
            src = self.project_root
            for item in src.iterdir():
                if item.name in exclude:
                    continue
                dst = backup_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True,
                                   ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                else:
                    shutil.copy2(item, dst)

            self.logger.info(f"创建备份: {backup_name}")
            self._refresh_backups()
            QMessageBox.information(self, "备份成功", f"备份已创建:\n{backup_name}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", str(e))
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)

    def _restore_backup(self):
        row = self.backup_table.currentRow()
        if row < 0 or row >= len(self.backup_infos):
            QMessageBox.warning(self, "提示", "请先选择一个备份。")
            return
        bi = self.backup_infos[row]
        reply = QMessageBox.question(
            self, "确认恢复",
            f"确定要从备份恢复项目吗？\n\n备份: {bi.name}\n时间: {bi.timestamp}\n\n当前项目将被覆盖！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            # Copy backup files to project root (excluding backup metadata)
            exclude = {'Backups', '__pycache__', '.git', 'node_modules', '.idea'}
            for item in bi.path.iterdir():
                if item.name in exclude:
                    continue
                dst = self.project_root / item.name
                if item.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
            self.logger.info(f"已从备份恢复: {bi.name}")
            QMessageBox.information(self, "恢复成功", f"项目已从备份恢复:\n{bi.name}")
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", str(e))

    def _delete_backup(self):
        rows = sorted(set(idx.row() for idx in self.backup_table.selectedIndexes()), reverse=True)
        if not rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的备份。")
            return
        names = [self.backup_infos[r].name for r in rows if r < len(self.backup_infos)]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {len(names)} 个备份吗？\n\n" + "\n".join(names),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        for r in rows:
            if r < len(self.backup_infos):
                bi = self.backup_infos[r]
                try:
                    shutil.rmtree(bi.path)
                    self.logger.info(f"删除备份: {bi.name}")
                except Exception as e:
                    self.logger.error(f"删除失败 {bi.name}: {e}")
        self._refresh_backups()

    def _diff_backups(self):
        rows = sorted(set(idx.row() for idx in self.backup_table.selectedIndexes()))
        if len(rows) != 2:
            QMessageBox.warning(self, "提示", "请选中恰好2个备份进行对比。")
            return
        a = self.backup_infos[rows[0]]
        b = self.backup_infos[rows[1]]
        self.diff_text.setText(f"正在对比 {a.name} 和 {b.name} ...")
        self._diff_thread = DiffThread(a.path, b.path)
        self._diff_thread.result_ready.connect(self._on_diff_result)
        self._diff_thread.start()

    def _on_diff_result(self, result: str):
        self.diff_text.setText(result)

    def _on_backup_selected(self, row, col):
        if 0 <= row < len(self.backup_infos):
            bi = self.backup_infos[row]
            info = [
                f"备份名称: {bi.name}",
                f"创建时间: {bi.timestamp}",
                f"备份大小: {format_size(bi.size_bytes)}",
                f"文件数量: {bi.file_count}",
                f"备份路径: {bi.path}",
            ]
            self.info_text.setText("\n".join(info))

    def _auto_backup(self):
        self.logger.info("执行自动备份...")
        self._create_backup()

    def _enforce_max_backups(self):
        if len(self.backup_infos) > self.max_backups:
            to_delete = self.backup_infos[self.max_backups:]
            for bi in to_delete:
                try:
                    shutil.rmtree(bi.path)
                    self.logger.info(f"自动清理旧备份: {bi.name}")
                except Exception:
                    pass
            if to_delete:
                self._refresh_backups()

    def _show_shortcuts(self):
        text = """<table>
        <tr><td><b>创建备份</b></td><td>创建当前项目快照</td></tr>
        <tr><td><b>恢复备份</b></td><td>将选中备份恢复到项目目录</td></tr>
        <tr><td><b>对比备份</b></td><td>选中2个备份查看差异</td></tr>
        <tr><td><b>自动备份</b></td><td>在设置中启用定时备份</td></tr>
        </table>"""
        QMessageBox.information(self, "操作说明", text)

    def closeEvent(self, event):
        """关闭窗口时清理线程"""
        if hasattr(self, '_diff_thread') and self._diff_thread and self._diff_thread.isRunning():
            self._diff_thread.terminate()
            self._diff_thread.wait(2000)
        if hasattr(self, '_auto_timer'):
            self._auto_timer.stop()
        super().closeEvent(event)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = BackupManagerWindow()
    window.show()
    sys.exit(app.exec())
