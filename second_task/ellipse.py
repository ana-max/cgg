import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPoint
import math


class Ellipse(QWidget):
    def __init__(self, a, b, c):
        super().__init__()
        self.init_ui()
        self.a = a
        self.b = b
        self.c = c

    def init_ui(self):
        self.setGeometry(250, 150, 600, 480)
        self.setWindowTitle('Function\'s Graphic. Ellipse')

    def rotate_x(self, x, y):
        return x + y

    def rotate_y(self, x, y):
        return -x + y

    def draw_ellipse(self, qp):
        a, b, c = self.a, self.b, self.c
        c_sq = c * c
        a_sq = (a*c_sq + b*c_sq)/(16*a*b*b)
        b_sq = (a*c_sq + b*c_sq)/(16*a*a*b)
        dx = c / (4*b)
        dy = c / (4*a)
        x = 0
        y = -math.sqrt(b_sq)
        delta = a_sq + b_sq - 2*a_sq*b
        while y <= 0:
            qp.drawPoint(QPoint(150 + self.rotate_x(dx + x, dy + y), 350 + self.rotate_y(dx + x, dy + y)))
            qp.drawPoint(QPoint(150 + self.rotate_x(dx + x, dy - y), 350 + self.rotate_y(dx + x, dy - y)))
            qp.drawPoint(QPoint(150 + self.rotate_x(dx - x, dy + y), 350 + self.rotate_y(dx - x, dy + y)))
            qp.drawPoint(QPoint(150 + self.rotate_x(dx - x, dy - y), 350 + self.rotate_y(dx - x, dy - y)))
            if delta < 0:
                if 2 * (delta - a_sq*y) > a_sq:
                    y += 1
                    delta += a_sq*(2*y + 1)
                x += 1
                delta += b_sq*(2*x+1)
            else:
                if 2 * (delta - b_sq * x) < b_sq:
                    x += 1
                    delta += b_sq*(2*x + 1)
                y += 1
                delta += a_sq * (2 * y + 1)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.draw_ellipse(qp)
        qp.end()

    def draw_lines(self, qp, previous_point, current_point):
        qp.drawLine(previous_point, current_point)


def main():
    app = QApplication(sys.argv)
    ellipse = Ellipse(-10, -30, 2000)
    ellipse.show()
    app.exec_()


if __name__ == '__main__':
    main()