#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 14:56:30 2020

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

class WatershesBasedClassifier:
    def __init__(self, input_images_collection, base_image_index=0, temp_folder=None, mode='raster', clasters_number=5):
        self.input_images_collection=input_images_collection
        self.base_image_index=base_image_index
        self.temp_folder=temp_folder
        self.mode=mode
        self.clasters_number=clasters_number
        
        self.base_ds=gdal.Open(input_images_collection[base_image_index])
        self.geo_transform=self.base_ds.GetGeoTransform()
        self.prj=self.base_ds.GetProjection()
        self.data_type=self.base_ds.GetRasterBand(1).DataType
        
    def get_segmentation_with_zonal_statistics(self, output_path, window_size=500):
        if self.temp_folder==None:
            os.mkdir(output_path.replace(output_path.split('/')[-1], '') +'/temp')
            temp_folder=output_path.replace(output_path.split('/')[-1], '') +'/temp'
        ds_array=np.array(self.base_ds.GetRasterBand(1).ReadAsArray())
        ds_shape=ds_array.shape
        x_min=self.geo_transform[0]
        y_min=self.geo_transform[3]
        
        first_slice_x=0
        second_slice_x=window_size
        first_slice_y=0
        second_slice_y=window_size
            
        range_x=ds_shape[0]//window_size
        range_y=ds_shape[1]//window_size
        
        for i in range(range_x+1):     
            for j in range (range_y+1):
                sub_array=ds_array[first_slice_x:second_slice_x, first_slice_y:second_slice_y]
                sub_x_min=self.geo_transform[1]*window_size*j+x_min 
                
                print(str(first_slice_x)+':'+str(second_slice_x))
                print(str(first_slice_y)+':'+str(second_slice_y))
                
                sub_geo_transform=[sub_x_min, self.geo_transform[1], self.geo_transform[2], y_min, self.geo_transform[4], self.geo_transform[5]]
                driver = gdal.GetDriverByName( "GTiff" )
                dt = self.data_type
                cols=sub_array.shape[1]
                rows=sub_array.shape[0]
                temp_out_ds=driver.Create(temp_folder+'temp.tif', cols, rows, 1, dt)
                temp_out_ds.SetProjection(self.prj)
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
                
                for g in range (len(self.input_images_collection)):
                    name=self.input_images_collection[g].split('.')[0].split('/')[-1]
                    app = otbApplication.Registry.CreateApplication("ZonalStatistics")
                    app.SetParameterString("in", self.input_images_collection[g])
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
            y_min=self.geo_transform[5]*(window_size)+y_min
            
        os.remove(temp_folder+'temp.tif')
        
        outShapefile = output_path
        outDriver = ogr.GetDriverByName("ESRI Shapefile")
        outDataSource = outDriver.CreateDataSource(outShapefile)
        outLayer = outDataSource.CreateLayer("layer", outReference, geom_type=ogr.wkbPolygon)
        
        
        for image in self.input_images_collection:
            name=image.split('.')[0].split('/')[-1]
            outLayer.CreateField(ogr.FieldDefn(name, ogr.OFTReal))
        
        outLayer=None
        outDataSource=None
        
        new_obj=ogr.Open(output_path, 1)
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
                    for image in self.input_images_collection:
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
