from PyQt6.QtGui import QPainter, QFont, QImage, QColor
from PyQt6.QtCore import QRectF, Qt
import sys

def test_emoji():
    try:
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        painter = QPainter(img)
        painter.setFont(QFont("Segoe UI Emoji", 14))
        # Try some common workflow emojis
        painter.drawText(QRectF(0,0,100,100), Qt.AlignmentFlag.AlignCenter, "⚙️")
        painter.drawText(QRectF(0,0,50,50), Qt.AlignmentFlag.AlignCenter, "\ud83d\uddd1")
        painter.end()
        print("Emoji rendering OK")
    except Exception as e:
        print(f"Emoji rendering CRASH: {e}")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    test_emoji()
