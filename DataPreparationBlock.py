#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 21:26:31 2020

@author: julia
"""

import os
import re
import gdal
import shutil
#from SREMPyLandsat.SREMPyLandsat import SREMPyLandsat
from LandsatBasicUtils.BandCalibrator import LandsatBandCalibrator
FMASK_EXECUTABLE_PATH = 'fmask_usgsLandsatStacked.py'

class DataPreparator:
    def __init__(self, input_folder, landsat=True, sentinel1=True, sentinel2=True, 
                 landsat_correction_method='srem',#dos
                 usgs_util_path= None,
                 landsat_cloud_fmask=False,
                 sentinel2_cloud=None# fmask, s2cloudless #if C1 - sen2cor - 
                ):
        self.landsat=landsat
        self.sentinel1=sentinel1
        self.sentinel2=sentinel2
        
        self.input_folder=input_folder
        self.usgs_util_path=usgs_util_path
        
        self.landsat_folder=None
        self.sentinel2_folder=None
        self.sentinel1_folder=None
        
        self.landsat_correction_method=landsat_correction_method
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
            
    def save_landsat_prepared_images(self, output_folder):
        if self.landsat_folder!=None and self.landsat==True:
            landsat_files=os.listdir(os.path.join(self.input_folder, self.landsat_folder))
            for file in landsat_files:
                if 'b1' in file.lower().split('.')[0].split('_'):
                    band_B1=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B1: '+file)
                if 'b2' in file.lower().split('.')[0].split('_'):
                    band_B2=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B2: '+file)
                if 'b3' in file.lower().split('.')[0].split('_'):
                    band_B3=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B3: '+file)
                if 'b4' in file.lower().split('.')[0].split('_'):
                    band_B4=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B4: '+file)
                if 'b5' in file.lower().split('.')[0].split('_'):
                    band_B5=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B5: '+file)
                if 'b6' in file.lower().split('.')[0].split('_'):
                    band_B6=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B6: '+file)
                if 'b7' in file.lower().split('.')[0].split('_'):
                    band_B7=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('band_B7: '+file)                
                if 'MTL' in file.split('.')[0].split('_'):   
                    MTL_file=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('MTL_file: '+file) 
                if 'ANG' in file.split('.')[0].split('_'):   
                    ANG_file=os.path.join(self.input_folder, self.landsat_folder, file)
                    print('ANG_file: '+file)
            bands_list=[band_B1, band_B2, band_B3, band_B4, band_B5, band_B6, band_B7]
            os.mkdir(os.path.join(self.input_folder, 'temp/'))
            
            if self.landsat_correction_method=='srem' and self.usgs_util_path!=None:
                srem = SREMPyLandsat(mode='landsat-usgs-utils')
                for band in bands_list:
                    if band!=band_B6 and band!=band_B7:
                        data = {'band': band,
                                'metadata': MTL_file,
                                'angles_file': ANG_file,
                                'usgs_util_path':self.usgs_util_path,
                                'temp_dir': os.path.join(self.input_folder, 'temp/'),
                                'cygwin_bash_exe_path':None}                    
                        srem.set_data(data)
                        sr = srem.get_srem_surface_reflectance_as_array()
                        srem.save_array_as_gtiff(sr, os.path.join(output_folder, 'SREM_'+band.split('/')[-1]))
                    else:
                        pre_image=LandsatBandCalibrator(band, MTL_file)
                        corrected_array=pre_image.get_dos_corrected_reflectance_as_array()
                        pre_image.save_array_as_gtiff(corrected_array, os.path.join(output_folder, 'DOS_'+band.split('/')[-1]))
            if self.landsat_correction_method=='dos':
                for band in bands_list:
                    pre_image=LandsatBandCalibrator(band, MTL_file)
                    corrected_array=pre_image.get_dos_corrected_reflectance_as_array()
                    pre_image.save_array_as_gtiff(corrected_array, os.path.join(output_folder, 'DOS_'+band.split('/')[-1]))            
            shutil.rmtree(os.path.join(self.input_folder, 'temp/'))                             
            
            if self.landsat_cloud_fmask==True:
                pass
                
a=DataPreparator('/home/julia/flooding_dataset/')
a.save_landsat_prepared_images()