#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 13:48:43 2020

@author: julia
"""
import gdal
from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance
from S1L1Tools import S1L1Tools
import otbApplication
from OTB_watershed_class import WatershesBasedClassifier

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

#ds=S1L1Tools('/home/julia/flooding_all/s1_filter_test/S1B_EW_GRDM_1SDH_20200121T041559_20200121T041704_019910_025A94_146D.zip')
#ds.export_to_l2('/home/julia/flooding_all/s1_filter_test/', x_scale=0, y_scale=0)
'''
ds='/home/julia/flooding_all/s1_filter_test/hv.tif'
#arr=ds.GetRasterBand(1).ReadAsArray()
#new_arr=cv2.medianBlur(arr, 5)
#save_array_as_gtiff(new_arr, '/home/julia/flooding_all/s1_filter_test/lee_hh.tif', dataset=ds)
app = otbApplication.Registry.CreateApplication("Despeckle")

app.SetParameterString("in", ds)
app.SetParameterString("filter","frost")
app.SetParameterInt("filter.frost.rad", 3)
app.SetParameterFloat("filter.frost.deramp", 0.1)
app.SetParameterString("out", "/home/julia/flooding_all/s1_filter_test/hv01_3.tif")

app.ExecuteAndWriteOutput()

'''
a=WatershesBasedClassifier(["/home/julia/flooding_all/s1_filter_test/hv01_3.tif"])
a.get_segmentation_with_base_image(output_path="/home/julia/flooding_all/s1_filter_test/hv_segm_01_3.shp")
