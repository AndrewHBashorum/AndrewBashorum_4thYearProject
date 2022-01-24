# Author: ANDREW BASHORUM: C00238900
# 4th YEAR PROJECT
import numpy as np
from numpy import linalg as LA
from scipy.spatial import ConvexHull

import json
import pickle
import os
from os import path
from pathlib import Path
import matplotlib.pyplot as plt
import sys
import math
import random
from pathlib import Path
import utils.constants
from pyproj import Proj, transform
from sklearn.linear_model import LinearRegression

if 'lukecoburn' not in str(Path.home()):
    user = 'andrew'
    import pickle5 as pickle
else:
    user = 'luke'
    import pickle


class Geometry(object):
    def __init__(self):
        pass

    def convert_lat_lon_to_27700(self, lat, lon):
        inProj = Proj(init='epsg:4326')
        outProj = Proj(init='epsg:27700')
        return transform(inProj, outProj, lat, lon)

    def convert_27700_to_lat_lon(self, x1, y1):
        inProj = Proj(init='epsg:27700')
        outProj = Proj(init='epsg:4326')
        return transform(inProj, outProj, x1, y1)

    def convert_list_lat_lon_to_27700(self, lat_list, lon_list):
        inProj = Proj(init='epsg:4326')
        outProj = Proj(init='epsg:27700')
        X, Y = [], []
        for p in range(len(lat_list)):
            x_temp, y_temp = transform(inProj, outProj, lat_list[p], lon_list[p])
            X.append(x_temp)
            Y.append(y_temp)
        return X, Y

    def convert_list_27700_to_lat_lon(self, X_list, Y_list):
        inProj = Proj(init='epsg:27700')
        outProj = Proj(init='epsg:4326')
        lat_list, lon_list = [], []
        for p in range(len(X_list)):
            lat_temp, lon_temp = transform(inProj, outProj, X_list[p], Y_list[p])
            lat_list.append(lat_temp)
            lon_list.append(lon_temp)
        return lat_list, lon_list

    def centre_poly(self, x, y):
        cx = sum(x) / max(1, len(x))
        cy = sum(y) / max(1, len(y))

        return cx, cy

    def poly_angles(self, x, y, cx, cy):
        cx = sum(x) / max(1, len(x))
        cy = sum(y) / max(1, len(y))
        return [np.fmod(np.arctan2((y[i] - cy), (x[i] - cx)) + 2 * np.pi, 2 * np.pi) for i in range(len(x))]

    def flip_array(self, x, y):
        x_temp = []
        y_temp = []
        for i in range(len(x)):
            x_temp.append(x[len(x) - (i + 1)])
            y_temp.append(y[len(x) - (i + 1)])
        x = x_temp
        y = y_temp
        return x, y

    def sort_array_acw(self, x, y):
        cx, cy = self.centre_poly(x, y)
        angle = self.poly_angles(x, y, cx, cy)

        cw_acw = 0
        for i in range(len(x)):
            j = (i + 1) % len(x)
            if (angle[j] - angle[i] > 0):
                cw_acw += 1
            else:
                cw_acw -= 1
        if (cw_acw < 0):
            x, y = self.flip_array(x, y)

        return x, y

    def find_area(self, x, y):
        cx = sum(x)/max(len(x), 1)
        cy = sum(y)/max(len(y), 1)
        area = 0
        for i in range(len(x)):
            j = (i + 1) % len(x)
            area += 0.5 * ((x[i] - cx) * (y[j] - cy) - (x[j] - cx) * (y[i] - cy))
        return area

    def get_aspect_ratio_area(self, x, y):
        M = np.zeros((2, 2))
        cx = sum(x) / max(len(x), 1)
        cy = sum(y) / max(len(y), 1)
        area = 0
        for i in range(len(x)):
            i1 = (i + 1) % len(x)
            area += 0.5 * abs((x[i1] - cx) * (y[i] - cy) - (x[i] - cx) * (y[i1] - cy))
            ix = x[i] - cx
            iy = y[i] - cy
            M[0][0] += ix ** 2
            M[1][1] += iy ** 2
            M[0][1] -= ix * iy
            M[1][0] -= ix * iy
        eig = LA.eig(M)[0]
        evec = LA.eig(M)[1]
        if eig[0] > eig[1]:
            v = evec[0]
        else:
            v = evec[1]
        orientation = np.arctan2(v[1], v[0])%np.pi
        evalues = [eig[0].real, eig[1].real]
        evalues = [abs(i) for i in evalues]
        if max(evalues) > 0:
            aspect_ratio = np.sqrt(max(evalues) / min(1, min(evalues)))
        else:
            aspect_ratio = 0
        area = round(100 * area) / 100

        return aspect_ratio, area, orientation

    def point_in_polygon(self, px, py, x, y):
        # returns True if point (px, py) is in polygon (x, y) and False otherwise
        x0, y0 = x[:], y[:]
        c = False
        n = len(x0)
        for i in range(n):
            j = (i - 1) % len(x0)
            if (((y0[i] > py) != (y0[j] > py)) and (
                    px >= ((x0[j] - x0[i]) * (py - y0[i]) / (y0[j] - y0[i])) + x0[i])):
                c = not c
        return c

    def rotate_polygon(self, x, y, alpha):
        x_ = x[:]
        y_ = y[:]
        if len(x) > 0:
            cx, cy = sum(x) / len(x), sum(y) / len(y)
            for i in range(len(x)):
                x[i] = ((x_[i] - cx) * np.cos(alpha) - (y_[i] - cy) * np.sin(alpha)) + cx
                y[i] = ((x_[i] - cx) * np.sin(alpha) + (y_[i] - cy) * np.cos(alpha)) + cy
        return x, y

    def rotate_polygon_alt(self, x, y, alpha):
        x_ = x[:]
        y_ = y[:]
        cx, cy = 0, 0
        for i in range(len(x)):
            x[i] = ((x_[i] - cx) * np.cos(alpha) - (y_[i] - cy) * np.sin(alpha)) + cx
            y[i] = ((x_[i] - cx) * np.sin(alpha) + (y_[i] - cy) * np.cos(alpha)) + cy
        return x, y

    def enlarge_polygon(self, x, y, scale_factor):
        cx, cy = sum(x) / len(x), sum(y) / len(y)
        x_temp, y_temp = [], []
        for i in range(len(x)):
            x_temp.append(scale_factor*(x[i] - cx) + cx)
            y_temp.append(scale_factor*(y[i] - cy) + cy)

        return x_temp, y_temp

    def polygon_in_enlarged_polygon(self, qx, qy, x, y, scale_factor):
        x_temp, y_temp = self.enlarge_polygon(x, y, scale_factor)
        poly_in_poly = True
        for i in range(len(qx)):
            if not self.point_in_polygon(qx[i], qy[i], x_temp, y_temp):
                poly_in_poly = False
        return poly_in_poly

    def antipodal_pairs(self, x0, y0):
        l = []
        n = len(x0)
        p1 = [x0[0], y0[0]]
        p2 = [x0[1], y0[1]]

        t, d_max = None, 0
        for p in range(1, n):
            pn = [x0[p], y0[p]]
            d = self.distance(p1, p2, pn)
            if d > d_max:
                t, d_max = p, d
        l.append(t)

        for p in range(1, n):
            p1 = [x0[p % n], y0[p % n]]
            p2 = [x0[(p + 1) % n], y0[(p + 1) % n]]
            _p = [x0[t % n], y0[t % n]]
            _pp = [x0[(t + 1) % n], y0[(t + 1) % n]]

            while self.distance(p1, p2, _pp) > self.distance(p1, p2, _p):
                t = (t + 1) % n
                _p = [x0[t % n], y0[t % n]]
                _pp = [x0[(t + 1) % n], y0[(t + 1) % n]]
            l.append(t)

        return l

    def parallel_vector(self, a, b, c):
        v0 = [c[0] - a[0], c[1] - a[1]]
        v1 = [b[0] - c[0], b[1] - c[1]]
        return [c[0] - v0[0] - v1[0], c[1] - v0[1] - v1[1]]

    def line_intersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        # finds intersection between lines, given 2 points on each line.
        # (x1, y1), (x2, y2) on 1st line, (x3, y3), (x4, y4) on 2nd line.
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / (
                    (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / (
                    (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
        return px, py

    def compute_parallelogram(self, x, y, l, z1, z2, n):
        # from each antipodal point, draw a parallel vector,
        # so ap1->ap2 is parallel to p1->p2
        #    aq1->aq2 is parallel to q1->q2
        p1 = [x[z1 % n], y[z1 % n]]
        p2 = [x[(z1 + 1) % n], y[(z1 + 1) % n]]
        q1 = [x[z2 % n], y[z2 % n]]
        q2 = [x[(z2 + 1) % n], y[(z2 + 1) % n]]
        ap1 = [x[l[z1 % n]], y[l[z1 % n]]]
        aq1 = [x[l[z2 % n]], y[l[z2 % n]]]
        ap2, aq2 = self.parallel_vector(p1, p2, ap1), self.parallel_vector(q1, q2, aq1)

        a = self.line_intersection(p1[0], p1[1], p2[0], p2[1], q1[0], q1[1], q2[0], q2[1])
        b = self.line_intersection(p1[0], p1[1], p2[0], p2[1], aq1[0], aq1[1], aq2[0], aq2[1])
        d = self.line_intersection(ap1[0], ap1[1], ap2[0], ap2[1], q1[0], q1[1], q2[0], q2[1])
        c = self.line_intersection(ap1[0], ap1[1], ap2[0], ap2[1], aq1[0], aq1[1], aq2[0], aq2[1])
        s = self.distance(a, b, c) * math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

        return s, a, b, c, d

    def distance(self, p1, p2, p):
        denom = math.sqrt((p2[1] - p1[1]) ** 2 + (p2[0] - p1[0]) ** 2)
        if denom > 0.0:
            return abs(((p2[1] - p1[1]) * p[0] - (p2[0] - p1[0]) * p[1] + p2[0] * p1[1] - p2[1] * p1[0]) / denom)
        else:
            return 0

    def minimum_pt_pt_dist(self, x1, y1, x2, y2, min_d):
        for i in range(len(x1)):
            for j in range(len(x2)):
                d = np.sqrt((x1[i] - x2[j])**2 + (y1[i] - y2[j])**2)
                if d < min_d:
                    min_d = d
        return min_d

    def minimum_containing_paralleogram(self, x, y):
        # returns score, area, points from top-left, clockwise , favouring low area

        z1, z2 = 0, 0
        n = len(x)
        points = np.zeros((n, 2))
        for i in range(n):
            points[i, 0] = x[i]
            points[i, 1] = y[i]
        hull = ConvexHull(points)
        xh = []
        yh = []

        for i in hull.vertices:
            xh.append(hull.points[i][0])
            yh.append(hull.points[i][1])

        # for each edge, find antipodal vertice for it (step 1 in paper).
        l = self.antipodal_pairs(xh, yh)
        n = len(xh)
        so, ao, bo, co, do, z1o, z2o = 100000000000, None, None, None, None, None, None

        # step 2 in paper.
        for z1 in range(n):
            if z1 >= z2:
                z2 = z1 + 1
            p1 = [xh[z1 % n], yh[z1 % n]]
            p2 = [xh[(z1 + 1) % n], yh[(z1 + 1) % n]]
            a = [xh[z2 % n], yh[z2 % n]]
            b = [xh[(z2 + 1) % n], yh[(z2 + 1) % n]]
            c = [xh[l[z2 % n]], yh[l[z2 % n]]]

            if self.distance(p1, p2, a) >= self.distance(p1, p2, b):
                continue

            while self.distance(p1, p2, c) > self.distance(p1, p2, b):
                z2 += 1
                a = [xh[z2 % n], yh[z2 % n]]
                b = [xh[(z2 + 1) % n], yh[(z2 + 1) % n]]
                c = [xh[l[z2 % n]], yh[l[z2 % n]]]

            st, at, bt, ct, dt = self.compute_parallelogram(xh, yh, l, z1, z2, n)
            xt = [at[0], bt[0], ct[0], dt[0]]
            yt = [at[1], bt[1], ct[1], dt[1]]
            inside = 1
            for i in range(n):
                ans = self.point_in_polygon(xh[i], yh[i], xt, yt)
                if (ans < 0):
                    inside = 0
            if (st < so) and (inside == 1):
                so, ao, bo, co, do, z1o, z2o = st, at, bt, ct, dt, z1, z2
        x1 = [ao[0], bo[0], co[0], do[0]]
        y1 = [ao[1], bo[1], co[1], do[1]]
        x1, y1 = self.sort_array_acw(x1, y1)

        return 1, x1, y1

    def shift_list(self, seq, n):
        n = n % len(seq)
        return seq[n:] + seq[:n]

    def shift_polygon(self, x, y, dx, dy):
        for i in range(len(x)):
            x[i] += dx
            y[i] += dy
        return x, y

    def linear_regression_to_angle(self, x, y):
        model = LinearRegression().fit(np.array(x).reshape((-1, 1)), np.array(y))
        return np.arctan2(model.coef_[0], 1)

    def get_pts_normals_elevations(self, x, y, x1, y1):
        Pts = []
        Normals = []
        Ele = []
        with open('../../tileSections/Tile_bounds.pickle', 'rb') as f:
            Tile = pickle.load(f)
        tile_ind = []
        for i in range(len(x)):
            for count, tile in enumerate(Tile):
                x_tile, y_tile = tile[0], tile[1]
                if self.point_in_polygon(x[i], y[i], x_tile, y_tile):
                    tile_ind.append(count)
        tile_ind = list(set(tile_ind))

        for tile in tile_ind:
            with open('../tileSections/Tile_-20_7_section_pts_' + str(tile) + '.pickle','rb') as f:
                temp_pts = pickle.load(f)
            with open('../tileSections/Tile_-20_7_section_normals_' + str(tile) + '.pickle','rb') as f:
                temp_normals = pickle.load(f)
            with open('../tileSections/Tile_-20_7_section_ele_' + str(tile) + '.pickle','rb') as f:
                temp_ele = pickle.load(f)

            for i in range(len(temp_pts)):
                p = temp_pts[i]
                e = temp_ele[i]
                n = temp_normals[i]
                l = np.sqrt(n[0]**2 + n[1]**2 + n[2]**2)
                if self.point_in_polygon(p[0], p[1], x, y) and self.point_in_polygon(p[0], p[1], x1, y1) and l > 0.1:
                    Ele.append(e)
                    Pts.append(p)
                    Normals.append(n)

        return Pts, Normals, Ele

    def find_centre(self, x, y):

        g = 0
        for i in x:
            g = g + x
        centreX = g / len(x)

        for i in y:
            f = f + x
        centreY = f / len(x)

        centre = [centreX, centreY]
        return centre

    def split_pts_vertical_and_rest(self, Pts, Ele, Normals, trim, alpha):

        # Points and normals of house
        x_, y_, zl_, zu_, u_, v_, w_ = [], [], [], [], [], [], []
        # Points and normals of flat parts
        xf_, yf_, zf_, uf_, vf_, wf_ = [], [], [], [], [], []
        # print(Pts.size())
        # x, y = self.rotate_polygon(x, y, np.pi / 2 - alpha)

        for i1 in range(int(len(Pts) / trim)):
            i = trim * i1
            px = Pts[i][0]
            py = Pts[i][1]

            if (Normals[i][1]) < 0.9:
                x_.append(Pts[i][0])
                y_.append(Pts[i][1])
                zl_.append(Ele[i])
                zu_.append(Ele[i] + Pts[i][2])
                if Normals[i][1] > 0:
                    u_.append(Normals[i][0])
                    v_.append(Normals[i][1])
                    w_.append(Normals[i][2])
                else:
                    u_.append(-Normals[i][0])
                    v_.append(-Normals[i][1])
                    w_.append(-Normals[i][2])
            else:
                xf_.append(Pts[i][0])
                yf_.append(Pts[i][1])
                zf_.append(Ele[i] + Pts[i][2])
                uf_.append(Normals[i][0])
                vf_.append(Normals[i][1])
                wf_.append(Normals[i][2])

        return x_, y_, zl_, zu_, u_, v_, w_, xf_, yf_, zf_, uf_, vf_, wf_

    def plot_normals_and_colour_map(self, pts, normals, ptsf, normalsf, house_id, img_folder):

        x_, y_, zl_, zu_ = pts[0], pts[1], pts[2], pts[3]
        u_, v_, w_ = normals[0], normals[1], normals[2]
        xf_, yf_, zf_ = ptsf[0], ptsf[1], ptsf[2]
        uf_, vf_, wf_ = normalsf[0], normalsf[1], normalsf[2]
        if len(u_) > 0 or len(uf_) > 0:
            if len(uf_) > 0 and  len(u_) > 0:
                max_u, min_u = max(max(u_), max(uf_)), min(min(u_), min(uf_))
                max_v, min_v = max(max(v_), max(vf_)), min(min(v_), min(vf_))
                max_w, min_w = max(max(w_), max(wf_)), min(min(w_), min(wf_))
            elif len(u_) > 0:
                max_u, min_u = max(u_), min(u_)
                max_v, min_v = max(v_), min(v_)
                max_w, min_w = max(w_), min(w_)
            elif len(uf_) > 0:
                max_u, min_u = max(uf_), min(uf_)
                max_v, min_v = max(vf_), min(vf_)
                max_w, min_w = max(wf_), min(wf_)

            plt.figure()
            plt.axis("off")
            for i in range(len(x_)):
                col = [0.75*(u_[i] - min_u) / (max_u - min_u), 0.75*(v_[i] - min_v) / (max_v - min_v),
                       0.75*(w_[i] - min_w) / (max_w - min_w)]
                plt.scatter(x_[i], y_[i], s=50, color=col)  # s=marker_size,
            for i in range(len(xf_)):
                col = [0.75*(uf_[i] - min_u) / (max_u - min_u), 0.75*(vf_[i] - min_v) / (max_v - min_v),
                       0.75*(wf_[i] - min_w) / (max_w - min_w)]
                plt.scatter(xf_[i], yf_[i], s=50, color=col)
            plt.show()

            im_str = img_folder + '/height_' + str(house_id) + '.png'
            plt.savefig(im_str)
            plt.close("all")

        # plt.savefig('images/vector_images/' + house_name + ".png", format='png', bbox_inches='tight', dpi=300)
        #
        # dx, dy, dz = max(x_) - min(x_), max(y_) - min(y_), max(zu_) - min(zu_)
        # d = max(dx, dy, dz)
        # delta = 2
        # mx, my, mz = 0.5 * (max(x_) + min(x_)), 0.5 * (max(y_) + min(y_)), 0.5 * (max(zu_) + min(zu_))
        #
        # #fig = plt.figure()

    def basic_model_from_height_data(self, x, y, x1, y1, plot_bool, house_id, alpha, img_folder):
        pts, normals, ptsf, normalsf = None, None, None, None
        Pts, Normals, Ele = self.get_pts_normals_elevations(x, y, x1, y1)

        trim = 1
        marker_size = 50
        x_, y_, zl_, zu_, u_, v_, w_, xf_, yf_, zf_, uf_, vf_, wf_ = self.split_pts_vertical_and_rest(Pts, Ele, Normals, trim, alpha)
        del Pts
        del Ele
        del Normals

        # Rotate all height data
        # x, y     = self.rotate_polygon(x,   y,   np.pi/2 - alpha)
        x_, y_   = self.rotate_polygon_alt(x_[:],  y_[:],  np.pi/2 - alpha)
        xf_, yf_ = self.rotate_polygon_alt(xf_[:], yf_[:], np.pi/2 - alpha)
        u_, v_   = self.rotate_polygon(u_[:],  v_[:],  np.pi/2 - alpha)
        uf_, vf_ = self.rotate_polygon(uf_[:], vf_[:], np.pi/2 - alpha)
        pts = [x_, y_, zl_, zu_]
        normals = [u_, v_, w_]
        ptsf = [xf_, yf_, zf_]
        normalsf = [uf_, vf_, wf_]

        if plot_bool:
            self.plot_normals_and_colour_map(pts, normals, ptsf, normalsf, house_id, img_folder)

        # Test v different roof shapes
        # fig = plt.figure()

        # if plot_bool:
        #     fig = plt.figure()
        # roof_shape, roof_ridge = self.default_roof_shapes(x, y)
        # roof_ind = self.simple_alignment_cor_fun(roof_shape, roof_ridge, x_, y_, u_, v_, w_, plot_bool)

        # # Test v different roof shapes
        # X_, Y_, Z_, faces = self.plot_basic_house(x, y, x_, y_, zl_, zu_, roof_shape, roof_ridge, roof_ind, plot_bool)

        return pts, normals, ptsf, normalsf

    def main(self):
        x = [0, 20, 20, 0]
        y = [0, 0, 100, 100]
        print(self.get_aspect_ratio_area(x, y))

if __name__ == '__main__':
    gt = Geometry()
    gt.main()