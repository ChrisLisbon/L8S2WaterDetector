#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 11:42:40 2020

@author: julia
"""

import os
import gdal
import numpy as np
from primary_functions import save_array_as_gtiff, percentile_to_range
class IndicesCalculator:
    def __init__(self, images_collection_dir):
        self.images_collection_dir=images_collection_dir        
        files_names=os.listdir(self.images_collection_dir)
        for file in files_names:
            if 'grn' in file.lower().split('.')[0].split('_'):
                self.green=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('GREEN: '+file)
            if 'red' in file.lower().split('.')[0].split('_'):
                self.red=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('RED: '+file)
            if 'nir' in file.lower().split('.')[0].split('_'):
                self.nir=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('NIR: '+file)
            if 'mir' in file.lower().split('.')[0].split('_'):
                self.mir=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('MIR: '+file)
            if 'swir' in file.lower().split('.')[0].split('_'):
                self.swir=gdal.Open(os.path.join(self.images_collection_dir, file))
                print('SWIR: '+file)
        
    def get_NDVI_as_array(self):
        nodataValue=self.red.GetRasterBand(1).GetNoDataValue()
        RED=self.red.GetRasterBand(1).ReadAsArray().astype('float')
        NIR=self.nir.GetRasterBand(1).ReadAsArray().astype('float')
        a=NIR-RED
        b=RED+NIR
        NDVI_array=percentile_to_range(np.divide(a,b))
        NDVI_array[RED==nodataValue]=nodataValue
        RED=None
        NIR=None
        a=None
        b=None
        return NDVI_array
    def get_NDWI_as_array(self):
        nodataValue=self.green.GetRasterBand(1).GetNoDataValue()
        GREEN=self.green.GetRasterBand(1).ReadAsArray().astype('float')
        NIR=self.nir.GetRasterBand(1).ReadAsArray().astype('float')
        a=GREEN-NIR
        b=GREEN+NIR
        NDWI_array=percentile_to_range(np.divide(a,b))
        NDWI_array[GREEN==nodataValue]=nodataValue
        GREEN=None
        NIR=None
        a=None
        b=None
        return NDWI_array
    def get_MNDWI_as_array(self):
        nodataValue=self.green.GetRasterBand(1).GetNoDataValue()
        GREEN=self.green.GetRasterBand(1).ReadAsArray().astype('float')
        MIR=self.mir.GetRasterBand(1).ReadAsArray().astype('float')
        a=GREEN-MIR
        b=GREEN+MIR
        MNDWI_array=percentile_to_range(np.divide(a,b))
        MNDWI_array[GREEN==nodataValue]=nodataValue
        return MNDWI_array
    def get_WRI_as_array(self):
        nodataValue=self.green.GetRasterBand(1).GetNoDataValue()
        GREEN=self.green.GetRasterBand(1).ReadAsArray().astype('float')
        RED=self.red.GetRasterBand(1).ReadAsArray().astype('float')
        NIR=self.nir.GetRasterBand(1).ReadAsArray().astype('float')
        MIR=self.mir.GetRasterBand(1).ReadAsArray().astype('float')
        a=GREEN+RED
        GREEN=None
        RED=None        
        b=NIR+MIR
        NIR=None
        MIR=None
        WRI_array=percentile_to_range(np.divide(a,b))  
        WRI_array[GREEN==nodataValue]=nodataValue
        a=None
        b=None
        return WRI_array
    def get_AWEI_as_array(self):
        nodataValue=self.green.GetRasterBand(1).GetNoDataValue()
        GREEN=self.green.GetRasterBand(1).ReadAsArray().astype('float')
        MIR=self.mir.GetRasterBand(1).ReadAsArray().astype('float')
        NIR=self.nir.GetRasterBand(1).ReadAsArray().astype('float')
        SWIR=self.swir.GetRasterBand(1).ReadAsArray().astype('float')
        a=GREEN-MIR
        GREEN=None
        MIR=None
        b=NIR*0.25
        NIR=None
        c=SWIR*2.75
        SWIR=None
        d=b+c
        e=a*4
        AWEI_array=percentile_to_range(e-d)
        AWEI_array[GREEN==nodataValue]=nodataValue
        a=None
        b=None
        c=None
        d=None
        e=None
        return AWEI_array
    def save_indices(self, output_folder):        
        array=self.get_NDVI_as_array()
        save_array_as_gtiff(array, output_folder+'/NDVI.tif', dataset=self.nir)
        array=self.get_NDWI_as_array()
        save_array_as_gtiff(array, output_folder+'/NDWI.tif', dataset=self.green)
        #array=self.get_MNDWI_as_array()
        #save_array_as_gtiff(array, output_folder+'/MNDWI.tif', dataset=self.green)
        array=self.get_WRI_as_array()
        save_array_as_gtiff(array, output_folder+'/WRI.tif', dataset=self.nir)
        array=self.get_AWEI_as_array()
        save_array_as_gtiff(array, output_folder+'/AWEI.tif', dataset=self.nir)
        array=None
        