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
    mn = np.nanmin(array)
    mx = np.nanmax(array)
    new_array =  0 + 255*((array - mn) / (mx-mn))    
    new_array=new_array.astype('uint8')
    
    blur = cv2.GaussianBlur(new_array,(3,3), 0)
    ret, thresh = cv2.threshold(blur, 0 ,255, cv2.THRESH_OTSU)
    thresh[thresh==255]=1
    return thresh

def get_binary_array_from_clasters(clasters_array, classified_arrays_list):
    clasters_values=np.unique(clasters_array)
    for value in clasters_values:
        unique1, counts1=np.unique(classified_arrays_list[0][clasters_array==value], return_counts=True)
        values_dict1=dict(zip(unique1, counts1))
        unique2, counts2=np.unique(classified_arrays_list[1][clasters_array==value], return_counts=True)
        values_dict2=dict(zip(unique2, counts2))
        if 1 not in values_dict1:
            values_dict1[1]=0
        if 0 not in values_dict1:
            values_dict1[0]=0
        if 1 not in values_dict2:
            values_dict2[1]=0
        if 0 not in values_dict2:
            values_dict2[0]=0               
        if values_dict1[1]/(values_dict1[1]+values_dict1[0])>=0.8 and values_dict2[1]/(values_dict2[1]+values_dict2[0])>=0.8:
            clasters_array[clasters_array==value]=1
        else:
            clasters_array[clasters_array==value]=0
    return clasters_array

def percentile_to_range(array, upper_threshold=98,lower_threshold=2):
    upper_perc=np.nanpercentile(array, upper_threshold)
    lower_perc=np.nanpercentile(array, lower_threshold)
    array[array>upper_perc]=upper_perc
    array[array<lower_perc]=lower_perc
    return array

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
    
def reverse_binary_array(array):
    array[array==0]=3
    array[array==1]=0
    array[array==3]=1
    return array