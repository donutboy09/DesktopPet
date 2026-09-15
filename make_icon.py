import os
import subprocess
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
S = 1024


def render_icon():
    pm = QPixmap(S, S)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    bg = QPainterPath()
    bg.addRoundedRect(QRectF(24, 24, S - 48, S - 48), 224, 224)
    grad = QLinearGradient(0, 24, 0, S - 24)
    grad.setColorAt(0.0, QColor("#FFD08A"))
    grad.setColorAt(0.55, QColor("#F7A93C"))
    grad.setColorAt(1.0, QColor("#E8890F"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(grad)
    p.drawPath(bg)

    p.save()
    p.translate(0, 14)
    p.setBrush(QColor(140, 70, 0, 45))
    for (cx, cy, rx, ry) in PAW:
        p.drawEllipse(QPointF(cx, cy), rx, ry)
    p.restore()

    p.setBrush(QColor("#FFFFFF"))
    for (cx, cy, rx, ry) in PAW:
        p.drawEllipse(QPointF(cx, cy), rx, ry)

    p.end()
    return pm


PAW = [
    (277, 417, 52, 66),
    (427, 322, 55, 68),
    (597, 322, 55, 68),
    (747, 417, 52, 66),
    (512, 655, 215, 185),
]

pm = render_icon()
png_path = os.path.join(ROOT, "icon.png")
pm.save(png_path)

img = Image.open(png_path).convert("RGBA")
img.save(os.path.join(ROOT, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

iconset = os.path.join(ROOT, "icon.iconset")
os.makedirs(iconset, exist_ok=True)
for size in (16, 32, 64, 128, 256, 512):
    img.resize((size, size), Image.LANCZOS).save(os.path.join(iconset, f"icon_{size}x{size}.png"))
    img.resize((size * 2, size * 2), Image.LANCZOS).save(os.path.join(iconset, f"icon_{size}x{size}@2x.png"))
subprocess.run(["iconutil", "-c", "icns", iconset, "-o", os.path.join(ROOT, "icon.icns")], check=True)

preview = Image.new("RGBA", (420, 140), (245, 245, 248, 255))
x = 10
for size in (128, 64, 32, 16):
    preview.paste(img.resize((size, size), Image.LANCZOS), (x, 70 - size // 2), img.resize((size, size), Image.LANCZOS))
    x += size + 14
preview.save(os.path.join(ROOT, "screenshots", "icon_preview.png"))
print("icon.png / icon.ico / icon.icns written")
