#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 21:26:31 2020

@author: julia
"""
from Landsat8SimpleAlbedo.AlbedoRetriever import AlbedoRetriever

a = AlbedoRetriever(metadata_file='/home/julia/flooding_all/validation_archives/LC08_L1TP_175029_20150428_20170409_01_T1/LC08_L1TP_175029_20150428_20170409_01_T1_MTL.txt',
                    angles_file='/home/julia/flooding_all/validation_archives/LC08_L1TP_175029_20150428_20170409_01_T1/LC08_L1TP_175029_20150428_20170409_01_T1_ANG.txt',
                    temp_dir='/home/julia/flooding_all/validation_archives/temp',
                    albedo_method='olmedo',
                    correction_method='srem',
                    usgs_utils='/home/julia/l8_angles/l8_angles',
                    cygwin_bash_exe_path=None,
                    )

a.save_albedo_as_gtiff('/home/julia/flooding_all/validation_archives/LC08_L1TP_175029_20150428_20170409_01_T1/olmedo_srem_albedo.tif')