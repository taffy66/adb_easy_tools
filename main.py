import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class AdbOperationThread(QThread):
    operation_finished = pyqtSignal(bool, str)  # Signal: success, message

    def __init__(self, operation, file_path):
        super().__init__()
        self.operation = operation  # 'install' or 'push'
        self.file_path = file_path

    def run(self):
        try:
            if self.operation == 'install':
                # 执行adb install命令
                result = subprocess.run(
                    ["adb", "install", self.file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if result.returncode == 0:
                    # 安装成功
                    self.operation_finished.emit(True, "安装完成")
                else:
                    # 安装失败，发送错误信息
                    error_message = result.stderr.strip() or "未知错误"
                    self.operation_finished.emit(False, f"安装失败: {error_message}")

            elif self.operation == 'push':
                # 执行adb push命令，将文件传输到/sdcard/Download
                result = subprocess.run(
                    ["adb", "push", self.file_path, "/sdcard/Download/"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if result.returncode == 0:
                    # 传输成功
                    self.operation_finished.emit(True, "传输完成")
                else:
                    # 传输失败，发送错误信息
                    error_message = result.stderr.strip() or "未知错误"
                    self.operation_finished.emit(False, f"传输失败: {error_message}")
            else:
                # 未知操作
                self.operation_finished.emit(False, "未知的操作类型")
        except FileNotFoundError:
            # adb命令未找到
            self.operation_finished.emit(False, "未找到adb，请确保已安装并配置ADB路径")
        except Exception as e:
            # 其他异常
            self.operation_finished.emit(False, f"操作过程中发生错误: {str(e)}")

class DragDropLabel(QLabel):
    def __init__(self, parent=None):
        super(DragDropLabel, self).__init__(parent)
        self.setText("将文件拖放到此处")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QLabel { border: 4px dashed #aaa; }")
        self.setAcceptDrops(True)
        self.operation_thread = None  # 用于存储线程实例

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # 检查是否有文件
            for url in event.mimeData().urls():
                if url.toLocalFile():  # 确保是本地文件
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            # 这里只处理第一个文件
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.apk'):
                self.setText("正在安装APK...")
                self.perform_operation('install', file_path)
            else:
                self.setText("正在传输文件...")
                self.perform_operation('push', file_path)
        else:
            self.setText("没有文件被拖放过来")

    def perform_operation(self, operation, file_path):
        # 创建并启动操作线程
        self.operation_thread = AdbOperationThread(operation, file_path)
        self.operation_thread.operation_finished.connect(self.on_operation_finished)
        self.operation_thread.start()

    def on_operation_finished(self, success, message):
        self.setText(message)
        if not success:
            QMessageBox.warning(self, "操作失败", message)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("文件安装与传输器")
        self.setGeometry(100, 100, 400, 200)

        self.label = DragDropLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
