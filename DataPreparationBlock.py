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
from S2CloudDetectorUtil import S2CloudDetectorUtil
from S1L1Tools import S1L1Tools
from osgeo.gdalconst import GA_Update
FMASK_EXECUTABLE_PATH_LANDSAT = 'fmask_usgsLandsatStacked.py'
FMASK_EXECUTABLE_PATH_SENTINEL='fmask_sentinel2Stacked.py'

class DataPreparator:
    def __init__(self, input_folder, 
                 landsat_correction_method='srem',#dos
                 usgs_util_path= None,
                 landsat_cloud_fmask=False,
                 sentinel2_cloud=None, # fmask, s2cloudless, native_2A_level(https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm)  C1 - sen2cor - 
                 sentinel2_resolution=10, # 10 - with interpolation in B6 and B7, 20 - without interpolation
                 sen2cor_util_path=None # /home/user/spaceshots/Sen2Cor-02.08.00-Linux64/bin/L2A_Process
                ):
        
        self.input_folder=input_folder
        self.usgs_util_path=usgs_util_path
        self.sen2cor_util_path=sen2cor_util_path
        self.sentinel2_resolution=sentinel2_resolution
        
        self.landsat_folder=None
        self.sentinel1_folder=None
        self.sentinel2_L1C_folder=None
        self.sentinel2_L2A_folder=None
        
        self.landsat_correction_method=landsat_correction_method
        self.landsat_cloud_fmask=landsat_cloud_fmask
        
        self.sentinel2_cloud=sentinel2_cloud
        
        folders_list=os.listdir(self.input_folder)
        print(folders_list)
        for folder in folders_list:
            if re.search('LC08', folder.split('.')[0])!=None and len(folder.split('.'))==1:
                self.landsat_folder=folder
            if  re.search('S2', folder.split('.')[0])!=None and folder.split('.')[1]=='SAFE':               
                if re.search('MSIL2A', folder.split('.')[0])!=None:
                    self.sentinel2_L2A_folder=folder
                if re.search('MSIL1C', folder.split('.')[0])!=None:
                    self.sentinel2_L1C_folder=folder
            if  re.search('S1', folder.split('.')[0])!=None and folder.split('.')[1]=='zip':
                self.sentinel1_folder=folder
            
    def save_landsat_prepared_images(self, output_folder):
        if self.landsat_folder!=None:
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
                FMASK_EXECUTABLE_PATH_LANDSAT, output_cloud_path, input_directory, 30, 60.0, 30)
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
        if self.sentinel2_L2A_folder==None and self.sentinel2_L1C_folder!=None:
            if self.sen2cor_util_path==None:
                raise Exception ('For processing Sentinel-2 1C-level product sen2cor_util_path is required')
            cmd = '%s %s' % (self.sen2cor_util_path, os.path.join(self.input_folder, self.sentinel2_L1C_folder))
            
            #после демоверсии можно посмотреть на встроенную возможность использования ЦМР,
            #которую sen2cor сам же скачивает http://data_public:GDdci@data.cgiar-csi.org/srtm/tiles/GeoTIFF/
            #но придется конфигурацию sen2cor менять пользователю, а не программно
            #поэтому пока без ЦМР
            
            print("cmd: "+ cmd)
            os.system(cmd)
            self.sentinel2_L2A_folder=self.sentinel2_L1C_folder.replace('MSIL1C', 'MSIL2A')
            
        if self.sentinel2_L2A_folder!=None:
            granule_into_main=os.path.join(self.input_folder, self.sentinel2_L2A_folder, 'GRANULE')
            images_dir=os.path.join(os.listdir(granule_into_main)[0], 'IMG_DATA')
            if self.sentinel2_resolution==20:
                print('Output spatial resolution - 20')
                m_images_folder=os.path.join(granule_into_main, images_dir, 'R20m')
                for file in os.listdir(m_images_folder):
                    if 'B02' in file.split('_') or 'B03' in file.split('_') or 'B04' in file.split('_') or 'B8A' in file.split('_') or 'B11' in file.split('_') or 'B12' in file.split('_'):
                        new_file=file.replace('B02', 'B2')
                        new_file=new_file.replace('B03', 'B3')
                        new_file=new_file.replace('B04', 'B4')
                        new_file=new_file.replace('B8A', 'B5')
                        new_file=new_file.replace('B11', 'B6')
                        new_file=new_file.replace('B12', 'B7')
                        gdal.Warp(output_folder+'/'+new_file.split('.')[0]+'.tif', os.path.join(m_images_folder, file))
            if self.sentinel2_resolution==10:
                print('Output spatial resolution - 10')
                m_images_folder=os.path.join(granule_into_main, images_dir, 'R10m')
                for file in os.listdir(m_images_folder):
                    if 'B02' in file.split('_') or 'B03' in file.split('_') or 'B04' in file.split('_') or 'B08' in file.split('_'):
                        new_file=file.replace('B02', 'B2')
                        new_file=new_file.replace('B03', 'B3')
                        new_file=new_file.replace('B04', 'B4')
                        new_file=new_file.replace('B08', 'B5')
                        gdal.Warp(output_folder+'/'+new_file.split('.')[0]+'.tif', os.path.join(m_images_folder, file))
                mm_images_folder=os.path.join(granule_into_main, images_dir, 'R20m')
                for file in os.listdir(mm_images_folder):
                    if 'B11' in file.split('_') or 'B12' in file.split('_'):
                        new_file=file.replace('B11', 'B6')
                        new_file=new_file.replace('B12', 'B7')
                        gdal.Warp(output_folder+'/'+new_file.replace('_20m.jp2', '_10m.tif'), os.path.join(mm_images_folder, file), xRes = 10, yRes = -10, resampleAlg='bilinear')
            
        if self.sentinel2_cloud!=None:
            
            if self.sentinel2_cloud=='native_2A_level':
                cloud_mask_folder=os.path.join(granule_into_main, images_dir, 'R20m')
                for file in os.listdir(cloud_mask_folder):
                    if 'SCL' in file.split('_'):
                        cloud_mask_file=os.path.join(cloud_mask_folder, file)
                        cloud_flags=[3, 8, 9, 10, 11]
                if self.sentinel2_resolution==10:
                    gdal.Warp(os.path.join(output_folder, 'cloud_mask.tif'), cloud_mask_file, xRes = 10, yRes = -10)
                    cloud_mask_file=os.path.join(output_folder, 'cloud_mask.tif')                
            
            if self.sentinel2_cloud=='fmask':
                if self.sentinel2_L1C_folder==None:
                    raise Exception('Fmask is applicable only to 1C-level product')
                cloud_mask_file = os.path.join(output_folder, 'cloud_mask.tif')
                print('Running FMASK')
                cmd = '%s -o %s --safedir %s --cloudbufferdistance %s --cloudprobthreshold %s --shadowbufferdistance %s' % (
                FMASK_EXECUTABLE_PATH_SENTINEL, cloud_mask_file, os.path.join(self.input_folder, self.sentinel2_L1C_folder), 30, 60.0, 30)
                print("cmd: "+ cmd)
                os.system(cmd)
                print('del .aux.xml')
                os.remove(cloud_mask_file+'.aux.xml')
                cloud_flags=[2, 3]
                if self.sentinel2_resolution==10:
                    gdal.Warp(os.path.join(output_folder, 'cloud_mask.tif'), cloud_mask_file, xRes = 10, yRes = -10)
                    cloud_mask_file=os.path.join(output_folder, 'cloud_mask.tif')
                    print('del .aux.xml')
                    os.remove(cloud_mask_file+'.aux.xml')
                
            if self.sentinel2_cloud=='s2cloudless':
                print('Running s2cloudless')
                if self.sentinel2_resolution==10:
                    resolution='10m'
                if self.sentinel2_resolution==20:
                    resolution='20m'
                cloud_mask_file = os.path.join(output_folder, 'cloud_mask.tif')
                u=S2CloudDetectorUtil(os.path.join(self.input_folder, self.sentinel2_L1C_folder), resolution=resolution)
                u.detect_clouds()
                u.export_to_gtiff(output_gtiff=cloud_mask_file, mode='mask')
                u=None
                cloud_flags=[1]
                          
            mask_ds=gdal.Open(cloud_mask_file)
            mask_array=np.array(mask_ds.GetRasterBand(1).ReadAsArray())
            mask_ds=None
            for file in os.listdir(output_folder):
                if file!='cloud_mask.tif':
                    print('Masking file: '+file)
                    ds=gdal.Open(os.path.join(output_folder, file))
                    output_array=np.array(ds.GetRasterBand(1).ReadAsArray())
                    for flag in cloud_flags:
                        output_array[mask_array==flag]=32767                        
                    save_array_as_gtiff(output_array, os.path.join(output_folder, file), dataset=ds, dtype='int')
                    new_ds=gdal.Open(os.path.join(output_folder, file), GA_Update)
                    new_ds.GetRasterBand(1).SetNoDataValue(32767)                        
            mask_array=None
            ds=None
            new_ds=None
            output_array=None
    
    def save_sentinel1_prepared_images(self, output_folder):
        if self.sentinel1_folder!=None:
            ds=S1L1Tools(os.path.join(self.input_folder, self.sentinel1_folder))
            ds.perform_radiometric_calibration()
            ds.perform_median_filter_correction(polarisations=['VH_sigmaNought', 'VV_sigmaNought'])
            ds.export_to_l2(output_folder, polarisations=['VH_sigmaNought_mf', 'VH_sigmaNought_mf'])
        
    def prepare_datasets(self, output_folder, landsat=False, sentinel1=False, sentinel2=False):
        if landsat==True and self.landsat_folder!=None:
            os.mkdir(os.path.join(output_folder, 'landsat'))
            self.save_landsat_prepared_images(os.path.join(output_folder, 'landsat'))
        if sentinel2==True and (self.sentinel2_L1C_folder!=None or self.sentinel2_L2A_folder!=None):
            os.mkdir(os.path.join(output_folder, 'sentinel2'))
            self.save_sentinel2_prepared_images(os.path.join(output_folder, 'sentinel2'))
        if sentinel1==True and self.sentinel1_folder!=None:
            os.mkdir(os.path.join(output_folder, 'sentinel1'))
            self.save_sentinel1_prepared_images(os.path.join(output_folder, 'sentinel1'))
            
#a=DataPreparator('/home/julia/flooding_all/flooding_preparation/test', landsat_cloud_fmask=True, 
#                 landsat_correction_method='dos',
#                 sentinel2_resolution=10,
#                 sentinel2_cloud='native_2A_level')
#a.prepare_datasets('/home/julia/flooding_all/flooding_preparation/test/output_dataset', landsat=False)