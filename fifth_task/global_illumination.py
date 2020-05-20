from abc import abstractmethod
import numpy as np
import itertools
import math
import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import QPoint

EPS = 0.0001


class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, p):
        return Point(self.x + p.x, self.y + p.y, self.z + p.z)

    def __sub__(self, p):
        return Point(self.x - p.x, self.y - p.y, self.z - p.z)

    def __mul__(self, p):
        return self.x * p.x + self.y * p.y + self.z * p.z

    def vector_on_scalar_mult(self, dot):
        return Point(self.x * dot, self.y * dot, self.z * dot)

    def vector_mul(self, p):
        return Point(self.y * p.z - self.z * p.y, self.z * p.x - self.x * p.z, self.x * p.y - self.y * p.x)

    def __neg__(self):
        return Point(-self.x, -self.y, -self.z)

    def get_length(self):
        return np.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self):
        length = self.get_length()
        if np.abs(length) <= 0.0001:
            length = 1
        return Point(self.x / length, self.y / length, self.z / length)

    def to_rgb(self):
        red_color = int(255 * min(1., max(0., self.x)))
        green_color = int(255 * min(1., max(0., self.y)))
        blue_color = int(255 * min(1., max(0., self.z)))
        return red_color, green_color, blue_color


class Material:
    def __init__(self, refractive: float, diffuse: Point, specular: float, albedo: list, transparency: float):
        self.refractive = refractive
        self.diffuse = diffuse
        self.specular = specular
        self.albedo = albedo
        self.transparency = transparency


# Используемые материалы
green = Material(refractive=1.0,
                 albedo=[1, 0.5],
                 diffuse=Point(0, 0.3, 0),
                 specular=10,
                 transparency=0.2)

red = Material(refractive=1.0,
               albedo=[1, 0.5],
               diffuse=Point(1, 0, 0),
               specular=10,
               transparency=0.0)

white = Material(refractive=1.0,
                 albedo=[1, 0.5],
                 diffuse=Point(1, 1, 1),
                 specular=10,
                 transparency=0.0)

yellow = Material(refractive=1.0,
                  albedo=[1, 0.5],
                  diffuse=Point(1, 1, (102 / 255)),
                  specular=10,
                  transparency=0)

blue = Material(refractive=1.0,
                albedo=[1, 0.5],
                diffuse=Point(0.5, 0.3, 1),
                specular=10,
                transparency=0)

gray = Material(refractive=1.0,
                albedo=[1, 0.5],
                diffuse=Point(0.8, 0.8, 0.8),
                specular=10,
                transparency=0)


class Shape(Point):
    def __init__(self, material: Material):
        self.material = material

    @abstractmethod
    def does_ray_intersect(self, camera: Point, direction: Point) -> (bool, float):
        """ проверка на пересечение с лучом """

    @abstractmethod
    def normal(self, point: Point) -> Point:
        """ получение нормали """

    def get_color(self, point: Point):
        """ получение цвета в точке """
        return self.material.diffuse


