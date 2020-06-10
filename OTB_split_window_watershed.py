#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 23:05:43 2020

@author: julia
"""

import otbApplication
from osgeo import gdal, ogr
#from osgeo.gdalconst import *
import numpy as np
import dask_ml.cluster
import dask.array as da
import os
import re
import sys

def get_clusters_array(arrays_list, clasters_number=3):  
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




input_file='/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/raw_B5.TIF'
temp_folder='/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/'
output_file='/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/full_shape.tif'

window_size=300
images_list=['/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/raw_B5.TIF',
             '/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/raw_B4.TIF',
             '/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/raw_B3.TIF']





ds=gdal.Open(input_file)
geo_transform=ds.GetGeoTransform()
prj=ds.GetProjection()
ds_array=np.array(ds.GetRasterBand(1).ReadAsArray())
ds_shape=ds_array.shape
x_min=geo_transform[0]
y_min=geo_transform[3]

first_slice_x=0
second_slice_x=window_size
first_slice_y=0
second_slice_y=window_size
    
range_x=ds_shape[0]//window_size
range_y=ds_shape[1]//window_size

not_full_x=ds_shape[0]-range_x*window_size
not_full_y=ds_shape[1]-range_y*window_size

for i in range(range_x+1):     
    for j in range (range_y+1):
        sub_array=ds_array[first_slice_x:second_slice_x, first_slice_y:second_slice_y]
        sub_x_min=geo_transform[1]*window_size*j+x_min 
        
        print('____________________') 
        print(str(first_slice_x)+':'+str(second_slice_x))
        print(str(first_slice_y)+':'+str(second_slice_y))
        
        sub_geo_transform=[sub_x_min, geo_transform[1], geo_transform[2], y_min, geo_transform[4], geo_transform[5]]
        driver = gdal.GetDriverByName( "GTiff" )
        dt = gdal.GDT_Float32
        cols=sub_array.shape[1]
        rows=sub_array.shape[0]
        temp_out_ds=driver.Create(temp_folder+'temp.tif', cols, rows, 1, dt)
        temp_out_ds.SetProjection(prj)
        temp_out_ds.SetGeoTransform(sub_geo_transform)
        temp_out_ds.GetRasterBand( 1 ).WriteArray( sub_array )
        temp_out_ds=None
        
        app = otbApplication.Registry.CreateApplication("Segmentation")
        app.SetParameterString("in", temp_folder+'temp.tif')
        app.SetParameterString("mode","vector")
        app.SetParameterString("mode.vector.out", temp_folder+"temp.shp")
        app.SetParameterString("filter","watershed")
        app.SetParameterString("filter.watershed.threshold", "0.1")
        app.ExecuteAndWriteOutput()  
        
        for g in range (len(images_list)):
            name=images_list[g].split('.')[0].split('/')[-1]
            app = otbApplication.Registry.CreateApplication("ZonalStatistics")
            app.SetParameterString("in", images_list[g])
            app.SetParameterString("inzone.vector.in", temp_folder+"temp.shp")
            app.SetParameterString("out.vector.filename", temp_folder+str(i)+str(j)+"__"+name+"__stats.shp")
            app.ExecuteAndWriteOutput()
            
            if g==0:
                old_obj=None
                old_layer=None
                first_obj_path=temp_folder+str(i)+str(j)+"__"+name+"__stats.shp"
                old_obj = ogr.Open(first_obj_path, 1)
                old_layer = old_obj.GetLayerByIndex(0)
                old_layer.CreateField(ogr.FieldDefn(name, ogr.OFTReal))
                for feature in old_layer:
                    value=feature.GetField("mean_0")
                    feature.SetField(name, value)
                    old_layer.SetFeature(feature)      
                #если нужно удалить все лишние поля из shp
                #index=old_layer.FindFieldIndex("mean_0", False)
                #old_layer.DeleteField(index)                
                old_obj=None
                old_layer=None
                
            if g!=0:
                old_obj = ogr.Open(first_obj_path, 1)
                old_layer = old_obj.GetLayerByIndex(0)
                old_layer.CreateField(ogr.FieldDefn(name, ogr.OFTReal))
                new_obj=ogr.Open(temp_folder+str(i)+str(j)+"__"+name+"__stats.shp")
                new_layer = new_obj.GetLayerByIndex(0)
                                
                for feature in old_layer:
                    new_feature=new_layer.GetNextFeature()
                    value=new_feature.GetField("mean_0")
                    feature.SetField(name, value)
                    old_layer.SetFeature(feature)                    
                    
                new_obj=None
                new_layer=None
                os.remove(temp_folder+str(i)+str(j)+"__"+name+"__stats.shp")
                os.remove(temp_folder+str(i)+str(j)+"__"+name+"__stats.shx")
                os.remove(temp_folder+str(i)+str(j)+"__"+name+"__stats.dbf")
                os.remove(temp_folder+str(i)+str(j)+"__"+name+"__stats.prj")
                
                old_obj=None
                old_layer=None
        
        tmp_obj = ogr.Open(temp_folder+'temp.shp')
        outReference = tmp_obj.GetLayerByIndex(0).GetSpatialRef()
        tmp_obj=None
        
        os.remove(temp_folder+'temp.shp')
        os.remove(temp_folder+'temp.prj')
        os.remove(temp_folder+'temp.shx')
        os.remove(temp_folder+'temp.dbf')
        
        first_slice_y=first_slice_y+window_size
        second_slice_y=second_slice_y+window_size  
                 
         
    first_slice_x=first_slice_x+window_size       
    second_slice_x=second_slice_x+window_size
    first_slice_y=0
    second_slice_y=window_size
    sub_x_min=x_min
    y_min=geo_transform[5]*(window_size)+y_min
    
os.remove(temp_folder+'temp.tif')

outShapefile = temp_folder+'vector_segments.shp'
outDriver = ogr.GetDriverByName("ESRI Shapefile")
outDataSource = outDriver.CreateDataSource(outShapefile)
outLayer = outDataSource.CreateLayer("layer", outReference, geom_type=ogr.wkbPolygon)


for image in images_list:
    name=image.split('.')[0].split('/')[-1]
    outLayer.CreateField(ogr.FieldDefn(name, ogr.OFTReal))

outLayer=None
outDataSource=None

new_obj=ogr.Open(temp_folder+'vector_segments.shp', 1)
newLayer=new_obj.GetLayerByIndex(0)
newLayerDef = newLayer.GetLayerDefn()

sapefiles_list=os.listdir(temp_folder)
featureID = 0

for file in sapefiles_list:
    if re.search(r"_stats.shp", file)!=None:     
        vector_obj = ogr.Open(temp_folder+file)
        layer = vector_obj.GetLayerByIndex(0)
        for feature in layer:            
            newFeature = ogr.Feature(newLayerDef)
            newFeature.SetFID(featureID)
            for image in images_list:
                #print('setting field')                
                #print(name)
                name=image.split('.')[0].split('/')[-1]
                newFeature.SetField(name, feature.GetField(name))
            newFeature.SetGeometry(feature.GetGeometryRef())
            newLayer.CreateFeature(newFeature)
            featureID += 1
            newFeature=None
            
            
newLayer=None
new_obj=None 
feature=None
layer=None
#for file in sapefiles_list:
    #if file!="vector_segments.shp" and file!="vector_segments.shx" and file!="vector_segments.dbf" and file!="vector_segments.prj":
        #os.remove(temp_folder+file)

arrays_list=[]
for image in images_list:
    arrays_list.append(list())
vector_obj = ogr.Open(temp_folder+'vector_segments.shp')
layer = vector_obj.GetLayerByIndex(0)
    
for feature in layer:
    i=0
    for image in images_list:
        name=image.split('.')[0].split('/')[-1]
        value=feature.GetField(name)
        arrays_list[i].append(value)
        i=i+1
        
new_list=[]
for i in range (len(arrays_list)):
    new_list.append(np.array(arrays_list[i]))
    
clasters_array=get_clusters_array(new_list, clusters_number=5)

vector_obj = ogr.Open(temp_folder+'vector_segments.shp', 1)
layer = vector_obj.GetLayerByIndex(0)   
layer.CreateField(ogr.FieldDefn("class", ogr.OFTInteger))
i=0
for feature in layer:
    value=int(clasters_array[i])
    #print(value)
    feature.SetField("class", value)
    layer.SetFeature(feature)
    i=i+1

driver = gdal.GetDriverByName('GTiff')
dst_ds = driver.Create(output_file, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_UInt16)
dst_ds.SetGeoTransform(ds.GetGeoTransform())
dst_ds.SetProjection(ds.GetProjection())
OPTIONS = ['ATTRIBUTE=class']
gdal.RasterizeLayer(dst_ds, [1], layer, None, options=OPTIONS)
dst_ds, vector_obj, layer = None, None, None


    





















































