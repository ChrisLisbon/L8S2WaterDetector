#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 11:42:40 2020

@author: julia
"""

import os
import gdal
import numpy as np
from primary_functions import save_array_as_gtiff

class IndicesCalculator:
    def __init__(self, images_collection_dir):
        self.images_collection_dir=images_collection_dir        
        files_names=os.listdir(self.images_collection_dir)
        for file in files_names:
            if 'b3' in file.lower().split('.')[0].split('_'):
                self.band_B3=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B3_GREEN: '+file)
            if 'b4' in file.lower().split('.')[0].split('_'):
                self.band_B4=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B4_RED: '+file)
            if 'b5' in file.lower().split('.')[0].split('_'):
                self.band_B5=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B5_NIR: '+file)
            if 'b6' in file.lower().split('.')[0].split('_'):
                self.band_B6=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B6_MIR: '+file)
            if 'b7' in file.lower().split('.')[0].split('_'):
                self.band_B7=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B7SWIR: '+file)
        
    def get_NDVI_as_array(self):
        RED=self.band_B4.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        a=NIR-RED
        b=RED+NIR
        NDVI_array=np.divide(a,b)
        RED=None
        NIR=None
        a=None
        b=None
        return NDVI_array
        NDVI_array=None
    def get_NDWI_as_array(self):
        GREEN=self.band_B3.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        a=GREEN-NIR
        b=GREEN+NIR
        NDWI_array=np.divide(a,b)
        GREEN=None
        NIR=None
        a=None
        b=None
        return NDWI_array  
        NDWI_array=None
    def get_MNDWI_as_array(self):
        GREEN=self.band_B3.GetRasterBand(1).ReadAsArray()
        MIR=self.band_B6.GetRasterBand(1).ReadAsArray()
        a=GREEN-MIR
        b=GREEN+MIR
        MNDWI_array=np.divide(a,b)
        return MNDWI_array
    def get_WRI_as_array(self):
        GREEN=self.band_B3.GetRasterBand(1).ReadAsArray()
        RED=self.band_B4.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        MIR=self.band_B6.GetRasterBand(1).ReadAsArray()
        a=GREEN+RED
        GREEN=None
        RED=None        
        b=NIR+MIR
        NIR=None
        MIR=None
        WRI_array=np.divide(a,b)      
        a=None
        b=None
        return WRI_array
        WRI_array=None
    def get_AWEI_as_array(self):
        GREEN=self.band_B3.GetRasterBand(1).ReadAsArray()
        MIR=self.band_B6.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        SWIR=self.band_B7.GetRasterBand(1).ReadAsArray()
        a=GREEN-MIR
        GREEN=None
        MIR=None
        b=NIR*0.25
        NIR=None
        c=SWIR*2.75
        SWIR=None
        d=b+c
        e=a*4
        AWEI_array=e-d
        a=None
        b=None
        c=None
        d=None
        e=None
        return AWEI_array
    def save_indices(self, output_folder):
        array=self.get_NDVI_as_array()
        save_array_as_gtiff(array, output_folder+'/NDVI.tif', dataset=self.band_B5)
        array=self.get_NDWI_as_array()
        save_array_as_gtiff(array, output_folder+'/NDWI.tif', dataset=self.band_B5)
        array=self.get_MNDWI_as_array()
        save_array_as_gtiff(array, output_folder+'/MNDWI.tif', dataset=self.band_B5)
        array=self.get_WRI_as_array()
        save_array_as_gtiff(array, output_folder+'/WRI.tif', dataset=self.band_B5)
        array=self.get_AWEI_as_array()
        save_array_as_gtiff(array, output_folder+'/AWEI.tif', dataset=self.band_B5)
        array=None
        