class Tracer:
    def __init__(self, camera=Point(0, 0, 0), width=0, height=0, shapes=list(), lights=list(), buffer=list()):
        self.camera: Point = camera
        self.width: int = width
        self.height: int = height
        self.shapes: list = shapes
        self.max_depth: int = 5
        self.background_color = Point(1, 1, 1)

        self.bitmap = list()

        self.lights: list = lights

        self.buffer: list = buffer
        self.x: list = list()
        self.y: list = list()

        self.size: int = max(self.width, self.height)

        for i in range(self.width * self.height):
            self.x.append(float(i % self.width) / self.size - 0.5)
            self.y.append(0.5 - (float(i) / self.width) / self.size)

    def closest_intersection(self, camera: Point, direction: Point, min_dist: float = EPS, max_dist: float = np.inf) \
            -> (Shape, float):
        closest_distance: float = np.inf
        closest_shape: Shape = None

        for shape in self.shapes:
            t = shape.does_ray_intersect(camera=camera, direction=direction)
            if not t[0]:
                continue
            if (t[1] < min_dist) or (t[1] > max_dist) or (t[1] >= closest_distance):
                continue
            closest_distance = t[1]
            closest_shape = shape

        return closest_shape, closest_distance

    def have_intersection(self, camera: Point, direction: Point, min_dist: float = EPS, max_dist: float = np.inf) \
            -> bool:
        for shape in self.shapes:
            t = shape.does_ray_intersect(camera=camera, direction=direction)
            if t[0] and min_dist <= t[1] <= max_dist:
                return True
        return False

    def lighting(self, point: Point, normal: Point, direction: Point, material: Material) -> (float, float):
        diffuse: float = 0.
        specular: float = 0.

        for light in self.lights:
            light_direction: Point = light.position - point
            max_dist: float = light_direction.get_length()
            light_direction = light_direction.normalize()

            if self.have_intersection(camera=point, direction=light_direction, max_dist=max_dist):
                continue

            light_cos: float = light_direction * normal
            diffuse += light_cos * light.intensity

            specular_cos: float = (light_direction - normal.vector_on_scalar_mult(light_cos * 2)) * direction
            specular += np.power(specular_cos, material.specular) * light.intensity

        diffuse *= material.albedo[0]
        specular *= material.albedo[1]

        return diffuse, specular

    def ray(self, camera: Point, direction: Point) -> Point:
        closest_shape, closest_dist = self.closest_intersection(camera=camera, direction=direction)

        if closest_shape is None:
            return self.background_color

        point = direction.vector_on_scalar_mult(closest_dist) + camera
        normal: Point = closest_shape.normal(point)
        material: Material = closest_shape.material

        diffuse, specular = self.lighting(point=point, normal=normal, direction=direction,
                                          material=closest_shape.material)

        diffuse_color = (closest_shape.get_color(point)).vector_on_scalar_mult(diffuse)
        specular_color = Point(specular, specular, specular)
        refraction_color = (self.get_refraction_color(closest_shape, direction, normal, point)) \
            .vector_on_scalar_mult(material.transparency)

        return diffuse_color + specular_color + refraction_color

    def get_refraction_color(self, closest_shape: Shape, direction: Point, normal: Point, point: Point):
        material = closest_shape.material
        refract_direction = self.refract(direction, normal, material.refractive)
        return self.ray(point, refract_direction)

    def refract(self, direction: Point, normal: Point, ior: float):
        scalar = direction.x * normal.x + direction.y * normal.y + direction.z * normal.z
        if scalar > 0:
            return self.refract(direction, normal.vector_on_scalar_mult(-1), ior)
        a = 1 / ior
        D = 1 - a * a * (1 - scalar * scalar)
        b = scalar * a + math.sqrt(D)
        if D > 0:
            return direction.vector_on_scalar_mult(a) - direction.vector_on_scalar_mult(b)

    def trace(self) -> list:
        ray_count = self.width * self.height

        for i in range(ray_count):
            p: Point = Point(self.x[i], self.y[i], 1)
            direction: Point = p.normalize()
            color: Point = self.ray(camera=self.camera, direction=direction)

            self.buffer.append(color.to_rgb())

        index = 0
        for x in range(self.width):
            list_y = list()
            for y in range(self.height):
                color = (int(self.buffer[index][0]),
                         int(self.buffer[index][1]),
                         int(self.buffer[index][2]))
                list_y.append(color)
                index += 1
            self.bitmap.append(list_y)

        return self.bitmap


