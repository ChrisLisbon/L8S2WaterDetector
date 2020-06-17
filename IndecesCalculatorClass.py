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
FMASK_EXECUTABLE_PATH = 'fmask_usgsLandsatStacked.py'

class IndecesCalculator:
    def __init__(self, images_collection_dir, srem_usgs_util_path=None):
        self.images_collection_dir=images_collection_dir        
        files_names=os.listdir(self.images_collection_dir)
        for file in files_names:
            if 'b1' in file.lower().split('.')[0].split('_'):
                self.band_B1=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B1: '+file)
            if 'b2' in file.lower().split('.')[0].split('_'):
                self.band_B2=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B2: '+file)
            if 'b3' in file.lower().split('.')[0].split('_'):
                self.band_B3=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B3: '+file)
            if 'b4' in file.lower().split('.')[0].split('_'):
                self.band_B4=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B4: '+file)
            if 'b5' in file.lower().split('.')[0].split('_'):
                self.band_B5=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B5: '+file)
            if 'b6' in file.lower().split('.')[0].split('_'):
                self.band_B6=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B6: '+file)
            if 'b7' in file.lower().split('.')[0].split('_'):
                self.band_B7=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('band_B7: '+file)
            if 'ang' in file.lower().split('.')[0].split('_'):
                self.ANG_file=os.path.join(self.images_collection_dir, file)
                print('ANG_file: '+file)
            if 'mtl' in file.lower().split('.')[0].split('_'):
                self.MTL_file=os.path.join(self.images_collection_dir, file)
                print('MTL_file: '+file)
    
    def get_fmask_cloud_array(self):
        print('Running FMASK')
        output_cloud_path = os.path.join(self.images_collection_dir, 'latest_cloud4.tif')
        cmd = '%s -o %s --scenedir %s --cloudbufferdistance %s --cloudprobthreshold %s --shadowbufferdistance %s' % (
        FMASK_EXECUTABLE_PATH, output_cloud_path, self.images_collection_dir, 30, 60.0, 30)
        print('Command: %s' % cmd)
        os.system(cmd)
    
    def get_NDVI_as_array(self):
        RED=self.band_B4.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        a=NIR-RED
        b=RED+NIR
        NDVI_array=np.divide(a,b)
        return NDVI_array
    def get_NDWI_as_array(self):
        GREEN=self.band_B3.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        a=GREEN-NIR
        b=GREEN+NIR
        NDWI_array=np.divide(a,b)
        return NDWI_array  
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
        b=NIR+MIR
        WRI_array=np.divide(a,b)
        return WRI_array
    def get_AWEI_as_array(self):
        GREEN=self.band_B3.GetRasterBand(1).ReadAsArray()
        MIR=self.band_B6.GetRasterBand(1).ReadAsArray()
        NIR=self.band_B5.GetRasterBand(1).ReadAsArray()
        SWIR=self.band_B7.GetRasterBand(1).ReadAsArray()
        a=GREEN-MIR
        b=NIR*0.25
        c=SWIR*2.75
        d=b+c
        e=a*4
        AWEI_array=e-d
        return AWEI_array
    def save_indeces(self, output_folder):
        array=self.get_NDVI_as_array()
        save_array_as_gtiff(array, output_folder+'/NDVI.tif', dataset=self.band_B1)
        array=self.get_NDWI_as_array()
        save_array_as_gtiff(array, output_folder+'/NDWI.tif', dataset=self.band_B1)
        array=self.get_MNDWI_as_array()
        save_array_as_gtiff(array, output_folder+'/MNDWI.tif', dataset=self.band_B1)
        array=self.get_WRI_as_array()
        save_array_as_gtiff(array, output_folder+'/WRI.tif', dataset=self.band_B1)
        array=self.get_AWEI_as_array()
        save_array_as_gtiff(array, output_folder+'/AWEI.tif', dataset=self.band_B1)
        array=None
        
#a=IndecesCalculator('/media/julia/Data/flooding_Landsat/biribidjan_2019/LC08_L1TP_115026_20190910_20190917_01_T1')
#a=IndecesCalculator(('/media/julia/Data/landsat_for_validation/LC08_L1TP_175029_20181029_20181115_01_T1'))
#a.save_indeces('/media/julia/Data/flooding_Landsat/biribidjan_2019/test_out/')
#a.get_fmask_cloud_array()