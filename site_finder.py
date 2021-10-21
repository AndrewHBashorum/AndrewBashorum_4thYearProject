# Author: ANDREW BASHORUM: C00238900
# 4th YEAR PROJECT
from geopy.geocoders import GoogleV3
from pyproj import Proj, transform
# from pyproj import Transformer
import os
from os import path
import sys
from pathlib import Path
import psycopg2
import geometry as geo
import matplotlib.pyplot as plt
import time
import pickle5 as pickle
from houses import Houses
from sites import Sites
from geometry import Geometry
import warnings
from datetime import date
warnings.filterwarnings("ignore", category=DeprecationWarning)
class SiteFinder(object):

    def __init__(self):

        self.houses = Houses()
        self.sites = Sites()
        self.gt = Geometry()
        pass

    def plotter(self):

        for i in self.sites.dict.keys():
            for g in self.sites.dict[i]['neigh_sites']:
                if g != []:
                    x_temp = []
                    y_temp = []
                    for i in range(0, len(g), 2):
                        x_temp.append(g[i])
                        y_temp.append(g[i+1])
                    aspect_ratio, area = self.gt.get_aspect_ratio_area(x_temp, y_temp)
                    print(aspect_ratio, area)
                    if area < 1000:
                        plt.fill(x_temp, y_temp, '--', fill=False, color='g')

        for i in range(len(self.sites.dict)):
            if self.sites.dict[i]['area'] < 1000:
                plt.plot(self.sites.dict[i]['x'], self.sites.dict[i]['y'], 'o', color='r')
                plt.fill(self.sites.dict[i]['x_poly'], self.sites.dict[i]['y_poly'], fill=False, color='b')



    def get_house_dict(self):

        #self.houses.get_houses_os_walk()

        self.houses.sample_house()
        self.houses.geo_locate_houses()

    def checkSitesForDupes(self, geom):

        site_id = None
        for site in self.sites.dict.keys():
            if self.sites.dict[site]['geom'] == geom:
                site_id = site

        return site_id

    def main(self):

        self.get_house_dict()

        for house_ID in self.houses.house_dict.keys():

            self.sites.take_from_database(self.houses.house_dict[house_ID]['Point_original_x'],self.houses.house_dict[house_ID]['Point_original_y'],self.houses.house_dict[house_ID]['Point_converted_x'],self.houses.house_dict[house_ID]['Point_converted_y'],house_ID)
            #self.sites.find_neighs()
            self.sites.nearby_polygons(self.houses.house_dict[house_ID]['Point_original_x'], self.houses.house_dict[house_ID]['Point_original_y'])
            self.sites.geometry = self.sites.process_geometry(str(self.sites.geom))

            dupeSiteFound_id = self.checkSitesForDupes(self.sites.geometry)
            if dupeSiteFound_id != None:
                print('>>><>', dupeSiteFound_id)
                self.sites.dict[dupeSiteFound_id]['multi_house'] = True
                self.sites.dict[dupeSiteFound_id]['house_address_list'].append(house_ID)
                self.houses.house_dict[house_ID]['sites'].append(dupeSiteFound_id)
            else:
                self.sites.add_to_site_list(self.sites.geometry)
                self.houses.house_dict[house_ID]['sites'].append(self.sites.id)


            for g in self.sites.neigh_geometry:
                self.sites.dict[self.sites.id]['neigh_sites'].append(self.sites.process_geometry(g[0]))
            if dupeSiteFound_id == None:
                self.sites.incrementID()

        self.sites.con.close()
        self.plotter()


if __name__ == '__main__':

    sf = SiteFinder()
    sf.main()

    date = today = date.today()
    dict = {
        'date':date,
        'sf':sf
    }
    #
    # with open('site_finder.pickle', 'wb') as f:
    #     pickle.dump(dict, f)

    # for i in self.sites.dict.keys():
    #     if self.sites.dict[i]['multi_house'] == True:# sel  self.sites.incrementID()
    #         for address in self.sites.dict[i]['house_address_list']:
    #             splitAdress = address.split('_')
    #             number = int(splitAdress[0])
    #             # self.houses.house_dict[address]['potential_neighs'].append(str(number + 2) + '_' + splitAdress[1] + '_' + splitAdress[2])
    #             # self.houses.house_dict[address]['potential_neighs'].append(str(number - 2) + '_' + splitAdress[1] + '_' + splitAdress[2])
    #             # self.houses.house_dict[address]['potential_neighs'].append(str(number + 4) + '_' + splitAdress[1] + '_' + splitAdress[2])
    #             # self.houses.house_dict[address]['potential_neighs'].append(str(number - 4) + '_' + splitAdress[1] + '_' + splitAdress[2])
    #
    #         print(self.sites.dict[i]['id'])
