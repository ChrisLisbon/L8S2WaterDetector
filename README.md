# Landsat-8/Sentinel-2 Water Detection Toolbox

Набор классов для предобработки и выделения водных объектов на спутниковых изображениях Landsat-8 и Sentinel-2

## Описание

Набор инструментов позволяет автоматизированно осуществить:
* предобработку данных, в том числе расчет отражательной способности, атмосферную коррекцию, маскировку облаков;
* расчет вегетационных индексов;
* выделение водных объектов на изображении.

## Набор зависимостей и дополнительных утилит

* **otbApplication** (обязательный) - python API для инструментов Orfeo ToolBox
(https://www.orfeo-toolbox.org/packages/nightly/latest/CookBook-6.7/PythonAPI.html)
* **python-fmask** (опциональный) - инструмент для выделения облаков на изображениях Landsat и Sentinel-2
(http://www.pythonfmask.org/en/latest/)
* **s2cloudless** (опциональный) - инструмент для выделения облаков на изображениях Sentinel-2
(https://github.com/sentinel-hub/sentinel2-cloud-detector)
* **SREMPyLandsat** (опциональный) - инструмент для атмосферной коррекции изображений Landsat методом SREM
(https://github.com/eduard-kazakov/SREMPy-landsat)
* **L8_ANGLES** (опциональный) - angles util by USGS - вспомогательный инструмент для атмосферной коррекции методом SREM
(https://www.usgs.gov/land-resources/nli/landsat/solar-illumination-and-sensor-viewing-angle-coefficient-files)
* **sen2cor** (опциональный) - инструмент ESA для подготовки продукта Sentinel-2 уровня 2A, если он недоступен для скачивания
(https://step.esa.int/main/third-party-plugins-2/sen2cor/)
* **LandsatBasicUtils** (встроенный) - инструмент для первичной калибровки изображений Landsat
(https://github.com/eduard-kazakov/LandsatBasicUtils)

## Описание компонентов

### DataPreparator 

Класс предназначен для предобработки "сырых" спутниковых изображений.

При инициализации класса передаются все параметры, отражающие необходимость подготовки каждого найденного в исходной папке типа данных, а также параметры атмосферной коррекции и пространственного разрешения (для изображений Sentinel-2).

Результатом применения обобщающей функции *prepare_datasets* является создание в выходной директории папки для каждого типа данных (landsat, sentinel2), в которой будут находиться изображения, обработанные в соответствии с заданными параметрами и именованные таким образом,  чтобы использоваться далее для расчета индексов.

#### Пример вызова
```python
from DataPreparatorClass import DataPreparator
a=DataPreparator('/home/user/input_folder',
                 landsat_cloud_fmask=True, 
                 landsat_correction_method='dos',
                 sentinel2_resolution=20,
                 sentinel2_cloud='native_2A_level')
a.prepare_datasets('/home/user/output_folder')
```

### IndicesCalculator

Класс предназначен для автоматического расчета вегетационных индексов. 

Источник исходных изображений не имеет значения - при инициализации класса происходит просмотр переданной папки на наличие суффиксов-определителей диапазона в названии каждого файла (grn, red, nir, mir, swir). Доступные для расчета индексы: NDVI, NDWI, MNDWI, WRI, AWEI.

#### Пример вызова
```python
from IndicesCalculatorClass import IndicesCalculator
a=IndicesCalculator('/home/user/input_folder')
#Для сохранения всех индексов в виде изображений
a.save_indices('/home/user/output_folder')
#Для получения индекса в виде матрицы значений
NDVI=a.get_NDVI_as_array()
```

### WatershesBasedClassifier

Класс предназначен для сегментации изображений и последующей классификации сегментов.

При инициализации класса передается список путей к изображениям на основе которых предполагается сегментация с последующей классификацией. По умолчанию индекс изображения из списка, на основе которого будет производиться сегментация - 0. Остальные изображения используются для присвоения объектам, полученным в результате сегментации, статистических метрик, для последующей классификации. 

В классе реализованы три функции:
* *get_segmentation_with_base_image* - сохраняет шейп-файл с результатом сегментации по базовому изображению, размер скользящего окна по умолчанию 500px.
* *get_segmentation_with_zonal_statistics* - сохраняет шейп-файл с результатом сегментации по базовому изображению, размер скользящего окна по умолчанию 500px. Для каждого объекта дополнительно рассчитываются метрики (по умолчанию - mean, доступные - max, min, stdev) возможно использование нескольких метрик одновременно. 
* *get_classified_segmentation* - сохраняет растр и шейп-файл или только шейп-файл в зависимости от параметра mode='vector', ‘raster’.  В возвращенном шейп-файле появляется дополнительное поле для каждого объекта (class) с результатом классификации по методу к-средних на основе полей, переданных функции.

#### Пример вызова
```python
from WatershesBasedClassifierClass import WatershesBasedClassifier
images_collection=['/home/user/indices/NDVI.tif',
                   '/home/user/indices/NDWI.tif',
                   '/home/user/indices/band_5.tif',]
a=WatershesBasedClassifier(images_collection, base_image_index=1)
a.get_classified_segmentation('class.tif', mode='raster', window_size=400, statistical_indicators=['mean', 'min', 'max'])
```

### AutomatedClassificationProcessor

Обобщающий класс, предназначенный для осуществления полной цепочки обработки от "сырых" изображений до получения маски воды.

При инициализации класса передаются все параметры, требуемые для клаасса DataPreparator и флаг о необходимости подготовки каждого типа данных (landsat=True, sentinel2=True).

Полная обработка данных посредством данного класса заключается в последовательном вызове функций (или игнорировании вызова в случае если какой либо этап был проделан ранее):
* *prepare_dataset* - полная подготовка набора данных в том числе обрезка по границам области интереса (должна находиться в рамках обеих сцен разных типов данных), выделение зон покрытых облачностью nodata value.
* *calculate_indices* - расчет многоспектральных индексов на основе подготовленных предыдущей функцией данных.
* *classify_dataset* - произведение сегментации и классификации основанной на выделенных объектах для каждого типа

#### Пример вызова
```python
a=ClassificationProcessor('/home/user/input_folder', '/home/user/output_folder', 
                          sentinel2=True, landsat=True, 
                          landsat_correction_method='dos',
                          landsat_cloud_fmask=True, 
                          sentinel2_cloud='s2cloudless')                
a.prepare_dataset(outputBounds=[609684.7559, 6639270.6362, 634680.5438, 6658914.9030], outputBoundsSRS='EPSG:32635')
a.calculate_indices(sentinel2=True, landsat=True)
a.classify_dataset(sentinel2=True, landsat=True)
```
