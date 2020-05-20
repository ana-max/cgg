import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPoint
import math


def f(x):
    return x * math.sin(x * x)


a, b = -5, 5


class IndependentScaleGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setGeometry(250, 150, 600, 480)
        self.setWindowTitle('Function\'s Graphic. Independent Scale')

    def independent_scale(self, qp):
        max_x = self.width()
        max_y = self.height()
        y_min = y_max = f(a)

        for xx in range(max_x):
            x = a + xx * (b - a) / max_x
            y = f(x)
            if y < y_min:
                y_min = y
            if y > y_max:
                y_max = y

        yy = (f(a) - y_min) * max_y / (y_max - y_min)
        previous_point = QPoint(0, yy)

        for xx in range(1, max_x):
            x = a + xx * (b - a) / max_x
            y = f(x)
            yy = (y - y_max) * max_y / (y_min - y_max)
            current_point = QPoint(xx, yy)
            self.draw_lines(qp, previous_point, current_point)
            previous_point = current_point

        if a <= 0:
            xx = abs(a) * max_x / (b - a)
            qp.drawLine(QPoint(xx, 0), QPoint(xx, max_y))
            qp.drawLine(QPoint(xx, 0), QPoint(xx + 5, 10))
            qp.drawLine(QPoint(xx, 0), QPoint(xx - 5, 10))

        yy = (0 - y_max) * max_y / (y_min - y_max)
        qp.drawLine(QPoint(0, yy), QPoint(max_x, yy))
        qp.drawLine(QPoint(max_x, yy), QPoint(max_x - 10, yy - 5))
        qp.drawLine(QPoint(max_x, yy), QPoint(max_x - 10, yy + 5))

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.independent_scale(qp)
        qp.end()

    def draw_lines(self, qp, previous_point, current_point):
        qp.drawLine(previous_point, current_point)


def main():
    app = QApplication(sys.argv)
    independent_scale_graph = IndependentScaleGraph()
    independent_scale_graph.show()
    app.exec_()


if __name__ == '__main__':
    main()