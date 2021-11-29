import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
from geometry import Geometry

class HouseFinder(object):
    def __init__(self, tolerance):
        self.gt = Geometry()
        self.tolerance = tolerance
        self.cur_dir = os.path.dirname(os.path.realpath(__file__))

    def load_from_pickle(self, pickle_file):
        with open(pickle_file, 'rb') as f:
            loadedDict = pickle.load(f)
        self.site_dict = loadedDict['site_dict']
        self.neigh_site_dict = loadedDict['neigh_site_dict']
        self.house_dict = loadedDict['house_dict']
        self.site_keys = list(self.site_dict.keys())
        self.house_keys = list(self.house_dict.keys())


    def save_to_pickle(self, pickle_file):
        dict = {
            'house_dict': self.house_dict,
            'site_dict': self.site_dict,
            'neigh_site_dict': self.neigh_site_dict
        }
        with open(pickle_file, 'wb') as f:
            pickle.dump(dict, f)

    def run_shell_script_to_find_house_bounds(self, site_id):
        xt = self.site_dict[site_id].xt
        yt = self.site_dict[site_id].yt
        x_poly = self.site_dict[site_id].x_poly
        y_poly = self.site_dict[site_id].y_poly

        # fig = plt.figure()
        command = '/Applications/QGIS-LTR.app/Contents/MacOS/bin/./run.sh'
        command += str(' ') + str(xt)
        command += str(' ') + str(yt)
        command += str(' ') + str(self.tolerance)
        os.system(command)

        file = open(self.cur_dir + "/temp.pickle", 'rb')
        dict = pickle.load(file)
        X_buildings, Y_buildings = dict['X'], dict['Y']
        X_temp, Y_temp, A_temp = [], [], []
        for i in range(len(X_buildings)):
            if self.gt.polygon_in_enlarged_polygon(X_buildings[i], Y_buildings[i], x_poly, y_poly, 1.2):
                X_temp.append(X_buildings[i])
                Y_temp.append(Y_buildings[i])
                A_temp.append(abs(self.gt.find_area(X_buildings[i], Y_buildings[i])))
        largest_area = max(A_temp)
        index_of_largest = A_temp.index(largest_area)
        X_main, Y_main, X_extra, Y_extra = X_temp, Y_temp, [], []
        if len(A_temp) == 1:
            X_main, Y_main = X_temp[0], Y_temp[0]
        elif len(A_temp) > 1:
            largest_area = max(A_temp)
            index_of_largest = A_temp.index(largest_area)
            X_main, Y_main = X_temp[index_of_largest], Y_temp[index_of_largest]
            for i in range(len(X_temp)):
                if i != index_of_largest:
                    X_extra.append(X_temp[i])
                    Y_extra.append(Y_temp[i])
        if type(X_main[0]) is list:
            X_main, Y_main = X_main[0], Y_main[0]
        self.site_dict[site_id].X_main = X_main
        self.site_dict[site_id].Y_main = Y_main
        self.site_dict[site_id].X_extra = X_extra
        self.site_dict[site_id].Y_extra = Y_extra
        if type(self.site_dict[site_id].house_address_list) is list:
            house_address = self.site_dict[site_id].house_address_list[0]
        elif type(self.site_dict[site_id].house_address_list) is str:
            house_address = self.site_dict[site_id].house_address_list
        self.house_dict[house_address].X_bounds = X_main
        self.house_dict[house_address].Y_bounds = Y_main

        self.make_plot_single_site_and_house(xt, yt, x_poly, y_poly, X_main, Y_main, X_extra, Y_extra, X_buildings, Y_buildings)

    def make_plot_single_site_and_house(self, xt, yt, x_poly, y_poly, X_main, Y_main, X_extra, Y_extra, X_buildings, Y_buildings):
        plt.figure()
        # Make plot
        plt.plot(xt, yt, 'x')
        plt.fill(x_poly, y_poly, color='b', linewidth=2, fill=False)
        plt.fill([xt - self.tolerance, xt + self.tolerance, xt + self.tolerance, xt - self.tolerance],
                 [yt - self.tolerance, yt - self.tolerance, yt + self.tolerance, yt + self.tolerance], color='orange', fill=False)
        plt.fill(X_main, Y_main, color='lightgreen', linewidth=3)
        for i in range(len(X_extra)):
            plt.fill(X_extra[i], Y_extra[i], color='r', fill=False, linewidth=2)
        for i in range(len(X_buildings)):
            plt.fill(X_buildings[i], Y_buildings[i], color='c', fill=False, linewidth=1)

    def make_plot(self):
        pass

if __name__ == '__main__':

    hf = HouseFinder(20)
    # load all sites and houses from pickle
    pickle_file_name = 'site_finder_lynmouth_odd'
    hf.load_from_pickle(pickle_file_name + '.pickle')
    for site_id in hf.site_keys:
    # site_id = 2
        print(site_id)
        hf.run_shell_script_to_find_house_bounds(site_id)
    hf.save_to_pickle(pickle_file_name + '1.pickle')

    # go through sites and get site centre and bounds and house address id
    # run shell script and retrieve buildings inside site
    # find biggest one and assign the bounds to house_dict
    # find centre of house bounds and change in house dict objects
    # find centre of site bounds and change in site dict objects
    # make convex rectangular hull around the site and find front and correct orientation vector
    # break rectangular hull into front, back, right, left
    # repeat for house
    # save pickle file again

