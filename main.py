import sys
from PySide6.QtCore import Qt, QPointF, QRectF, QLineF
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF, QImage, QAction
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsLineItem, QToolBar, QFileDialog)

# (المفتاح, الاسم, العرض, الارتفاع)
ELEMENTS = [
    ("car", "سيارة", 60, 30),
    ("bus", "حافلة", 120, 36),
    ("tree", "شجرة", 40, 40),
    ("roundabout", "محور دوران", 120, 120),
    ("sidewalk", "رصيف", 160, 26),
    ("pole", "عمود", 14, 14),
    ("building", "مبنى", 120, 90),
    ("sign", "إشارة طريق", 32, 32),
]


class ElementItem(QGraphicsItem):
    def __init__(self, kind, w, h):
        super().__init__()
        self.kind, self.w, self.h = kind, w, h
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setTransformOriginPoint(w / 2, h / 2)

    def boundingRect(self):
        return QRectF(-2, -2, self.w + 4, self.h + 4)

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing)
        w, h, k = self.w, self.h, self.kind
        r = QRectF(0, 0, w, h)
        border = QPen(Qt.black, 1.5)

        if k == "car":
            p.setPen(border)
            p.setBrush(QColor("#d32f2f"))
            p.drawRoundedRect(r, 8, 8)
            p.setBrush(QColor("#90caf9"))
            p.drawRect(QRectF(w * 0.45, 4, w * 0.25, h - 8))
        elif k == "bus":
            p.setPen(border)
            p.setBrush(QColor("#fbc02d"))
            p.drawRoundedRect(r, 4, 4)
            p.setBrush(QColor("#90caf9"))
            seg = (w - 16) / 5
            for i in range(5):
                p.drawRect(QRectF(8 + i * seg, 5, seg - 4, h - 10))
        elif k == "tree":
            p.setPen(QPen(Qt.black, 1))
            p.setBrush(QColor("#2e7d32"))
            p.drawEllipse(r)
        elif k == "roundabout":
            p.setPen(QPen(QColor("#616161"), 3))
            p.setBrush(QColor("#9e9e9e"))
            p.drawEllipse(r)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#66bb6a"))
            p.drawEllipse(r.adjusted(w * 0.3, h * 0.3, -w * 0.3, -h * 0.3))
        elif k == "sidewalk":
            p.setPen(border)
            p.setBrush(QColor("#bdbdbd"))
            p.drawRect(r)
            p.setPen(QPen(QColor("#757575"), 1))
            for x in range(10, int(w), 10):
                p.drawLine(QLineF(x, 0, x, h))
        elif k == "pole":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#424242"))
            p.drawEllipse(r)
        elif k == "building":
            p.setPen(border)
            p.setBrush(QColor("#8d6e63"))
            p.drawRect(r)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffee58"))
            for row in range(2):
                for col in range(3):
                    p.drawRect(QRectF(12 + col * (w - 24) / 3, 12 + row * (h - 24) / 2, 14, 14))
        elif k == "sign":
            p.setPen(QPen(Qt.white, 2))
            p.setBrush(QColor("#d50000"))
            p.drawPolygon(QPolygonF([QPointF(w / 2, 2), QPointF(w - 2, h - 2), QPointF(2, h - 2)]))


class LaneLine(QGraphicsLineItem):
    def __init__(self, line, dashed):
        super().__init__(line)
        pen = QPen(QColor("white"), 3)
        pen.setStyle(Qt.DashLine if dashed else Qt.SolidLine)
        self.setPen(pen)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)


class DiagramView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QColor("#4a4a4a"))
        self.setFocusPolicy(Qt.StrongFocus)
        self.line_mode = None  # None | "dashed" | "solid"
        self._drawing = None
        self._start = None

    def mousePressEvent(self, e):
        if self.line_mode and e.button() == Qt.LeftButton:
            self._start = self.mapToScene(e.position().toPoint())
            self._drawing = LaneLine(QLineF(self._start, self._start), self.line_mode == "dashed")
            self.scene().addItem(self._drawing)
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drawing:
            pos = self.mapToScene(e.position().toPoint())
            self._drawing.setLine(QLineF(self._start, pos))
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._drawing:
            if self._drawing.line().length() < 5:
                self.scene().removeItem(self._drawing)
            self._drawing = None
        else:
            super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for it in self.scene().selectedItems():
                self.scene().removeItem(it)
        elif e.key() == Qt.Key_R:
            for it in self.scene().selectedItems():
                if isinstance(it, ElementItem):
                    it.setRotation((it.rotation() + 15) % 360)
        else:
            super().keyPressEvent(e)

    def wheelEvent(self, e):
        factor = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مخطط حوادث المرور")
        self.resize(1200, 800)

        self.scene = QGraphicsScene(-3000, -3000, 6000, 6000)
        self.view = DiagramView(self.scene)
        self.setCentralWidget(self.view)

        tb = QToolBar("أدوات")
        tb.setMovable(False)
        self.addToolBar(tb)

        for kind, label, w, h in ELEMENTS:
            self._action(tb, label, lambda _=False, k=kind, ww=w, hh=h: self.add_element(k, ww, hh))

        tb.addSeparator()
        self.line_actions = {}
        for label, mode in [("خط متقطع", "dashed"), ("خط متصل", "solid")]:
            act = QAction(label, self, checkable=True)
            act.triggered.connect(lambda checked, m=mode: self.toggle_line(m, checked))
            tb.addAction(act)
            self.line_actions[mode] = act

        tb.addSeparator()
        self._action(tb, "تدوير (R)", self.rotate_selected)
        self._action(tb, "حذف (Del)", self.delete_selected)
        self._action(tb, "تصدير PNG", self.export_png)

    def _action(self, tb, text, slot):
        act = QAction(text, self)
        act.triggered.connect(slot)
        tb.addAction(act)

    def add_element(self, kind, w, h):
        item = ElementItem(kind, w, h)
        center = self.view.mapToScene(self.view.viewport().rect().center())
        item.setPos(center.x() - w / 2, center.y() - h / 2)
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)

    def toggle_line(self, mode, checked):
        for m, a in self.line_actions.items():
            a.setChecked(checked and m == mode)
        self.view.line_mode = mode if checked else None

    def rotate_selected(self):
        for it in self.scene.selectedItems():
            if isinstance(it, ElementItem):
                it.setRotation((it.rotation() + 15) % 360)

    def delete_selected(self):
        for it in self.scene.selectedItems():
            self.scene.removeItem(it)

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "حفظ الرسم", "schema.png", "PNG (*.png)")
        if not path:
            return
        rect = self.scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
        if rect.isEmpty():
            rect = QRectF(0, 0, 800, 600)
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(QColor("#4a4a4a"))
        painter = QPainter(image)
        self.scene.render(painter, QRectF(image.rect()), rect)
        painter.end()
        image.save(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