class Sphere(Shape):
    def __init__(self, center: Point, radius: float, material: Material, eps: float = 0.0001):
        self.eps = eps
        self.center = center
        self.radius = radius
        self.material = material

    def does_ray_intersect(self, camera: Point, direction: Point):
        intersection_point = camera - self.center

        b = intersection_point * direction
        c = intersection_point * intersection_point - self.radius * self.radius
        discriminant = b * b - c
        if discriminant < self.eps:
            res = np.inf
            return False, res
        res = -b - np.sqrt(discriminant)
        if res < self.eps:
            res = -b + np.sqrt(discriminant)

        return res > self.eps, res

    def normal(self, point: Point):
        return (point - self.center).normalize()


class Side(Shape):
    def __init__(self, points: list, material: Material, norm: Point, eps: float = 0.0001):
        self.eps = eps
        self.points = list()
        for p in points:
            self.points.append(Point(p.x, p.y, p.z))
        self.material = material
        self.norm = Point(norm.x, norm.y, norm.z)

    def ray_intersects_triangle(self, camera: Point, direction: Point,
                                p0: Point, p1: Point, p2: Point) -> (bool, float):
        intersect = -1.
        edge1: Point = p1 - p0
        edge2: Point = p2 - p0
        h: Point = direction.vector_mul(edge2)
        a: float = edge1 * h

        if -self.eps < a < self.eps:
            return False, intersect

        f: float = 1. / a

        s: Point = camera - p0
        u: float = s * h * f
        if u < 0 or u > 1:
            return False, intersect

        q: Point = s.vector_mul(edge1)
        v: float = direction * q * f
        if v < 0 or v + u > 1:
            return False, intersect

        t: float = edge2 * q * f

        if t > self.eps:
            intersect = t
            return True, intersect
        else:
            return False, intersect

    def does_ray_intersect(self, camera: Point, direction: Point) -> (bool, float):
        intersect = np.inf
        f = self.ray_intersects_triangle(camera, direction, self.points[0], self.points[1], self.points[3])
        f2 = self.ray_intersects_triangle(camera, direction, self.points[1], self.points[2], self.points[3])
        if f[0] and (intersect == np.inf or f[1] < intersect):
            intersect = f[1]
        elif f2[0] and (intersect == np.inf or f2[1] < intersect):
            intersect = f2[1]
        print(intersect, 'side')
        if intersect != np.inf:
            return True, intersect
        return False, intersect

    def normal(self, point: Point) -> Point:
        return self.norm


class TetrahedronSide(Shape):
    def __init__(self, points: list(), material: Material, eps: float = 0.0001):
        self.eps = eps
        self.points = list()
        for p in points:
            self.points.append(Point(p.x, p.y, p.z))
        self.material = material

    def ray_intersects_triangle(self, camera: Point, direction: Point,
                                p0: Point, p1: Point, p2: Point) -> (bool, float):
        intersect = -1.
        edge1: Point = p1 - p0
        edge2: Point = p2 - p0
        h: Point = direction.vector_mul(edge2)
        a: float = edge1 * h

        if -self.eps < a < self.eps:
            return False, intersect

        f: float = 1. / a

        s: Point = camera - p0
        u: float = s * h * f
        if u < 0 or u > 1:
            return False, intersect

        q: Point = s.vector_mul(edge1)
        v: float = direction * q * f
        if v < 0 or v + u > 1:
            return False, intersect

        t: float = edge2 * q * f

        if t > self.eps:
            intersect = t
            return True, intersect
        else:
            return False, intersect

    def does_ray_intersect(self, camera: Point, direction: Point) -> (bool, float):
        intersect = np.inf
        f = self.ray_intersects_triangle(camera, direction, self.points[0], self.points[1], self.points[2])
        if f[0] and (intersect == np.inf or f[1] < intersect):
            intersect = f[1]
        print(intersect)
        if intersect != np.inf:
            return True, intersect
        return False, intersect

    def normal(self, point: Point) -> Point:
        return self.calc_normal()

    def calc_normal(self) -> Point:
        point1, point2, point3 = self.points
        vx1 = point1.x - point2.x
        vy1 = point1.y - point2.y
        vz1 = point1.z - point2.z

        vx2 = point2.x - point3.x
        vy2 = point2.y - point3.y
        vz2 = point2.z - point3.z
        wrki = math.sqrt(sqr(vy1 * vz2 - vz1 * vy2) + sqr(vz1 * vx2 - vx1 * vz2) + sqr(vx1 * vy2 - vy1 * vx2))
        nx = (vy1 * vz2 - vz1 * vy2) / wrki
        ny = (vz1 * vx2 - vx1 * vz2) / wrki
        nz = (vx1 * vy2 - vy1 * vx2) / wrki
        return Point(nx, ny, nz)


