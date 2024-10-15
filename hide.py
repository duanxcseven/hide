import sys
import ctypes
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QFrame
from PySide2.QtCore import Qt, QTimer
import win32gui
import win32con


def is_valid_window(hwnd, title):
    """判断窗口是否为有效的主窗口，只显示在任务栏的窗口"""
    if not title:
        return False

    # 获取窗口类名
    class_name = win32gui.GetClassName(hwnd)

    if "Cortana" in title or "SearchUI" in class_name:
        return False

    # 检查窗口是否可见，并且不处于最小化状态
    if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
        return False

    # 检查窗口的样式，确保它是应用程序窗口而非工具窗口等
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    if not (style & win32con.WS_EX_APPWINDOW):
        return False

    return True


class WindowBlock(QFrame):
    """表示单个窗口信息的块"""

    def __init__(self, hwnd, title, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.title = title[:8]  # 最多显示8个字符
        self.init_ui()

    def init_ui(self):
        # 设置边框
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)  # 边框线宽

        # 布局：横向布局，标题在左，滑块在右
        layout = QHBoxLayout()

        # 设置统一的固定大小
        self.setFixedSize(50, 150)  # 宽度100，高度150，根据你的需求调整

        # 调整内部布局的间距和边距，让整体更紧凑
        layout.setContentsMargins(5, 5, 5, 5)  # 控制窗口边距，越小越紧凑
        layout.setSpacing(3)  # 控制内部元素之间的间距

        # 竖直显示窗口标题
        self.title_label = QLabel(self.format_vertical_text(self.title))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # 透明度滑块，竖向布局
        self.slider = QSlider(Qt.Vertical)  # 改为竖向拖动
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(255)
        self.slider.valueChanged.connect(self.change_transparency)
        layout.addWidget(self.slider)

        self.setLayout(layout)

    def format_vertical_text(self, text):
        """将文本格式化为竖直排列"""
        return '\n'.join(list(text))

    def change_transparency(self, value):
        """根据滑块值调整窗口透明度"""
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, value, win32con.LWA_ALPHA)


class WindowTransparencyApp(QWidget):
    """主窗口类，展示所有可调整透明度的窗口"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("窗口透明度调整器")
        self.setGeometry(300, 300, 800, 200)  # 横向布局，调宽度

        # 总体布局
        self.layout = QHBoxLayout()  # 改为横向布局
        self.layout.setContentsMargins(5, 5, 5, 5)  # 控制主窗口的边距
        self.layout.setSpacing(5)  # 控制每个窗口块之间的间距
        self.setLayout(self.layout)

        # 设置定时器每秒更新窗口列表
        self.timer = QTimer(self)  # 使用 QTimer
        self.timer.timeout.connect(self.update_window_list)
        self.timer.start(1000)  # 每秒刷新一次窗口列表

        # 初始化窗口列表
        self.windows = []

    def update_window_list(self):
        """每秒更新当前打开的窗口列表，保持最新状态。"""
        current_hwnds = [hwnd for hwnd, _ in self.windows]
        new_windows = []

        def enum_window_callback(hwnd, _):
            title = win32gui.GetWindowText(hwnd)
            if is_valid_window(hwnd, title):
                if hwnd not in current_hwnds:  # 仅添加新窗口
                    new_windows.append((hwnd, title))

        # 枚举所有窗口
        win32gui.EnumWindows(enum_window_callback, None)

        # 如果有新窗口，更新显示
        if new_windows:
            for hwnd, title in new_windows:
                self.windows.append((hwnd, title))
                window_block = WindowBlock(hwnd, title)
                self.layout.addWidget(window_block)

        # 检查是否有窗口关闭
        for hwnd, title in self.windows[:]:
            if not win32gui.IsWindow(hwnd):
                self.windows.remove((hwnd, title))
                # 删除对应的窗口块
                for i in range(self.layout.count()):
                    widget = self.layout.itemAt(i).widget()
                    if isinstance(widget, WindowBlock) and widget.hwnd == hwnd:
                        widget.deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowTransparencyApp()
    window.show()
    window.adjustSize()
    sys.exit(app.exec_())
