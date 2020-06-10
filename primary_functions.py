#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 12:09:14 2020

@author: julia
"""


import dask_ml.cluster
import dask.array as da
import numpy as np

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