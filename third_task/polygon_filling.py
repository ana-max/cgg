import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import QPoint, Qt

from collections import namedtuple
from operator import itemgetter
import copy

StackItem = namedtuple('StackItem', 'y x1 x2 orientation segments')
Point = namedtuple('Point', 'x y')
Segment = namedtuple('Segment', 'p1 p2')
orientation_up = 1
orientation_down = -1


class Figure(QWidget):
    def __init__(self, polygon):
        super().__init__()
        self.init_ui()
        self.polygon = polygon

    def init_ui(self):
        self.setGeometry(250, 150, 1000, 1000)
        self.setWindowTitle('Filling Polygon')
        self.show()

    def draw_polygon(self, qp):
        qp.setPen(QPen(QColor(Qt.black)))

        # Ищем начальную точку - левую верхнюю границу
        first_vertex = Point(*self.find_first_vertex())

        # Ищем начальный отрезок
        segment = self.find_first_segment(first_vertex)
        next_y = first_vertex.y - 1
        # Кладём начальный отрезок в стек с противоположным построению направлением
        segments = list(self.find_segments_with_vertex(first_vertex))
        x1 = min(segment.p1.x, segment.p2.x)
        x2 = max(segment.p1.x, segment.p2.x)
        first_stack_item = StackItem(next_y, x1, x2, orientation_up, segments)
        self.stack.append(first_stack_item)

        current = StackItem(next_y, x1, x2, orientation_down, segments)
        segment = Segment(Point(current.x1, current.y), Point(current.x2, current.y))
        self.draw_new_segment(segment, qp)
        while len(self.stack):
            current = self.find_new_segment(current, qp)
            if not current or current.x1 >= current.x2:
                current = self.stack.pop()
                self.previous_left = ''
                self.previous_right = ''
                self.previous_y = ''
            segment = Segment(Point(current.x1, current.y), Point(current.x2, current.y))
            self.draw_new_segment(segment, qp)
        self.draw_border(qp)

    def draw_new_segment(self, segment, qp):
        q_pen = QPen(QColor(Qt.black))
        qp.drawLine(QPoint(segment.p1.x, segment.p1.y), QPoint(segment.p2.x, segment.p2.y))

    # Поиск нового отрезка
    def find_new_segment(self, last_item: StackItem, qp):
        if not last_item.segments:
            return
        ys = sorted([p[1] for p in self.polygon])
        new_segment = Segment(Point(0, last_item.y + last_item.orientation),
                              Point(1, last_item.y + last_item.orientation))
        a1, b1, c1 = self.find_line_with_two_point(new_segment.p1, new_segment.p2)

        a2, b2, c2 = self.find_line_with_two_point(last_item.segments[0].p1, last_item.segments[0].p2)
        intersection1 = self.find_line_intersection(a1, b1, c1, a2, b2, c2)

        a3, b3, c3 = self.find_line_with_two_point(last_item.segments[1].p1, last_item.segments[1].p2)
        intersection2 = self.find_line_intersection(a1, b1, c1, a3, b3, c3)

        left_x = min(intersection1.x, intersection2.x)
        right_x = max(intersection1.x, intersection2.x)
        result = StackItem(intersection1.y, left_x, right_x, last_item.orientation, last_item.segments)
        if (left_x, intersection1.y) in self.polygon or (right_x, intersection2.y) in self.polygon:
            new_segments = self.find_polygon_border(
                intersection1.y,
                Segment(Point(left_x, intersection1.y), Point(right_x, intersection1.y)),
                last_item.orientation
            )
            if not new_segments:
                return
            result = StackItem(intersection1.y, left_x, right_x, last_item.orientation, new_segments)
        if (self.previous_left, self.previous_y) in self.polygon or \
                (self.previous_right, self.previous_y) in self.polygon:
            self.process_the_border_is_vertex(left_x, right_x, intersection1.y, last_item.orientation, qp)
        if intersection1.y in ys:
            for p in self.polygon:
                if p[1] == intersection1.y:
                    if left_x < p[0] < right_x:
                        result = self.split_to_many_segments(left_x, right_x, intersection1.y,
                                                             last_item.orientation, qp)
        if not result:
            return
        self.previous_left = result.x1
        self.previous_right = result.x2
        self.previous_y = result.y
        return result

    def process_the_border_is_vertex(self, left_x, right_x, y, orientation, qp):
        max_x, min_x = self.get_maxx_minx()
        max_x += 1
        min_x -= 1
        y_line = Segment(Point(min_x, self.previous_y), Point(max_x, self.previous_y))
        intersection_points, points_segment = self.get_all_intersection_points(y_line, orientation)
        intersection_points.sort(key=lambda p: p.x)
        segments = []
        for i in range(len(intersection_points) - 1):
            if i % 2 != 0:
                continue
            segments.append(Segment(intersection_points[i], intersection_points[i + 1]))
        for s in self.used_segments:
            if s in segments:
                segments.remove(s)
        if Segment(Point(self.previous_left, self.previous_y), Point(self.previous_right, self.previous_y)) in segments:
            segments.remove(Segment(Point(self.previous_left, self.previous_y), Point(self.previous_right, self.previous_y)))
        self.draw_new_segment(Segment(Point(self.previous_left, self.previous_y), Point(self.previous_right, self.previous_y)), qp)
        segments_copy = copy.copy(segments)
        for s in segments_copy:
            if left_x <= s.p1.x <= right_x or \
                    right_x <= s.p1.x <= left_x or \
                    left_x <= s.p2.x <= right_x or \
                    right_x <= s.p2.x <= left_x:
                continue
            segments.remove(s)
        to_stack = []
        for s in segments:
            self.draw_new_segment(Segment(Point(s.p1.x, s.p1.y), Point(s.p2.x, s.p2.y)), qp)
            borders = self.find_polygon_border(s.p1.y, Segment(Point(s.p1.x, s.p1.y), Point(s.p2.x, s.p2.y)), -orientation)
            a1, b1, c1 = self.find_line_with_two_point(Point(min_x, s.p1.y - orientation),
                                                       Point(max_x, s.p2.y - orientation))

            a2, b2, c2 = self.find_line_with_two_point(borders[0].p1, borders[0].p2)
            point1 = self.find_line_intersection(a1, b1, c1, a2, b2, c2)

            a3, b3, c3 = self.find_line_with_two_point(borders[1].p1, borders[1].p2)
            point2 = self.find_line_intersection(a1, b1, c1, a3, b3, c3)
            to_stack.append(StackItem(s.p1.y - orientation, point1.x, point2.x, -orientation, borders))
        self.put_segments_in_stack(to_stack, -orientation)

    def find_polygon_border(self, y, segment, orientation):
        y = y + orientation
        max_x, min_x = self.get_maxx_minx()
        max_x += 1
        min_x -= 1
        maxy, miny = self.get_maxy_miny()
        if y <= miny or y >= maxy:
            return
        y_line = Segment(Point(min_x, y), Point(max_x, y))
        intersection_points, points_segment = self.get_all_intersection_points(y_line, orientation)
        intersection_points.sort(key=lambda p: p.x)
        segments = []
        for i in range(len(intersection_points) - 1):
            if i % 2 != 0:
                continue
            segments.append(Segment(intersection_points[i], intersection_points[i + 1]))
        min_s = 100000000
        new_segment = ''
        for s in segments:
            if abs(segment.p1.x - s.p1.x) < min_s:
                min_s = abs(segment.p1.x - s.p1.x)
                new_segment = s
        if new_segment:
            new_borders = [points_segment[(new_segment.p1.x, new_segment.p1.y)],
                           points_segment[(new_segment.p2.x, new_segment.p2.y)]]
            return new_borders

        return

    def put_segments_in_stack(self, segments, orientation):
        for segment in segments:
            if segment not in self.used_segments:
                self.used_segments.append(segment)
                self.stack.append(segment)

    def get_all_intersection_points(self, line, orientation):
        points = []
        points_segment = {}
        a1, b1, c1 = self.find_line_with_two_point(line.p1, line.p2)
        for i in range(len(self.polygon) - 1):
            p1 = Point(*self.polygon[i])
            p2 = Point(*self.polygon[i + 1])
            segment = Segment(p1, p2)
            if self.is_intersection(line, segment):
                a2, b2, c2 = self.find_line_with_two_point(p1, p2)
                point = self.find_line_intersection(a1, b1, c1, a2, b2, c2)
                must_append = self.must_append_in_intersection(point, orientation) if point else ''
                if point and point not in points and must_append == 'Add TWO':
                    points.append(point)
                    points.append(point)
                    points_segment[(point.x, point.y)] = segment
                    continue
                if point and point not in points and must_append:
                    points.append(point)
                    points_segment[(point.x, point.y)] = segment
        p1 = Point(*self.polygon[0])
        p2 = Point(*self.polygon[-1])
        segment = Segment(p1, p2)
        if self.is_intersection(line, segment):
            a2, b2, c2 = self.find_line_with_two_point(p1, p2)
            point = self.find_line_intersection(a1, b1, c1, a2, b2, c2)
            if point and point not in points and self.must_append_in_intersection(point, orientation):
                points.append(point)
                points_segment[(point.x, point.y)] = segment
        return points, points_segment

    def must_append_in_intersection(self, point, orientation):
        if (point.x, point.y) not in self.polygon:
            return True
        index = self.polygon.index((point.x, point.y))
        right_index = (index + 1) % len(self.polygon)
        left_index = index - 1
        left_point = Point(*self.polygon[left_index])
        right_point = Point(*self.polygon[right_index])
        left_diff = point.y - left_point.y
        right_diff = point.y - right_point.y
        if left_diff == 0 and right_diff == 0:
            return False
        if left_diff == 0 or right_diff == 0:
            return True
        left_sign = left_diff / abs(left_diff)
        right_sign = right_diff / abs(right_diff)
        if left_sign == right_sign == orientation:
            return 'Add TWO'
        return left_sign != right_sign

    def split_to_many_segments(self, left_x, right_x, y, orientation, qp):
        max_x, min_x = self.get_maxx_minx()
        max_x += 1
        min_x -= 1
        maxy, miny = self.get_maxy_miny()
        if y <= miny or y >= maxy:
            return
        y_line = Segment(Point(min_x, y), Point(max_x, y))
        intersection_points, points_segment = self.get_all_intersection_points(y_line, -orientation)
        intersection_points.sort(key=lambda p: p.x)

        segments = []
        for i in range(len(intersection_points) - 1):
            if i % 2 != 0:
                continue
            segments.append(Segment(intersection_points[i], intersection_points[i + 1]))
        if len(segments) == 0:
            return
        self.draw_new_segment(Segment(Point(left_x, y), Point(right_x, y)), qp)
        for s in self.used_segments:
            if s in segments:
                segments.remove(s)
        for s in segments:
            if (min(s.p1.x, s.p2.x) < left_x - 1 and max(s.p1.x, s.p2.x) < left_x - 1) or \
                    (max(s.p1.x, s.p2.x) > right_x + 1 and min(s.p1.x, s.p2.x) > right_x + 1):
                segments.remove(s)
        borders = self.find_polygon_border(y, Segment(Point(left_x, y), Point(right_x, y)), orientation)
        a1, b1, c1 = self.find_line_with_two_point(Point(min_x, y + orientation),
                                                   Point(max_x, y + orientation))

        a2, b2, c2 = self.find_line_with_two_point(borders[0].p1, borders[0].p2)
        point1 = self.find_line_intersection(a1, b1, c1, a2, b2, c2)

        a3, b3, c3 = self.find_line_with_two_point(borders[1].p1, borders[1].p2)
        point2 = self.find_line_intersection(a1, b1, c1, a3, b3, c3)
        result = StackItem(y + orientation, point1.x, point2.x, orientation, borders)
        to_stack = []
        for s in segments:
            self.draw_new_segment(Segment(Point(s.p1.x, s.p1.y), Point(s.p2.x, s.p2.y)), qp)
            borders = self.find_polygon_border(s.p1.y, Segment(Point(s.p1.x, s.p1.y), Point(s.p2.x, s.p2.y)),
                                               orientation)
            a1, b1, c1 = self.find_line_with_two_point(Point(min_x, s.p1.y + orientation),
                                                       Point(max_x, s.p2.y + orientation))

            a2, b2, c2 = self.find_line_with_two_point(borders[0].p1, borders[0].p2)
            point1 = self.find_line_intersection(a1, b1, c1, a2, b2, c2)

            a3, b3, c3 = self.find_line_with_two_point(borders[1].p1, borders[1].p2)
            point2 = self.find_line_intersection(a1, b1, c1, a3, b3, c3)
            to_stack_item = StackItem(s.p1.y + orientation, point1.x, point2.x, -orientation, borders)
            if to_stack_item != result:
                to_stack.append(to_stack_item)
                self.draw_new_segment(Segment(Point(s.p1.x, y), Point(s.p2.x, y)), qp)
        self.used_segments.append(result)
        self.put_segments_in_stack(to_stack, orientation)
        return result

    def is_intersection(self, s1, s2):
        v1 = (s2.p2.x - s2.p1.x) * (s1.p1.y - s2.p1.y) - (s2.p2.y - s2.p1.y) * (s1.p1.x - s2.p1.x)
        v2 = (s2.p2.x - s2.p1.x) * (s1.p2.y - s2.p1.y) - (s2.p2.y - s2.p1.y) * (s1.p2.x - s2.p1.x)
        v3 = (s1.p2.x - s1.p1.x) * (s2.p1.y - s1.p1.y) - (s1.p2.y - s1.p1.y) * (s2.p1.x - s1.p1.x)
        v4 = (s1.p2.x - s1.p1.x) * (s2.p2.y - s1.p1.y) - (s1.p2.y - s1.p1.y) * (s2.p2.x - s1.p1.x)
        return (v1 * v2 <= 0) and (v3 * v4 <= 0)

    def get_maxx_minx(self):
        sort_by_x = sorted(self.polygon, key=itemgetter(0))
        max_x = sort_by_x[-1][0]
        min_x = sort_by_x[0][0]
        return max_x, min_x

    def get_maxy_miny(self):
        sort_by_y = sorted(self.polygon, key=itemgetter(1))
        max_y = sort_by_y[-1][1]
        min_y = sort_by_y[0][1]
        return max_y, min_y

    def find_first_segment(self, first_vertex: Point) -> Segment:
        current_y = first_vertex.y
        next_y = current_y - 1
        segments = self.find_segments_with_vertex(first_vertex)
        left_segment = segments[0]
        right_segment = segments[1]
        a1, b1, c1 = self.find_line_with_two_point(left_segment.p1, left_segment.p2)
        a2, b2, c2 = self.find_line_with_two_point(Point(0, next_y), Point(1, next_y))
        a3, b3, c3 = self.find_line_with_two_point(right_segment.p1, right_segment.p2)
        left_intersection = self.find_line_intersection(a1, b1, c1, a2, b2, c2)
        right_intersection = self.find_line_intersection(a2, b2, c2, a3, b3, c3)

        return Segment(left_intersection, right_intersection)

    def find_line_with_two_point(self, p1, p2):
        a = p1.y - p2.y
        b = p2.x - p1.x
        c = p1.x * p2.y - p2.x * p1.y
        return a, b, c

    def find_line_intersection(self, a1, b1, c1, a2, b2, c2):
        delimiter = a1 * b2 - a2 * b1
        if delimiter == 0:
            return
        x = (b1 * c2 - b2 * c1) / delimiter
        y = (c1 * a2 - c2 * a1) / delimiter
        return Point(x, y)

    def find_segments_with_vertex(self, vertex):
        vertex_index = self.polygon.index((vertex.x, vertex.y))
        left_vertex = Point(*self.polygon[vertex_index - 1])
        right_vertex = Point(*self.polygon[vertex_index + 1])

        right_segment = Segment(vertex, right_vertex)
        copy_vertex_index = vertex_index
        while right_vertex.y == vertex.y:
            copy_vertex_index += 1
            if copy_vertex_index == len(self.polygon):
                copy_vertex_index = 0
            right_vertex = Point(*self.polygon[copy_vertex_index])
            right_segment = Segment(right_segment.p2, right_vertex)

        left_segment = Segment(left_vertex, vertex)
        while left_vertex.y == vertex.y:
            vertex_index -= 1
            left_vertex = Point(*self.polygon[vertex_index])
            left_segment = Segment(left_vertex, left_segment.p1)
        return left_segment, right_segment

    def find_first_vertex(self):
        sorted_vertices = self.get_sorted_vertices_by_y()
        return sorted_vertices[0]

    def get_sorted_vertices_by_y(self):
        vertices_copy = copy.deepcopy(self.polygon)
        vertices_copy = sorted(vertices_copy, key=itemgetter(0))
        vertices_copy = sorted(vertices_copy, key=itemgetter(1), reverse=True)
        return vertices_copy

    def draw_border(self, qp: QPainter):
        q_pen = QPen(QColor(Qt.red))
        qp.setPen(q_pen)
        for i in range(len(self.polygon) - 1):
            qp.drawLine(QPoint(*self.polygon[i]), QPoint(*self.polygon[i + 1]))

        qp.drawLine(QPoint(*self.polygon[0]), QPoint(*self.polygon[-1]))

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.previous_left = ''
        self.previous_right = ''
        self.previous_y = ''
        self.used_segments = []
        self.stack = []
        self.draw_polygon(qp)

        qp.end()

