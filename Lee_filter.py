#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 13:48:43 2020

@author: julia
"""
import gdal
import cv2
import numpy as np
from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance
from S1L1Tools import S1L1Tools
import otbApplication
from OTB_watershed_class import WatershesBasedClassifier
from PIL import Image
from PIL import ImageFilter

def lee_filter(img, size):
    img_mean = uniform_filter(img, (size, size))
    img_sqr_mean = uniform_filter(img**2, (size, size))
    img_variance = img_sqr_mean - img_mean**2

    overall_variance = variance(img)

    img_weights = img_variance / (img_variance + overall_variance)
    img_output = img_mean + img_weights * (img - img_mean)
    return img_output

def save_array_as_gtiff(array, new_file_path, gtiff_path=None, dataset=None,  dtype='float'):    
    if dtype=='float':
        dataType = gdal.GDT_Float32
    if dtype=='int':
        dataType = gdal.GDT_Int16
    if dataset!=None:
        ds=dataset
    if gtiff_path!=None:
        ds=gdal.Open(gtiff_path)
    
    driver = gdal.GetDriverByName("GTiff")    
    dataset = driver.Create(new_file_path, ds.RasterXSize, ds.RasterYSize, 1, dataType)
    dataset.SetProjection(ds.GetProjection())
    dataset.SetGeoTransform(ds.GetGeoTransform())    
    dataset.GetRasterBand(1).WriteArray(array)

ds=S1L1Tools('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/sentitel-1-test/S1A_IW_GRDH_1SDV_20190831T151921_20190831T151946_028815_0343B4_5B41.zip')
ds.perform_radiometric_calibration(polarisations=['VV'])
ds.perform_median_filter_correction(polarisations=['VV', 'VV_sigmaNought'])
ds.export_to_l2('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/sentitel-1-test', x_scale=0, y_scale=0)
ds=None

#ds.perform_radiometric_calibration(polarisations=['VV'])
#ds.export_to_l2('/home/julia/flooding_all/s1_filter_test/', x_scale=0, y_scale=0, polarisations=['VV'])


#ds=gdal.Open('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/sentitel-1-test/VH_sigmaNought.tif')
#arr=ds.GetRasterBand(1).ReadAsArray()
#new_arr=cv2.medianBlur(arr, 5)
#save_array_as_gtiff(new_arr, '/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/sentitel-1-test/VH_sigmaNought_median_f.tif', dataset=ds)

#ds=gdal.Open('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/sentitel-1-test/VH_sigmaNought_median_f.tif')
#arr=ds.GetRasterBand(1).ReadAsArray()
#image = Image.fromarray(arr.astype('float32'))
#new_image = np.asarray(image.filter(ImageFilter.UnsharpMask(radius=2, percent=150)))
#save_array_as_gtiff(new_image, '/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/sentitel-1-test/pil_test.tif', dataset=ds)

'''
app = otbApplication.Registry.CreateApplication("Despeckle")

app.SetParameterString("in", ds)
app.SetParameterString("filter","frost")
app.SetParameterInt("filter.frost.rad", 3)
app.SetParameterFloat("filter.frost.deramp", 0.1)
app.SetParameterString("out", "/home/julia/flooding_all/s1_filter_test/hv01_3.tif")

app.ExecuteAndWriteOutput()

'''
#a=WatershesBasedClassifier(["/home/julia/flooding_all/s1_filter_test/hv01_3.tif"])
#a.get_segmentation_with_base_image(output_path="/home/julia/flooding_all/s1_filter_test/hv_segm_01_3.shp")
