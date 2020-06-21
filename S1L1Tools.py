# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 13:15:03 2017

@author: silent
"""
import gdal
import zipfile
import os
import json
import xml.etree.ElementTree as etree
from datetime import datetime
from scipy import interpolate, ndimage
import numpy as np
import shapely.wkt
import geojson
import cv2

class S1L1Tools():
    
    # metadata = {}
    # measurements = []
    # radiometric_correction_LUT = []
    # noise_correction_LUT = []
        
    
    def __init__(self,datasource_path):
        self.datasource_path = datasource_path
        self.datasource_body = os.path.basename(datasource_path).split('.')[0]
        self.measurements = []
        self.radiometric_correction_LUT = []
        self.noise_correction_LUT = []

        self.metadata = {}
        self.__get_metadata()
        
        for polarisation in self.metadata['polarisations']:
            for archived_file in self.file_list:
                if (archived_file.filename.lower().find(polarisation.lower()) !=-1) and (archived_file.filename.find('.tif') !=-1):
                    self.measurements.append({'polarisation':polarisation,'measurement':gdal.Open(os.path.join('/vsizip/'+self.datasource_path,archived_file.filename))})    
                    
                if (archived_file.filename.lower().find(polarisation.lower()) !=-1) and (archived_file.filename.find('calibration/calibration') !=-1) and (archived_file.filename.find('.xml') !=-1):
                    print (polarisation)
                    print (archived_file.filename)
                    self.radiometric_correction_LUT.append({'polarisation':polarisation,'LUT': self.archive.read(archived_file)})
                    
                if (archived_file.filename.lower().find(polarisation.lower()) !=-1) and (archived_file.filename.find('noise') !=-1) and (archived_file.filename.find('.xml') !=-1):
                    self.noise_correction_LUT.append({'polarisation':polarisation,'LUT': self.archive.read(archived_file)})
                    
    def export_to_l2(self,output_directory,polarisations=None,projection='+proj=longlat +datum=WGS84 +no_defs', preview_mode=False, x_scale=0, y_scale=0):        
        if not polarisations:
            polarisations=[]
            for measurement in self.measurements:
                polarisations.append(measurement['polarisation'])
        
        for measurement in self.measurements:
            if measurement['polarisation'] in polarisations:
                if preview_mode:
                    current_name = os.path.join(output_directory,self.datasource_body+'_'+measurement['polarisation']+'.jpeg')
                else:
                    current_name = os.path.join(output_directory,self.datasource_body+'_'+measurement['polarisation']+'.tif')
                    
                current_measurement = self.__gcp_raster_to_projected(measurement['measurement'])
                current_measurement = self.__reproject_raster_to_projection(current_measurement,projection)
                
                if preview_mode:
                    pixelSize = self.__get_raster_pixel_size(current_measurement)
                    current_measurement = self.__set_raster_resolution(current_measurement,pixelSize['xSize']*x_scale,pixelSize['ySize']*y_scale)
                    self.__save_raster_to_jpeg(current_measurement,current_name)
                else:
                    self.__save_raster_to_gtiff(current_measurement,current_name)
            
    def perform_radiometric_calibration(self, parameter='sigma', polarisations=None):
        if not parameter in ['sigma','beta','gamma']:
            print ('Invalid parameter')
            return 0
        else:
            parameter = parameter + 'Nought'
        
        if not polarisations:
            polarisations=[]
            for measurement in self.measurements:
                polarisations.append(measurement['polarisation'])        
        
        for measurement in self.measurements:
            cols = measurement['measurement'].RasterXSize
            rows = measurement['measurement'].RasterYSize            
            if measurement['polarisation'] in polarisations:
                #print measurement['polarisation']
                lut_xml = self.__dict_search(self.radiometric_correction_LUT,'polarisation',measurement['polarisation'])[0]['LUT']
                #print lut_xml                
                full_lut = self.__get_full_coefficients_array(lut_xml,'radiometric',parameter,cols,rows)
                
                measurement_array = np.array(measurement['measurement'].GetRasterBand(1).ReadAsArray().astype(np.float32))
                #np.save('/home/silent/ma.npy',measurement_array)
                #np.save('/home/silent/lut.npy',full_lut)
                calibrated_array = (measurement_array * measurement_array) / (full_lut * full_lut)
                self.measurements.append({'polarisation':measurement['polarisation']+'_'+parameter,'measurement':self.__create_mem_raster_based_on_existing(measurement['measurement'],[calibrated_array],gdal.GDT_Float32)})
    
    def perform_median_filter_correction(self, polarisations=None):
        print(self.measurements)
        if not polarisations:
            polarisations=[]
            for measurement in self.measurements:
                polarisations.append(measurement['polarisation'])
        print(polarisations) 
        for measurement in self.measurements:
            if measurement['polarisation'] in polarisations:
                measurement_array=np.array(measurement['measurement'].GetRasterBand(1).ReadAsArray())
                if measurement_array.dtype=='float32':
                    shape=measurement_array.shape
                    dx=int(shape[1]/5)
                    start_slice=0
                    new_slice=dx
                    for i in range (5):
                        sub_array=measurement_array[... , start_slice:new_slice]
                        start_slice=start_slice+dx
                        new_slice=new_slice+dx
                        filtered_sub_array=cv2.medianBlur(sub_array, 5)
                        if i==0:
                            filtered_array=filtered_sub_array
                        else:
                            print(filtered_sub_array)
                            print(filtered_array)
                            filtered_array=np.concatenate((filtered_array, filtered_sub_array),1)
                        filtered_sub_array=None
                        print('full sh')
                        print(filtered_array.shape)                   
                else:
                    filtered_array=cv2.medianBlur(measurement_array, 5)
                self.measurements.append({'polarisation':measurement['polarisation']+'_mf','measurement':self.__create_mem_raster_based_on_existing(measurement['measurement'],[filtered_array],gdal.GDT_Float32)})
     
    def __get_metadata(self):
        namespaces = {'safe': '{http://www.esa.int/safe/sentinel-1.0}'}
        self.metadata_raw = ''
        self.archive = zipfile.ZipFile(self.datasource_path)
        self.file_list = self.archive.filelist
        for archived_file in self.file_list:
            if (archived_file.filename.find('manifest.safe') !=-1):
                self.metadata_raw = self.archive.read(archived_file)
        
        if not self.metadata_raw:
            print ('error while reading metadata!')
            return 0
            
        self.metadata_xml_raw = etree.ElementTree(etree.fromstring(self.metadata_raw)).getroot()
        
        metadata_section = self.metadata_xml_raw.find('metadataSection')
        for metadata_object in metadata_section.findall('metadataObject'):
            if metadata_object.attrib['ID'] == 'platform':
                self.metadata['mode'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0}platform').find('{http://www.esa.int/safe/sentinel-1.0}instrument').find('{http://www.esa.int/safe/sentinel-1.0}extension').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}instrumentMode').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}mode').text
                self.metadata['satellite_family'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0}platform').find('{http://www.esa.int/safe/sentinel-1.0}familyName').text
                self.metadata['satellite_name'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0}platform').find('{http://www.esa.int/safe/sentinel-1.0}number').text
                
            if metadata_object.attrib['ID'] == 'generalProductInformation':
                self.metadata['instrument_configuration_id'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}standAloneProductInformation').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}instrumentConfigurationID').text
                
                self.metadata['polarisations'] = []
                for polarisation_node in metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}standAloneProductInformation').findall('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}transmitterReceiverPolarisation'):
                    self.metadata['polarisations'].append(polarisation_node.text)
                
                self.metadata['product_type'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}standAloneProductInformation').find('{http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1}productType').text
        
            if metadata_object.attrib['ID'] == 'acquisitionPeriod':
                self.metadata['start_time'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0}acquisitionPeriod').find('{http://www.esa.int/safe/sentinel-1.0}startTime').text
                self.metadata['start_time'] = datetime.strptime(self.metadata['start_time'], '%Y-%m-%dT%H:%M:%S.%f')
                self.metadata['stop_time'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0}acquisitionPeriod').find('{http://www.esa.int/safe/sentinel-1.0}stopTime').text
                self.metadata['stop_time'] = datetime.strptime(self.metadata['stop_time'], '%Y-%m-%dT%H:%M:%S.%f')
                
            if metadata_object.attrib['ID'] == 'measurementFrameSet':
                self.metadata['foot_print'] = metadata_object.find('metadataWrap').find('xmlData').find('{http://www.esa.int/safe/sentinel-1.0}frameSet').find('{http://www.esa.int/safe/sentinel-1.0}frame').find('{http://www.esa.int/safe/sentinel-1.0}footPrint').find('{http://www.opengis.net/gml}coordinates').text
                self.metadata['foot_print'] = self.__gml_polygon_to_wkt(self.metadata['foot_print'])    
    
    def __gml_polygon_to_wkt(self,gml_coordinates):
        pairs = gml_coordinates.split(' ')
        wkt_pairs = []
        for pair in pairs:
            coords = pair.split(',')
            wkt_pair = coords[1]+' '+coords[0]
            wkt_pairs.append(wkt_pair)
        
        wkt_pairs.append(wkt_pairs[0])
        return 'Polygon((' + ','.join(wkt_pairs) + '))'
            
    def __save_raster_to_gtiff(self,raster,gtiff_path):
        driver = gdal.GetDriverByName("GTiff")
        dataType = raster.GetRasterBand(1).DataType
        dataset = driver.Create(gtiff_path, raster.RasterXSize, raster.RasterYSize, raster.RasterCount, dataType)
        dataset.SetProjection(raster.GetProjection())
        dataset.SetGeoTransform(raster.GetGeoTransform())
        i = 1
        while i<= raster.RasterCount:
            dataset.GetRasterBand(i).WriteArray(raster.GetRasterBand(i).ReadAsArray())
            i+=1
        del dataset
        
    def __create_mem_raster_based_on_existing(self,raster, new_arrays, new_type=None):
        driver = gdal.GetDriverByName("MEM")
        if not new_type:        
            dataType = raster.GetRasterBand(1).DataType
        else:
            dataType = new_type
            
        dataset = driver.Create('', raster.RasterXSize, raster.RasterYSize, raster.RasterCount, dataType)
        #print ('===')
        #print (raster.GetGCPs())
        #print (raster.GetGCPProjection())
        if len(raster.GetGCPs()) > 0:
            dataset.SetGCPs(raster.GetGCPs(), raster.GetGCPProjection())
            
        else:
            dataset.SetProjection(raster.GetProjection())
            dataset.SetGeoTransform(raster.GetGeoTransform())
        
        i = 1
        while i<= raster.RasterCount:
            dataset.GetRasterBand(i).WriteArray(new_arrays[i-1])
            i+=1
        return dataset
    
    def __save_raster_to_jpeg(self,raster,jpeg_path):
        gdal.Translate(jpeg_path, raster, format='JPEG')
        
    def __reproject_raster_to_projection(self,raster,dest_projection):
        source_projection = self.__get_projection(raster)
        output_raster = gdal.Warp('', raster, srcSRS=source_projection, dstSRS=dest_projection, format='MEM')
        return output_raster
    
    def __get_projection(self,raster):
        return raster.GetProjection()
        
    def __set_raster_resolution(self,raster, xRes,yRes):
        outraster = gdal.Warp('',raster,format='MEM',xRes=xRes,yRes=yRes)
        return outraster
    
    def __gcp_raster_to_projected(self,raster):
        output_raster = gdal.Warp('', raster, format='MEM')
        return output_raster
        
    def __get_raster_pixel_size(self,raster):
        geotransform = raster.GetGeoTransform()
        return {'xSize':geotransform[1],'ySize':geotransform[5]}
                
    def __get_full_coefficients_array(self, xml_text, mode, parameter, cols, rows):
        if mode == 'radiometric':
            xml_element_name = 'calibrationVectorList'
        elif mode == 'noise':
            xml_element_name = 'noiseVectorList'
        
        coefficients_rows = []
        
        e = etree.ElementTree(etree.fromstring(xml_text)).getroot()
        for noiseVectorList in e.findall(xml_element_name):
            for child in noiseVectorList:
                for param in child:
                    if param.tag == 'pixel':
                        currentPixels = str(param.text).split()
                    if param.tag == parameter:
                        currentValues = str(param.text).split()
                    
                i = 0
                currentRow = np.empty([1,cols])
                currentRow[:] = np.nan
                while i < len(currentPixels):
                    currentRow[0,int(currentPixels[i])] = float(currentValues[i])
                    i += 1
                
                    
                currentRow = self.__fill_nan(currentRow)
                
                coefficients_rows.append(currentRow[0])
                
        zoom_x = float(cols) / len(coefficients_rows[0])
        zoom_y = float(rows) / len (coefficients_rows)
        return ndimage.zoom(coefficients_rows,[zoom_y,zoom_x])
        
    def __dict_search(self, dictionary_list, key, value):
        return [element for element in dictionary_list if element[key] == value]
        
    def __fill_nan(self,A):
        B = A
        ok = ~np.isnan(B)
        xp = ok.ravel().nonzero()[0]
        fp = B[~np.isnan(B)]
        x = np.isnan(B).ravel().nonzero()[0]
        B[np.isnan(B)] = np.interp(x, xp, fp)
        return B

    def __dump_footprint_to_geojson(self, footprint, out_dir):
        result = False
        try:
            geojson_file_path = os.path.join(out_dir, "%s.geojson" % self.datasource_body)
            g1 = shapely.wkt.loads(footprint)
            g2 = geojson.Feature(geometry=g1, properties={})
            outfile = open(geojson_file_path, "w")
            geojson.dump(g2, outfile)
            outfile.close()
            result = geojson_file_path
        except Exception as e:
            print (e)
            result = False
        finally:
            return result

    def create_footprint(self, out_dir):
        result = False
        try:
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            footprint = self.metadata["foot_print"]
            created_file_path = self.__dump_footprint_to_geojson(footprint, out_dir)
            result = created_file_path
        except Exception as e:
            print (e)
            result = False
        finally:
            return result

#tools = S1L1Tools('/home/silent/Data/sakhalin/S1A_IW_GRDH_1SSV_20150430T203758_20150430T203826_005718_007570_463D.SAFE.zip')
#tools = S1L1Tools('/home/silent/Testing/datasets/S1A_EW_GRDM_1SDH_20141101T022433_20141101T022533_003082_00387B_077E.SAFE.zip')
