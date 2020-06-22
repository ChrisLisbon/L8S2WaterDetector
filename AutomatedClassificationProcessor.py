#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:38:29 2020

@author: julia
"""

import os
from DataPreparationBlock import DataPreparator
from IndicesCalculatorClass import IndicesCalculator
from OTB_watershed_class import WatershesBasedClassifier

input_directory='/home/julia/flooding_all/flooding_preparation/test'
output_directory='/home/julia/flooding_all/flooding_preparation/test/output_dataset'
prep=DataPreparator(input_directory, landsat_correction_method='dos')
prep.prepare_datasets(output_directory)
prep=None
for folder in os.listdir(output_directory):
    if folder=='landsat':
        ind_cal=IndicesCalculator(os.path.join(output_directory, folder))
        os.mkdir(os.path.join(output_directory, 'landsat_indices'))
        ind_cal.save_indices(os.path.join(output_directory, 'landsat_indices'))
        
        indices=os.listdir(os.path.join(output_directory, 'landsat_indices'))
        images_collection=[]
        for index in indices:
            images_collection.append(os.path.join(output_directory, 'landsat_indices', index))
        a=WatershesBasedClassifier(images_collection)
        a.get_classified_segmentation(os.path.join(output_directory, 'landsat_water.shp'))
        
    if folder=='sentinel2':
        ind_cal=IndicesCalculator(os.path.join(output_directory, folder))
        os.mkdir(os.path.join(output_directory, 'sentinel2_indices'))
        ind_cal.save_indices(os.path.join(output_directory, 'sentinel2_indices'))

        indices=os.listdir(os.path.join(output_directory, 'sentinel2_indices'))
        images_collection=[]
        for index in indices:
            images_collection.append(os.path.join(output_directory, 'sentinel2_indices', index))
        a=WatershesBasedClassifier(images_collection)
        a.get_classified_segmentation(os.path.join(output_directory, 'sentinel2_water.shp'))