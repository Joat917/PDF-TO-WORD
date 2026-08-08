from m import data as raw_data
import lzma
import base64
svg_data = dict(eval(lzma.decompress(base64.a85decode(raw_data)).decode('utf-8')))

from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QIcon, QIconEngine, QPainter, QPixmap
from PyQt5.QtCore import QByteArray, QRectF, Qt

class SvgIconEngine(QIconEngine):
    """从字节串/字符串创建矢量 QIcon 的核心引擎"""

    def __init__(self, svg_data):
        super().__init__()
        if isinstance(svg_data, str):
            svg_data = svg_data.encode('utf-8')
        self.svg_bytes = QByteArray(svg_data)
        self.renderer = QSvgRenderer(self.svg_bytes)

    def paint(self, painter, rect, mode, state):
        """核心绘制方法：把 SVG 渲染到给定矩形区域"""
        self.renderer.render(painter, rect)

    def pixmap(self, size, mode, state):
        """生成指定尺寸的 QPixmap（有些场景如 QListView 会调用）"""
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
        painter.end()
        return pixmap

    def clone(self):
        """必须实现，保证 QIcon 复制时引擎也被正确复制"""
        return SvgIconEngine(bytes(self.svg_bytes))

class SvgIconManager(dict):
    def __init__(self, svg_data):
        super().__init__()
        for name, svg_content in svg_data.items():
            self[name] = QIcon(SvgIconEngine(svg_content))

