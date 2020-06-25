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
from primary_functions import get_binary_classified_array, save_array_as_gtiff, get_binary_array_from_clasters, reverse_binary_array

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
        
    def prepare_dataset(self, outputBounds=None, outputBoundsSRS=None): #outputBounds (minX, minY, maxX, maxY)
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
                    gdal.Warp(full_file, full_file, format = 'GTiff', outputBounds=outputBounds, outputBoundsSRS = outputBoundsSRS)
    
    def calculate_indices(self, landsat=False, sentinel2=False):
        for folder in os.listdir(self.output_directory):
            if folder=='landsat' and landsat==True:
                ind_cal=IndicesCalculator(os.path.join(self.output_directory, folder))
                os.mkdir(os.path.join(self.output_directory, 'landsat_indices'))
                ind_cal.save_indices(os.path.join(self.output_directory, 'landsat_indices'))         
                
            if folder=='sentinel2' and sentinel2==True:
                ind_cal=IndicesCalculator(os.path.join(self.output_directory, folder))
                os.mkdir(os.path.join(self.output_directory, 'sentinel2_indices'))
                ind_cal.save_indices(os.path.join(self.output_directory, 'sentinel2_indices'))
    
    def classify_dataset(self, landsat=False, sentinel2=False, bands_using=True, indices_using=True):
        if sentinel2==True:
            images_collection=[]
            if indices_using==True:
                indices=os.listdir(os.path.join(self.output_directory, 'sentinel2_indices'))
                for index in indices:
                    images_collection.append(os.path.join(self.output_directory, 'sentinel2_indices', index))
            if bands_using==True:
                bands=os.listdir(os.path.join(self.output_directory, 'sentinel2'))
                for band in bands:
                   images_collection.append(os.path.join(self.output_directory, 'sentinel2', band)) 
            a=WatershesBasedClassifier(images_collection, base_image_index=2)
            a.get_classified_segmentation(os.path.join(self.output_directory, 'sentinel2_class.tif'), mode='raster', window_size=500, statistical_indicators=['mean', 'min', 'max'])
            a=None
            for index in indices:
                if index=='NDWI.tif':
                    ds=gdal.Open(os.path.join(self.output_directory, 'sentinel2_indices', index))
                    array=np.array(ds.GetRasterBand(1).ReadAsArray())
                    ds=None
                    ndwi_bin_array=get_binary_classified_array(array)
                    save_array_as_gtiff(ndwi_bin_array, os.path.join(self.output_directory, 'ndwi_bin_array.tif'), gtiff_path=os.path.join(self.output_directory, 'sentinel2_class.tif'))
                    array=None
                if 'NDVI' in index:
                    ds=gdal.Open(os.path.join(self.output_directory, 'sentinel2_indices', index))
                    array=np.array(ds.GetRasterBand(1).ReadAsArray())
                    ds=None
                    ndvi_bin_array=get_binary_classified_array(array)
                    save_array_as_gtiff(ndvi_bin_array, os.path.join(self.output_directory, 'ndvi_bin_array.tif'), gtiff_path=os.path.join(self.output_directory, 'sentinel2_class.tif'))
                    array=None 
            claster_ds=gdal.Open(os.path.join(self.output_directory, 'sentinel2_class.tif'))
            claster_array=np.array(claster_ds.GetRasterBand(1).ReadAsArray())
            claster_ds=None
            new_claster_array=get_binary_array_from_clasters(claster_array, [ndwi_bin_array, reverse_binary_array(ndvi_bin_array)])
            ndwi_bin_array=None
            ndvi_bin_array=None
            save_array_as_gtiff(new_claster_array, os.path.join(self.output_directory, 'sentinel2_water_mask.tif'), gtiff_path=os.path.join(self.output_directory, 'sentinel2_class.tif'))                
        if landsat==True:
            images_collection=[]
            if indices_using==True:
                indices=os.listdir(os.path.join(self.output_directory, 'landsat_indices'))
                for index in indices:
                    images_collection.append(os.path.join(self.output_directory, 'landsat_indices', index))
            if bands_using==True:
                bands=os.listdir(os.path.join(self.output_directory, 'landsat'))
                for band in bands:
                   images_collection.append(os.path.join(self.output_directory, 'landsat', band)) 
            a=WatershesBasedClassifier(images_collection, base_image_index=2)
            a.get_classified_segmentation(os.path.join(self.output_directory, 'landsat_class.tif'), mode='raster', window_size=500, statistical_indicators=['mean', 'min', 'max'])
            a=None
            for index in indices:
                if index=='NDWI.tif':
                    ds=gdal.Open(os.path.join(self.output_directory, 'landsat_indices', index))
                    array=np.array(ds.GetRasterBand(1).ReadAsArray())
                    ds=None
                    ndwi_bin_array=get_binary_classified_array(array)
                    save_array_as_gtiff(ndwi_bin_array, os.path.join(self.output_directory, 'ndwi_bin_array.tif'), gtiff_path=os.path.join(self.output_directory, 'landsat_class.tif'), dtype='uint')
                    array=None
                if 'NDVI' in index:
                    ds=gdal.Open(os.path.join(self.output_directory, 'landsat_indices', index))
                    array=np.array(ds.GetRasterBand(1).ReadAsArray())
                    ds=None
                    ndvi_bin_array=get_binary_classified_array(array)
                    save_array_as_gtiff(ndvi_bin_array, os.path.join(self.output_directory, 'ndvi_bin_array.tif'), gtiff_path=os.path.join(self.output_directory, 'landsat_class.tif'), dtype='uint')
                    array=None 
            claster_ds=gdal.Open(os.path.join(self.output_directory, 'landsat_class.tif'))
            claster_array=np.array(claster_ds.GetRasterBand(1).ReadAsArray())
            claster_ds=None
            new_claster_array=get_binary_array_from_clasters(claster_array, [ndwi_bin_array, reverse_binary_array(ndvi_bin_array)])
            ndwi_bin_array=None
            ndvi_bin_array=None
            save_array_as_gtiff(new_claster_array, os.path.join(self.output_directory, 'landsat_water_mask.tif'), gtiff_path=os.path.join(self.output_directory, 'landsat_class.tif'), dtype='uint')
            
output_folder='/home/julia/flooding_all/flooding_preparation/test/output_folder'
input_folder='/home/julia/flooding_all/flooding_preparation/test'

a=ClassificationProcessor(input_folder, output_folder, sentinel2=True, sentinel2_cloud='s2cloudless')                
a.prepare_dataset(outputBounds=[358762.589761, 6638238.03191, 370456.825133, 6631100.54521], outputBoundsSRS='EPSG:32636')
a.calculate_indices(sentinel2=True)
a.classify_dataset(sentinel2=True)