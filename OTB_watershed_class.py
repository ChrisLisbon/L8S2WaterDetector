#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 14:56:30 2020

@author: julia
"""


import otbApplication
from osgeo import gdal, ogr
import numpy as np
import os
import re
import shutil
from primary_functions import k_means_clastering

class WatershesBasedClassifier:
    def __init__(self, input_images_collection, base_image_index=0, temp_folder=None):
        self.input_images_collection=input_images_collection
        self.base_image_index=base_image_index
        self.temp_folder=temp_folder
        
        self.base_ds=gdal.Open(input_images_collection[base_image_index])
        self.geo_transform=self.base_ds.GetGeoTransform()
        self.prj=self.base_ds.GetProjection()
        self.data_type=self.base_ds.GetRasterBand(1).DataType
        self.base_array=np.array(self.base_ds.GetRasterBand(1).ReadAsArray())
        self.base_array_shape=self.base_array.shape
     
    def get_segmentation_with_base_image(self,  output_path, window_size=500):
        if self.temp_folder==None:
            os.mkdir(output_path.replace(output_path.split('/')[-1], '') +'temp')
            temp_folder=output_path.replace(output_path.split('/')[-1], '') +'temp/'
            del_flag=True
        else:
            temp_folder=self.temp_folder
            del_flag=False
        
        y_min=self.geo_transform[3]        
        first_slice_x=0
        second_slice_x=window_size
        first_slice_y=0
        second_slice_y=window_size
            
        range_x=self.base_array_shape[0]//window_size
        range_y=self.base_array_shape[1]//window_size
        
        for i in range(range_x+1):     
            for j in range (range_y+1):
                sub_array=self.base_array[first_slice_x:second_slice_x, first_slice_y:second_slice_y]
                sub_x_min=self.geo_transform[1]*window_size*j+self.geo_transform[0] 
                
                sub_geo_transform=[sub_x_min, self.geo_transform[1], self.geo_transform[2], y_min, self.geo_transform[4], self.geo_transform[5]]
                driver = gdal.GetDriverByName( "GTiff" )
                cols=sub_array.shape[1]
                rows=sub_array.shape[0]
                temp_out_ds=driver.Create(temp_folder+'temp.tif', cols, rows, 1, self.data_type)
                temp_out_ds.SetProjection(self.prj)
                temp_out_ds.SetGeoTransform(sub_geo_transform)
                temp_out_ds.GetRasterBand( 1 ).WriteArray( sub_array )
                temp_out_ds=None
                
                app = otbApplication.Registry.CreateApplication("Segmentation")
                app.SetParameterString("in", temp_folder+'temp.tif')
                app.SetParameterString("mode","vector")
                app.SetParameterString("mode.vector.out", temp_folder+str(i)+str(j)+"_temp.shp")
                app.SetParameterString("filter","watershed")
                app.SetParameterString("filter.watershed.threshold", "0.1")
                app.ExecuteAndWriteOutput()
                
                tmp_obj = ogr.Open(temp_folder+str(i)+str(j)+"_temp.shp")
                outReference = tmp_obj.GetLayerByIndex(0).GetSpatialRef()
                tmp_obj=None
                
                first_slice_y=first_slice_y+window_size
                second_slice_y=second_slice_y+window_size  
                         
                 
            first_slice_x=first_slice_x+window_size       
            second_slice_x=second_slice_x+window_size
            first_slice_y=0
            second_slice_y=window_size
            sub_x_min=self.geo_transform[0]
            y_min=self.geo_transform[5]*(window_size)+y_min
            
        os.remove(temp_folder+'temp.tif')
        
        outShapefile = output_path
        outDriver = ogr.GetDriverByName("ESRI Shapefile")
        outDataSource = outDriver.CreateDataSource(outShapefile)
        outDataSource.CreateLayer("layer", outReference, geom_type=ogr.wkbPolygon)
        outDataSource=None
        
        new_obj=ogr.Open(outShapefile, 1)
        newLayer=new_obj.GetLayerByIndex(0)
        newLayerDef = newLayer.GetLayerDefn()
        
        sapefiles_list=os.listdir(temp_folder)
        featureID = 0
        for file in sapefiles_list:
            if re.search(r"_temp.shp", file)!=None:     
                vector_obj = ogr.Open(temp_folder+file)
                layer = vector_obj.GetLayerByIndex(0)
                for feature in layer:            
                    newFeature = ogr.Feature(newLayerDef)
                    newFeature.SetFID(featureID)
                    newFeature.SetGeometry(feature.GetGeometryRef())
                    newLayer.CreateFeature(newFeature)
                    featureID += 1
                    newFeature=None                    
                    
        newLayer=None
        new_obj=None 
        feature=None
        layer=None        
        
        if del_flag==True:
            shutil.rmtree(temp_folder)
            
    def get_segmentation_with_zonal_statistics(self, output_path, statistical_indicators=['mean'], window_size=500):
        #availible statistical_indicators = ['mean', 'max', 'min', 'stdev']
        if self.temp_folder==None:
            os.mkdir(output_path.replace(output_path.split('/')[-1], '') +'temp')
            temp_folder=output_path.replace(output_path.split('/')[-1], '') +'temp/'
            del_flag=True
        else:
            temp_folder=self.temp_folder
            del_flag=False
        
        y_min=self.geo_transform[3]        
        first_slice_x=0
        second_slice_x=window_size
        first_slice_y=0
        second_slice_y=window_size
            
        range_x=self.base_array_shape[0]//window_size
        range_y=self.base_array_shape[1]//window_size
        
        for i in range(range_x+1):     
            for j in range (range_y+1):
                sub_array=self.base_array[first_slice_x:second_slice_x, first_slice_y:second_slice_y]
                sub_x_min=self.geo_transform[1]*window_size*j+self.geo_transform[0] 
                
                print(str(first_slice_x)+':'+str(second_slice_x))
                print(str(first_slice_y)+':'+str(second_slice_y))
                
                sub_geo_transform=[sub_x_min, self.geo_transform[1], self.geo_transform[2], y_min, self.geo_transform[4], self.geo_transform[5]]
                driver = gdal.GetDriverByName( "GTiff" )
                cols=sub_array.shape[1]
                rows=sub_array.shape[0]
                temp_out_ds=driver.Create(temp_folder+'temp.tif', cols, rows, 1, self.data_type)
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
                        for indicator in statistical_indicators:
                            old_layer.CreateField(ogr.FieldDefn(name+'_'+indicator, ogr.OFTReal))
                        for feature in old_layer:
                            for indicator in statistical_indicators:
                                value=feature.GetField(indicator+"_0")
                                feature.SetField(name+'_'+indicator, value)
                                old_layer.SetFeature(feature)      
                        #если нужно удалить все лишние поля из shp
                        #index=old_layer.FindFieldIndex("mean_0", False)
                        #old_layer.DeleteField(index)                
                        old_obj=None
                        old_layer=None
                        
                    if g!=0:
                        old_obj = ogr.Open(first_obj_path, 1)
                        old_layer = old_obj.GetLayerByIndex(0)
                        for indicator in statistical_indicators:
                            old_layer.CreateField(ogr.FieldDefn(name+'_'+indicator, ogr.OFTReal))
                        new_obj=ogr.Open(temp_folder+str(i)+str(j)+"__"+name+"__stats.shp")
                        new_layer = new_obj.GetLayerByIndex(0)
                                        
                        for feature in old_layer:
                            new_feature=new_layer.GetNextFeature()
                            for indicator in statistical_indicators:                                
                                value=new_feature.GetField(indicator+"_0")
                                feature.SetField(name+'_'+indicator, value)
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
            sub_x_min=self.geo_transform[0]
            y_min=self.geo_transform[5]*(window_size)+y_min
            
        os.remove(temp_folder+'temp.tif')
        
        outDriver = ogr.GetDriverByName("ESRI Shapefile")
        outDataSource = outDriver.CreateDataSource(output_path)
        outLayer = outDataSource.CreateLayer("layer", outReference, geom_type=ogr.wkbPolygon)
        
        for image in self.input_images_collection:
            name=image.split('.')[0].split('/')[-1]
            for indicator in statistical_indicators:
                outLayer.CreateField(ogr.FieldDefn(name+'_'+indicator, ogr.OFTReal))
        
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
                        name=image.split('.')[0].split('/')[-1]
                        for indicator in statistical_indicators:
                            value=feature.GetField(name+'_'+indicator)
                            newFeature.SetField(name+'_'+indicator, value)
                    newFeature.SetGeometry(feature.GetGeometryRef())
                    newLayer.CreateFeature(newFeature)
                    featureID += 1
                    newFeature=None                  
                  
        newLayer=None
        new_obj=None 
        feature=None
        layer=None
        
        if del_flag==True:
            print(temp_folder)
            shutil.rmtree(temp_folder, ignore_errors=True)

    def get_classified_segmentation (self, output_path=None, input_shapefile=None, fields=[], statistical_indicators=['mean'], window_size=500, class_number=5, mode='vector'):
        if mode=='vector':
            filename=output_path
        if mode=='raster':
            filename=output_path.replace(output_path.split('/')[-1], 'temp.shp')
        if input_shapefile==None:
            self.get_segmentation_with_zonal_statistics(filename, statistical_indicators=statistical_indicators, window_size=window_size)
            input_shapefile=filename
            
            vector_obj = ogr.Open(input_shapefile)
            layer = vector_obj.GetLayerByIndex(0)
            ldefn = layer.GetLayerDefn()
            for n in range(ldefn.GetFieldCount()):
                fdefn = ldefn.GetFieldDefn(n)
                fields.append(fdefn.name)
        if input_shapefile!=None:  
            vector_obj = ogr.Open(input_shapefile)
            layer = vector_obj.GetLayerByIndex(0)                              
        arrays_list=[]
        for field in fields:
            arrays_list.append(list())
            
        for feature in layer:
            i=0
            for field in fields:
                value=feature.GetField(field)
                arrays_list[i].append(value)
                i=i+1
                
        new_list=[]
        for i in range (len(arrays_list)):
            new_list.append(np.array(arrays_list[i]))
            
        clasters_array=k_means_clastering(new_list, clasters_number=class_number)
        
        vector_obj = ogr.Open(filename, 1)
        layer = vector_obj.GetLayerByIndex(0)   
        layer.CreateField(ogr.FieldDefn("class", ogr.OFTInteger))
        i=0
        for feature in layer:
            value=int(clasters_array[i])
            feature.SetField("class", value)
            layer.SetFeature(feature)
            i=i+1
        
        if mode=='raster':
            driver = gdal.GetDriverByName('GTiff')
            dst_ds = driver.Create(output_path, self.base_ds.RasterXSize, self.base_ds.RasterYSize, 1, gdal.GDT_UInt16)
            dst_ds.SetGeoTransform(self.geo_transform)
            dst_ds.SetProjection(self.prj)
            OPTIONS = ['ATTRIBUTE=class']
            gdal.RasterizeLayer(dst_ds, [1], layer, None, options=OPTIONS)
            dst_ds, vector_obj, layer = None, None, None
            
            os.remove(output_path.replace(output_path.split('/')[-1], 'temp.shp'))
            os.remove(output_path.replace(output_path.split('/')[-1], 'temp.prj'))
            os.remove(output_path.replace(output_path.split('/')[-1], 'temp.shx'))
            os.remove(output_path.replace(output_path.split('/')[-1], 'temp.dbf'))
        
        
            
            
            
'''files=['/home/julia/flooding_all/ob_to_class/LC08_L1TP_162016_20180714_20180730_01_T1/out_folder/NDVI',
       '/home/julia/flooding_all/ob_to_class/LC08_L1TP_162016_20180714_20180730_01_T1/out_folder/NDWI',
       '/home/julia/flooding_all/ob_to_class/LC08_L1TP_162016_20180714_20180730_01_T1/out_folder/r_B4.tif',
       '/home/julia/flooding_all/ob_to_class/LC08_L1TP_162016_20180714_20180730_01_T1/out_folder/r_B5.tif']
a=WatershesBasedClassifier(files)
a.get_segmentation_with_zonal_statistics('/home/julia/flooding_all/ob_to_class/LC08_L1TP_162016_20180714_20180730_01_T1/out_folder/result.shp')
a.get_classified_segmentation('/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/result.shp', mode='vector')
'''

files=['/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/B5_.tif',
       '/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/B4_.tif',
       '/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/B3_.tif']
a=WatershesBasedClassifier(files)
a.get_classified_segmentation(input_shapefile='/media/julia/Data/KrasnodarskiKray_Landsat_Sentinel-1/LC08_L1TP_175029_20190407_20190422_01_T1/temp/result.shp',
                              fields=['B5__mean', 'B4__mean'], mode='vector')























