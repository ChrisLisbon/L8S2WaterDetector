#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 12:09:14 2020

@author: julia
"""


import dask_ml.cluster
import dask.array as da
import numpy as np
import gdal
import cv2

def k_means_clastering(arrays_list, clasters_number=3):  
    arrays_number=len(arrays_list)
    shape=arrays_list[0].shape
    print(shape)
    if len(shape)==2:    
        ravel_shape=shape[0]*shape[1]
    if len(shape)==1:
        ravel_shape=shape[0]
    arrays_matrix=np.empty((0,ravel_shape), int)
    for i in range (len(arrays_list)):              
        arrays_list[i]=np.nan_to_num(arrays_list[i], nan=-9999)
        arrays_matrix=np.append(arrays_matrix, [np.ravel(arrays_list[i])], axis=0)        
    matrix_for_kmeans=np.transpose(arrays_matrix) 
    print('Starting clastering')
    x=da.from_array(matrix_for_kmeans, chunks= (5000, arrays_number))
    x = x.persist()    
    km = dask_ml.cluster.KMeans(n_clusters = clasters_number, init_max_iter = 2, oversampling_factor = 10) 
    km.fit(x)
    print('Clasterization finished')
    return(np.reshape(np.array(km.labels_), shape))

def get_binary_classified_array(array):
    upper_perc=np.nanpercentile(array, 98)
    lower_perc=np.nanpercentile(array, 2)
    array[array>upper_perc]=upper_perc
    array[array<lower_perc]=lower_perc
    
    mn = np.nanmin(array)
    mx = np.nanmax(array)
    new_array =  0 + 255*((array - mn) / (mx-mn))    
    new_array=new_array.astype('uint8')
    
    blur = cv2.GaussianBlur(new_array,(3,3), 0)
    ret, thresh = cv2.threshold(blur, 0 ,255, cv2.THRESH_OTSU)
    thresh[thresh==255]=1
    return thresh

def save_array_as_gtiff(array, new_file_path, gtiff_path=None, dataset=None,  dtype='float'):    
    if dtype=='float':
        dataType = gdal.GDT_Float32
    if dtype=='int':
        dataType = gdal.GDT_Int16
    if dtype=='uint':
        dataType = gdal.GDT_UInt16
    if dataset!=None:
        ds=dataset
    if gtiff_path!=None:
        ds=gdal.Open(gtiff_path)    
    driver = gdal.GetDriverByName("GTiff")    
    dataset = driver.Create(new_file_path, ds.RasterXSize, ds.RasterYSize, 1, dataType)
    dataset.SetProjection(ds.GetProjection())
    dataset.SetGeoTransform(ds.GetGeoTransform())    
    dataset.GetRasterBand(1).WriteArray(array)
    
a=gdal.Open('/media/julia/Data/flooding_Landsat/biribidjan_2019/LC08_L1TP_114026_20190802_20190819_01_T1/LC08_L1TP_114026_20190802_20190819_01_T1_B5.TIF')
array=a.GetRasterBand(1).ReadAsArray()
b=get_binary_classified_array(array)
save_array_as_gtiff(b, '/media/julia/Data/flooding_Landsat/biribidjan_2019/test.tif', dataset=a, dtype='uint')