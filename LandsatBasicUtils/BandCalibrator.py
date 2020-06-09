from .MetadataReader import LandsatMetadataReader
import gdal
import numpy as np

class LandsatBandCalibrator():
    def __init__(self, band_file, metadata_file):
        self.metadata_reader = LandsatMetadataReader(metadata_file)
        self.metadata = self.metadata_reader.metadata
        self.band_metadata = self.metadata_reader.get_band_metadata_by_file_name(band_file)

        if not self.band_metadata:
            raise KeyError('Invalid band')

        self.band_dataset = gdal.Open(band_file)
        self.band_array = self.band_dataset.GetRasterBand(1).ReadAsArray()

    def get_radiance_as_array(self):
        radiance = ((self.band_metadata['radiance_maximum']-self.band_metadata['radiance_minimum']) / (self.band_metadata['quantize_cal_maximum']-self.band_metadata['quantize_cal_minimum'])) * (self.band_array - self.band_metadata['quantize_cal_minimum']) + self.band_metadata['radiance_minimum']
        radiance[self.band_array==0] = np.nan
        return radiance

    def get_reflectance_as_array(self, not_native_radiance_array=False):
        if self.band_metadata['type'] != 'reflectance':
            raise TypeError('Given band is thermal')
        if type(not_native_radiance_array)==bool:
            radiance = self.get_radiance_as_array()
        else:
            radiance = not_native_radiance_array
        d = float(self.metadata['EARTH_SUN_DISTANCE'])
        O = np.deg2rad(float(self.metadata['SUN_ELEVATION']))
        E = self.band_metadata['solar_irradiance']

        reflectance = (np.pi*radiance*d*d)/(E*np.sin(O))
        return reflectance

    def get_dos_corrected_reflectance_as_array (self):
        radiance_array = self.get_radiance_as_array()
        dark_object_radiance = np.nanpercentile(radiance_array,0.01)
        O = np.deg2rad(float(self.metadata['SUN_ELEVATION']))
        E = self.band_metadata['solar_irradiance']
        d = float(self.metadata['EARTH_SUN_DISTANCE'])
        L_1p = (0.01*np.cos(O)*np.cos(O)*np.cos(O)*E) / (np.pi*d*d)
        Lhaze = dark_object_radiance - L_1p
        corrected_radiances = radiance_array - Lhaze
        corrected_reflectance = self.get_reflectance_as_array(not_native_radiance_array=corrected_radiances)
        corrected_reflectance[corrected_reflectance < 0] = 0
        
        return corrected_reflectance

    def get_brightness_temperature_as_array(self):
        if self.band_metadata['type'] != 'thermal':
            raise TypeError('Given band is reflectance')

        radiance = self.get_radiance_as_array()

        K1 = self.band_metadata['k1_constant']
        K2 = self.band_metadata['k2_constant']

        brightness_temperature = (K2 / (np.log((K1/radiance+1))))
        return brightness_temperature

    def save_array_as_gtiff(self, array, new_file_path):
        driver = gdal.GetDriverByName("GTiff")
        dataType = gdal.GDT_Float32
        dataset = driver.Create(new_file_path, self.band_dataset.RasterXSize, self.band_dataset.RasterYSize, self.band_dataset.RasterCount, dataType)
        dataset.SetProjection(self.band_dataset.GetProjection())
        dataset.SetGeoTransform(self.band_dataset.GetGeoTransform())
        dataset.GetRasterBand(1).WriteArray(array)
        del dataset