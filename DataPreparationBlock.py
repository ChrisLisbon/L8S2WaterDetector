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
import numpy as np
from SREMPyLandsat.SREMPyLandsat import SREMPyLandsat
from LandsatBasicUtils.BandCalibrator import LandsatBandCalibrator
from primary_functions import save_array_as_gtiff
FMASK_EXECUTABLE_PATH = 'fmask_usgsLandsatStacked.py'

class DataPreparator:
    def __init__(self, input_folder, landsat=True, sentinel1=True, sentinel2=True, 
                 landsat_correction_method='srem',#dos
                 usgs_util_path= None,
                 landsat_cloud_fmask=False,
                 sentinel2_cloud=None, # fmask, s2cloudless #if C1 - sen2cor - 
                 sentinel2_resolution=10, # 10 - with interpolation in B6 and B7, 20 - without interpolation
                 sen2cor_util_path=None
                ):
        self.landsat=landsat
        self.sentinel1=sentinel1
        self.sentinel2=sentinel2
        
        self.input_folder=input_folder
        self.usgs_util_path=usgs_util_path
        self.sentinel2_resolution=sentinel2_resolution
        
        self.landsat_folder=None
        self.sentinel2_folder=None
        self.sentinel1_folder=None        
        self.sentinel2_level=None
        
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
            os.mkdir(os.path.join(self.input_folder, 'temp'))
            
            if self.landsat_correction_method=='srem' and self.usgs_util_path==None:
                raise Exception("For using SREM correction method indicate usgs_util_path!")
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
                    print('Running DOS: '+band)
                    pre_image=LandsatBandCalibrator(band, MTL_file)
                    corrected_array=pre_image.get_dos_corrected_reflectance_as_array()
                    pre_image.save_array_as_gtiff(corrected_array, os.path.join(output_folder, 'DOS_'+band.split('/')[-1]))            
                    pre_image=None 
                                     
            if self.landsat_cloud_fmask==True:
                output_cloud_path = os.path.join(output_folder, 'fmask_cloud_landsat.tif')
                input_directory=os.path.join(self.input_folder, self.landsat_folder)
                print('Running FMASK')
                cmd = '%s -o %s --scenedir %s --cloudbufferdistance %s --cloudprobthreshold %s --shadowbufferdistance %s' % (
                FMASK_EXECUTABLE_PATH, output_cloud_path, input_directory, 30, 60.0, 30)
                print("cmd: "+ cmd)
                os.system(cmd)
                os.remove(output_cloud_path+'.aux.xml')
                
                mask_ds=gdal.Open(output_cloud_path)
                mask_array=np.array(mask_ds.GetRasterBand(1).ReadAsArray())
                mask_ds=None
                output_files_list=os.listdir(output_folder)
                for file in output_files_list:
                    if file!='fmask_cloud_landsat.tif':
                        ds=gdal.Open(os.path.join(output_folder, file))
                        output_array=np.array(ds.GetRasterBand(1).ReadAsArray())
                        output_array[mask_array==2]=np.nan
                        output_array[mask_array==3]=np.nan
                        save_array_as_gtiff(output_array, os.path.join(output_folder, file), dataset=ds)
                mask_array=None
                ds=None
                output_array=None
            shutil.rmtree(os.path.join(self.input_folder, 'temp'))
            
    def save_sentinel2_prepared_images(self, output_folder):
        if self.sentinel2_folder!=None and self.sentinel2==True:
            if self.sentinel2_level=='2A' and self.sentinel2_cloud==None:
                granule_into_main=os.path.join(self.input_folder, self.sentinel2_folder, 'GRANULE')
                images_dir=os.path.join(os.listdir(granule_into_main)[0], 'IMG_DATA')
                if self.sentinel2_resolution==20:
                    m_images_folder=os.path.join(granule_into_main, images_dir, 'R20m')
                    for file in os.listdir(m_images_folder):
                        if 'B02' in file.split('_') or 'B03' in file.split('_') or 'B04' in file.split('_') or 'B8A' in file.split('_') or 'B11' in file.split('_') or 'B12' in file.split('_'):
                            shutil.copyfile(os.path.join(m_images_folder, file), output_folder+'/'+file)
                if self.sentinel2_resolution==10:
                    m_images_folder=os.path.join(granule_into_main, images_dir, 'R10m')
                    for file in os.listdir(m_images_folder):
                        if 'B02' in file.split('_') or 'B03' in file.split('_') or 'B04' in file.split('_') or 'B08' in file.split('_'):
                            shutil.copyfile(os.path.join(m_images_folder, file), output_folder+'/'+file)
                            
                    mm_images_folder=os.path.join(granule_into_main, images_dir, 'R20m')
                    print(os.listdir(mm_images_folder))
                    for file in os.listdir(mm_images_folder):
                        if 'B11' in file.split('_') or 'B12' in file.split('_'):
                            src_ds=gdal.Open(os.path.join(mm_images_folder, file))
                            print(src_ds.GetDriver())
                            
                    
                    
                    
#a=DataPreparator('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/test_preparation/', landsat_correction_method='srem', 
                 #landsat_cloud_fmask=True, usgs_util_path='/home/julia/L8_ANGLES_2_7_0/l8_angles/l8_angles')
#a.save_landsat_prepared_images('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/test_preparation/output_folder')
a=DataPreparator('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/test_preparation/', sentinel2_resolution=10)
a.save_sentinel2_prepared_images('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/test_preparation/sentinel2_output')