#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:38:29 2020

@author: julia
"""

import os
import gdal
import numpy as np
from DataPreparationClass import DataPreparator
from IndicesCalculatorClass import IndicesCalculator
from WatershesBasedClassifierClass import WatershesBasedClassifier
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
                    gdal.Warp(full_file, full_file, format = 'GTiff', outputBounds=outputBounds, outputBoundsSRS = outputBoundsSRS, dstSRS=outputBoundsSRS)
    
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
        try:
            os.remove(self.output_directory+'/landsat/cloud_mask.tif.aux.xml')
        except Exception as e:
            print(e)
            pass
    
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
                    if band!='cloud_mask.tif':
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
            
            mask_path=os.path.join(self.output_directory, 'sentinel2', 'nir.tif')
            mask_ds=gdal.Open(mask_path)
            mask_array=mask_ds.getRasterBand(1).ReadAsArray()
            mask_nodata=mask_ds.getRasterBand(1).GetNoDataValue()
            mask_ds=None
            new_claster_array[mask_array==mask_nodata]=5
            mask_array=None
            
            ndwi_bin_array=None
            ndvi_bin_array=None
            save_array_as_gtiff(new_claster_array, os.path.join(self.output_directory, 'sentinel2_water_mask.tif'), gtiff_path=os.path.join(self.output_directory, 'sentinel2_class.tif'), dtype='uint', nodata_value=5)                
        
        if landsat==True:
            images_collection=[]
            if indices_using==True:
                indices=os.listdir(os.path.join(self.output_directory, 'landsat_indices'))
                for index in indices:
                    images_collection.append(os.path.join(self.output_directory, 'landsat_indices', index))
            if bands_using==True:
                bands=os.listdir(os.path.join(self.output_directory, 'landsat'))
                for band in bands:
                    if band!='cloud_mask.tif':
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
            
            mask_path=os.path.join(self.output_directory, 'landsat', 'nir.tif')
            mask_ds=gdal.Open(mask_path)
            mask_array=mask_ds.getRasterBand(1).ReadAsArray()
            mask_nodata=mask_ds.getRasterBand(1).GetNoDataValue()
            mask_ds=None
            new_claster_array[mask_array==mask_nodata]=5
            mask_array=None
                
            ndwi_bin_array=None
            ndvi_bin_array=None
            save_array_as_gtiff(new_claster_array, os.path.join(self.output_directory, 'landsat_water_mask.tif'), gtiff_path=os.path.join(self.output_directory, 'landsat_class.tif'), dtype='uint', nodata_value=5)

    def create_consolidated_water_mask(self):
        sentinel2_mask_path=os.path.join(self.output_directory, 'sentinel2_water_mask.tif')
        sentinel2_mask_ds=gdal.Open(sentinel2_mask_path)
        sentinel2_mask_nodata_value=sentinel2_mask_ds.GetRasterBand(1).GetNoDataValue()
        sentinel2_mask_array=sentinel2_mask_ds.GetRasterBand(1).ReadAsArray()
        sentinel2_mask_ds=None
        
        landsat_mask_path=os.path.join(self.output_directory, 'landsat_water_mask.tif')
        landsat_mask_ds=gdal.Warp('MEM', landsat_mask_path,  options=gdal.WarpOptions(format = 'MEM', xRes = 10, yRes = -10))
        landsat_mask_nodata_value=landsat_mask_ds.GetRasterBand(1).GetNoDataValue()
        landsat_mask_array=landsat_mask_ds.GetRasterBand(1).ReadAsArray()
        landsat_mask_ds=None
        
        sentinel2_mask_array[sentinel2_mask_array==sentinel2_mask_nodata_value]=landsat_mask_array
                
        save_array_as_gtiff(sentinel2_mask_array, os.path.join(self.output_directory, 'sentinel2_landsat_water_mask.tif'), gtiff_path=os.path.join(self.output_directory, 'sentinel2_water_mask.tif'), dtype='uint', nodata_value=landsat_mask_nodata_value)


output_folder='/media/julia/Data/water_detection_sbp/out'
input_folder='/media/julia/Data/water_detection_sbp'

a=ClassificationProcessor(input_folder, output_folder, sentinel2=True, landsat=True, 
                          landsat_correction_method='dos',
                          landsat_cloud_fmask=True, sentinel2_cloud='s2cloudless')                
#a.prepare_dataset(outputBounds=[609684.7559, 6639270.6362, 634680.5438, 6658914.9030], outputBoundsSRS='EPSG:32635')
#a.calculate_indices(sentinel2=True, landsat=True)
a.classify_dataset(sentinel2=True, landsat=True)