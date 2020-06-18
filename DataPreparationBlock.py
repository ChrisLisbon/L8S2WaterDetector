#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 21:26:31 2020

@author: julia
"""

import os
import re
import gdal
from SREMPyLandsat.SREMPyLandsat import SREMPyLandsat

class DataPreparator:
    def __init__(self, input_folder, landsat=True, sentinel1=True, sentinel2=True, 
                 landsat_reflectance_method= 'srem',#reflectance
                 landsat_dos_correction= True,
                 landsat_cloud_fmask= False,
                 sentinel2_cloud=None# fmask, s2cloudless #if C1 - sen2cor - 
                ):
        self.landsat=landsat
        self.sentinel1=sentinel1
        self.sentinel2=sentinel2
        
        self.input_folder=input_folder
        self.landsat_folder=None
        self.sentinel2_folder=None
        self.sentinel1_folder=None
        
        self.landsat_reflectance_method=landsat_reflectance_method
        self.landsat_dos_correction=landsat_dos_correction
        self.landsat_cloud_fmask=landsat_cloud_fmask
        
        self.sentinel2_cloud=sentinel2_cloud
        
        folders_list=os.listdir(self.input_folder)
        print(folders_list)
        for folder in folders_list:
            if re.search('LC08', folder.split('.')[0])!=None and len(folder.split('.'))==1:
                self.landsat_folder=folder
            if  re.search('S2', folder.split('.')[0])!=None and folder.split('.')[1]=='SAFE':                
                self.sentinel2_folder=folder
                if re.search('MSIL2A', folder.split('.')[0])!=None:
                    self.sentinel2_level='2A'
                if re.search('MSIL1C', folder.split('.')[0])!=None:
                    self.sentinel2_level='1C'
            if  re.search('S1', folder.split('.')[0])!=None and folder.split('.')[1]=='zip':
                self.sentinel1_folder=folder
            
    def save_landsat_prepared_images(self, output_folder=None):
        if self.landsat_folder!=None and self.landsat==True:
            landsat_files=os.listdir(os.path.join(self.input_folder, self.landsat_folder))
            for file in landsat_files:
                if 'b1' in file.lower().split('.')[0].split('_'):
                    band_B1=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B1: '+file)
                if 'b2' in file.lower().split('.')[0].split('_'):
                    band_B2=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B2: '+file)
                if 'b3' in file.lower().split('.')[0].split('_'):
                    band_B3=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B3: '+file)
                if 'b4' in file.lower().split('.')[0].split('_'):
                    band_B4=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B4: '+file)
                if 'b5' in file.lower().split('.')[0].split('_'):
                    band_B5=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B5: '+file)
                if 'b6' in file.lower().split('.')[0].split('_'):
                    band_B6=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B6: '+file)
                if 'b7' in file.lower().split('.')[0].split('_'):
                    band_B7=gdal.Open(os.path.join(self.input_folder, self.landsat_folder, file))
                    print('band_B7: '+file)                
                if 'MTL' in file.split('.')[0].split('_'):   
                    MTL_file=file
                    print('MTL_file: '+file) 
                if 'ANG' in file.split('.')[0].split('_'):   
                    ANG_file=file
                    print('ANG_file: '+file)
                    
a=DataPreparator('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/test_preparation')
a.save_landsat_prepared_images()