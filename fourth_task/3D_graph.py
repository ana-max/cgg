import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import QPoint, Qt
from collections import namedtuple
import math

Point = namedtuple('Point', 'x y')


def func1(x, y):
    return math.cos(x*y)


class Graph(QWidget):
    def __init__(self, func):
        super().__init__()
        self.init_ui()
        self.function = func
        self.primary_step = 100
        self.secondary_step = self.width() + self.height()
        self.min_x, self.max_x = (0, 0)
        self.min_y, self.max_y = self.min_x, self.max_x
        self.point1 = Point(-3, -3)
        self.point2 = Point(3, 3)

    def init_ui(self):
        self.setGeometry(250, 150, 800, 500)
        self.setWindowTitle('Function\'s Graphic. 3D')
        self.show()

    def draw_graph(self, qp: QPainter):
        self.set_boundaries()
        self.draw_lines_x(qp)
        self.draw_lines_y(qp)

    """
    Перед рисованием необходимо просчитать по сетке 
    диапазон изменения координат в плоскости экрана. 
    """
    def set_boundaries(self):
        for i in range(self.primary_step):
            x = self.x_with_step(i, self.primary_step)
            for j in range(self.secondary_step):
                y = self.y_with_step(j, self.secondary_step)
                self.initialize_horizon(x, y)
        for i in range(self.primary_step):
            y = self.y_with_step(i, self.primary_step)
            for j in range(self.secondary_step):
                x = self.x_with_step(j, self.secondary_step)
                self.initialize_horizon(x, y)

    """
    Непосредственно перед рисованием проводим 
    инициализацию верхнего и нижнего горизонтов.
    """
    def initialize_horizon(self, x, y):
        z = self.function(x, y)
        xx = screen_x(x, y)
        yy = screen_y(x, y, z)
        self.max_x, self.min_x = max(self.max_x, xx), min(self.min_x, xx)
        self.max_y, self.min_y = max(self.max_y, yy), min(self.min_y, yy)

    def draw_lines_x(self, qp: QPainter):
        n = self.width() + 1
        top, bottom = [self.height()] * n, [0] * n
        for i in range(self.primary_step):
            x = self.x_with_step(i, self.primary_step)
            for j in range(self.secondary_step):
                y = self.y_with_step(j, self.secondary_step)
                self.draw_point(x, y, top, bottom, qp)

    def draw_lines_y(self, qp: QPainter):
        n = self.width() + 1
        top, bottom = [self.height()] * n, [0] * n
        for i in range(self.primary_step):
            y = self.y_with_step(i, self.primary_step)
            for j in range(self.secondary_step):
                x = self.x_with_step(j, self.secondary_step)
                self.draw_point(x, y, top, bottom, qp)

    def draw_point(self, x, y, top, bottom, qp: QPainter):
        z = self.function(x, y)
        old_xx = screen_x(x, y)
        old_yy = screen_y(x, y, z)
        xx = round((old_xx - self.min_x) / (self.max_x - self.min_x) * self.width())
        yy = round((old_yy - self.min_y) / (self.max_y - self.min_y) * self.height())
        if yy > bottom[xx]:
            qp.setPen(QPen(Qt.darkBlue))
            qp.drawPoint(QPoint(xx, yy))
            bottom[xx] = yy
        if yy < top[xx]:
            qp.setPen(QPen(Qt.blue))
            qp.drawPoint(QPoint(xx, yy))
            top[xx] = yy

    def x_with_step(self, i, steps):
        return self.point2.x + i * (self.point1.x - self.point2.x) / steps

    def y_with_step(self, j, steps):
        return self.point2.y + j * (self.point1.y - self.point2.y) / steps

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.draw_graph(qp)
        qp.end()


def screen_x(x, y):
    return (y - x) * math.sqrt(3.0)/2


def screen_y(x, y, z):
    return (y + x) / 2 - z


def main():
    app = QApplication(sys.argv)
    graph = Graph(func1)

    app.exec_()


if __name__ == "__main__":
    main()