class MainWindow(QWidget):
    def __init__(self, sphere: Sphere, tetrahedron_points: list, width=300, height=300):
        super().__init__()
        self.width = width
        self.height = height
        self.sphere = sphere
        self.tetrahedron_points = tetrahedron_points

        self.shapes = []
        self.lights = []
        self.init_ui()

    def init_ui(self):
        self.setGeometry(250, 150, self.width, self.height)
        self.setWindowTitle('Main Window')

    def build_scene(self):
        self.lights = [Light(intensity=0.8, position=Point(0, 0.4, 1))]
        tetrahedron = list(itertools.combinations(self.tetrahedron_points, 3))
        tetrahedron_sides = [TetrahedronSide(side, yellow) for side in tetrahedron]

        self.shapes = [
            Side([Point(-0.5, -0.5, 4.5),
                  Point(-0.5, 0.5, 4.5),
                  Point(-0.5, 0.5, -4.5),
                  Point(-0.5, -0.5, -4.5)],
                 material=white,
                 norm=Point(1, 0, 0)),

            Side([Point(0.5, -0.5, 4.5),
                  Point(0.5, 0.5, 4.5),
                  Point(0.5, 0.5, -4.5),
                  Point(0.5, -0.5, -4.5)],
                 material=white,
                 norm=Point(-1, 0, 0)),

            Side([Point(0.5, -0.5, 4.5),
                  Point(-0.5, -0.5, 4.5),
                  Point(-0.5, -0.5, -4.5),
                  Point(0.5, -0.5, -4.5)],
                 material=red,
                 norm=Point(0, 1, 0)),

            Side([Point(0.5, 0.5, 4.5),
                  Point(-0.5, 0.5, 4.5),
                  Point(-0.5, 0.5, -4.5),
                  Point(0.5, 0.5, -4.5)],
                 material=blue,
                 norm=Point(0, -1, 0)),

            Side([Point(0.5, 0.5, 3),
                  Point(-0.5, 0.5, 3),
                  Point(-0.5, -0.5, 3),
                  Point(0.5, -0.5, 3)],
                 material=gray,
                 norm=Point(0, 0, -1)),
            self.sphere,
            *tetrahedron_sides
        ]

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.build_scene()
        tracer = Tracer(camera=Point(0, 0, 0), width=self.width, height=self.height,
                        shapes=self.shapes, lights=self.lights)
        tracer.trace()

        bitmap = tracer.bitmap
        for x in range(self.width):
            for y in range(self.height):
                qp.setPen(QPen(QColor(*bitmap[x][y])))
                qp.drawPoint(QPoint(x, y))

        qp.end()


class Light:
    def __init__(self, intensity: float, position: Point):
        self.intensity = intensity
        self.position = position


def sqr(a):
    return a * a


def main():
    app = QApplication(sys.argv)
    tetrahedron_points = [
        Point(0.5, 0.0, 1.5),
        Point(0.5, -0.3, 1.8),
        Point(-0.1, -0.1, 1.5),
        Point(0.5, 0.2, 2)
    ]
    sphere = Sphere(Point(0.3, 0.2, 1), 0.1, green)
    window = MainWindow(sphere=sphere, tetrahedron_points=tetrahedron_points, width=400, height=400)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