def main():
    app = QApplication(sys.argv)

    vertices = [
        (10, 10), (10, 30), (20, 40), (30, 30),
        (50, 60), (80, 30), (50, 10), (40, 20)
    ]
    graph = Figure(vertices)

    vertices1 = [
        (10, 10), (50, 50), (100, 10)
    ]
    graph1 = Figure(vertices1)

    vertices2 = [
        (100, 150), (150, 200), (200, 150), (150, 110)
    ]
    graph2 = Figure(vertices2)

    vertices3 = [
        (100, 100), (100, 140), (100, 190), (140, 190), (110, 170),
        (140, 130), (150, 160), (170, 130), (220, 170),
        (240, 130), (140, 50)
    ]
    graph3 = Figure(vertices3)

    vertices4 = [
        (10, 100), (40, 140), (40, 170), (190, 170), (190, 140),
        (160, 100), (80, 80), (150, 100), (140, 160), (40, 100),
        (90, 120), (40, 70), (10, 70)
    ]
    graph4 = Figure(vertices4)

    vertices5 = [
        (10, 10), (20, 20), (100, 10), (400, 200), (500, 200),
        (550, 180), (450, 400), (100, 100), (50, 300)
    ]
    graph5 = Figure(vertices5)

    vertices6 = [
        (90, 90), (120, 100), (100, 130), (120, 150), (100, 200), (210, 210), (200, 120),
        (350, 120), (400, 350), (200, 360), (190, 300),
        (110, 370), (100, 290), (90, 210)
    ]
    graph6 = Figure(vertices6)

    vertices7 = [
        (110, 10), (200, 10), (200, 100), (510, 100),
        (510, 350), (410, 200), (200, 200),
        (200, 300), (110, 300), (110, 200), (50, 200),
        (50, 100), (110, 100)
    ]
    graph7 = Figure(vertices7)

    vertices8 = [
        (200, 0), (300, 0), (300, 100), (600, 100), (600, 200),
        (325, 200), (325, 300),
        (600, 300), (600, 350), (500, 350), (500, 375),
        (400, 375), (400, 350), (75, 350),
        (75, 400), (0, 400), (0, 300), (200, 300), (200, 200),
        (0, 200), (0, 100), (200, 100)
    ]
    graph8 = Figure(vertices8)

    vertices9 = [
        (150, 75), (300, 75), (400, 150), (525, 150),
        (525, 250), (400, 250),
        (300, 325), (150, 325), (75, 250), (75, 150)
    ]
    graph9 = Figure(vertices9)

    vertices10 = [
        (100, 25), (200, 75), (400, 75), (500, 25), (500, 175),
        (400, 125),
        (350, 125), (550, 325), (400, 325), (325, 250),
        (325, 325), (250, 325),
        (250, 250), (175, 325), (50, 325), (250, 125),
        (200, 125), (100, 175)
    ]
    graph10 = Figure(vertices10)

    vertices11 = [
        (225, 275), (150, 250), (150, 175), (300, 175),
        (300, 250), (225, 275),
        (275, 225), (175, 225), (225, 275)
    ]
    graph11 = Figure(vertices11)

    app.exec_()


if __name__ == '__main__':
    main()
