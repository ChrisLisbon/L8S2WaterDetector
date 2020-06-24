#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:38:29 2020

@author: julia
"""

import os
import gdal
import numpy as np
from DataPreparationBlock import DataPreparator
from IndicesCalculatorClass import IndicesCalculator
from OTB_watershed_class import WatershesBasedClassifier
from primary_functions import get_binary_classified_array, save_array_as_gtiff

class ClassificationProcessor:
    def __init__(self, input_directory, output_directory, 
                 landsat_correction_method='srem',#dos
                 usgs_util_path= None,
                 landsat_cloud_fmask=False,
                 sentinel2_cloud=None, # fmask, s2cloudless, native_2A_level(https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm)  C1 - sen2cor - 
                 sentinel2_resolution=10, # 10 - with interpolation in B6 and B7, 20 - without interpolation
                 sen2cor_util_path=None,
                 landsat=False, sentinel1=False, sentinel2=False,
                 ):
        self.input_directory=input_directory
        self.output_directory=output_directory
        
        self.usgs_util_path=usgs_util_path
        self.sen2cor_util_path=sen2cor_util_path
        self.sentinel2_resolution=sentinel2_resolution
        self.landsat_correction_method=landsat_correction_method
        self.landsat_cloud_fmask=landsat_cloud_fmask        
        self.sentinel2_cloud=sentinel2_cloud
        
        self.landsat=landsat
        self.sentinel1=sentinel1
        self.sentinel2=sentinel2
        
    def prepare_dataset(self, outputBounds=None): #outputBounds in EPSG:4326 (WGS84) (minX, minY, maxX, maxY)
        prep=DataPreparator(self.input_directory, 
                            landsat_correction_method=self.landsat_correction_method,
                             usgs_util_path=self.usgs_util_path,
                             landsat_cloud_fmask=self.landsat_cloud_fmask,
                             sentinel2_cloud=self.sentinel2_cloud, 
                             sentinel2_resolution=self.sentinel2_resolution,
                             sen2cor_util_path=self.sen2cor_util_path
                            )
        prep.prepare_datasets(self.output_directory, landsat=self.landsat, sentinel1=self.sentinel1, sentinel2=self.sentinel2)
        prep=None
        if outputBounds!=None:
            for folder in os.listdir(self.output_directory):
                for file in os.listdir(os.path.join(self.output_directory, folder)):
                    full_file=os.path.join(self.output_directory, folder, file)
                    gdal.Warp(full_file, full_file, format = 'GTiff', outputBounds=outputBounds, outputBoundsSRS = 'EPSG:4326')
    
    def calculate_indices(self):
        for folder in os.listdir(self.output_directory):
            if folder=='landsat':
                ind_cal=IndicesCalculator(os.path.join(self.output_directory, folder))
                os.mkdir(os.path.join(self.output_directory, 'landsat_indices'))
                ind_cal.save_indices(os.path.join(self.output_directory, 'landsat_indices'))         
                
            if folder=='sentinel2':
                ind_cal=IndicesCalculator(os.path.join(self.output_directory, folder))
                os.mkdir(os.path.join(self.output_directory, 'sentinel2_indices'))
                ind_cal.save_indices(os.path.join(self.output_directory, 'sentinel2_indices'))
    
    def classify_dataset(self):
        indices=os.listdir(os.path.join(self.output_directory, 'sentinel2_indices'))
        images_collection=[]
        for index in indices:
            images_collection.append(os.path.join(self.output_directory, 'sentinel2_indices', index))
        a=WatershesBasedClassifier(images_collection)
        a.get_classified_segmentation(os.path.join(self.output_directory, 'sentinel2_class.tif'), mode='raster', window_size=500)
        a=None
        for index in indices:
            if index=='1NDWI.tif':
                ds=gdal.Open(os.path.join(self.output_directory, 'sentinel2_indices', index))
                array=np.array(ds.GetRasterBand(1).ReadAsArray())
                ds=None
                ndwi_bin_array=get_binary_classified_array(array)
                array=None
            if 'NDVI' in index:
                ds=gdal.Open(os.path.join(self.output_directory, 'sentinel2_indices', index))
                array=np.array(ds.GetRasterBand(1).ReadAsArray())
                ds=None
                ndvi_bin_array=get_binary_classified_array(array)
                array=None 
        claster_ds=gdal.Open(os.path.join(self.output_directory, 'sentinel2_class.tif'))
        claster_array=np.array(claster_ds.GetRasterBand(1).ReadAsArray())
        claster_ds=None
        for value in np.unique(claster_array):
            ndwi_water_values=(ndwi_bin_array[claster_array==value]==1).sum()
            ndwi_non_water_values=(ndwi_bin_array[claster_array==value]==0).sum()
            ndvi_water_values=(ndvi_bin_array[claster_array==value]==0).sum()
            ndvi_non_water_values=(ndvi_bin_array[claster_array==value]==1).sum()
            if ndwi_water_values/(ndwi_water_values+ndwi_non_water_values)>=0.9 and ndvi_water_values/(ndvi_water_values+ndvi_non_water_values)>=0.9:
                claster_array[claster_array==value]=1
            else:
                claster_array[claster_array==value]=0
        ndwi_bin_array=None
        ndvi_bin_array=None
        save_array_as_gtiff(claster_array, os.path.join(self.output_directory, 'sentinel2_water_mask.tif'), gtiff_path=os.path.join(self.output_directory, 'sentinel2_class.tif'))                
                        
output_folder='/home/julia/flooding_all/flooding_preparation/test/output_dataset'
input_folder='/home/julia/flooding_all/flooding_preparation/test'

#a=ClassificationProcessor(input_folder, output_folder, landsat_correction_method='dos', sentinel2_cloud='fmask', sentinel2=True)                
#a.prepare_dataset(outputBounds=[29.7400, 59.8400, 30.4188, 60.0109])
#a.calculate_indices()
#a.classify_dataset()