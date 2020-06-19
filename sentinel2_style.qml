<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.17" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" classificationMax="10" classificationMinMaxOrigin="CumulativeCutFullExtentEstimated" band="1" classificationMin="3" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" clip="0">
          <item alpha="255" value="0" label="NO_DATA" color="#000000"/>
          <item alpha="255" value="1" label="DEFECTIVE" color="#f80004"/>
          <item alpha="255" value="2" label="DARK_AREA" color="#646469"/>
          <item alpha="255" value="3" label="CLOUD_SHADOWS" color="#986541"/>
          <item alpha="255" value="4" label="VEGETATION" color="#2cdf4d"/>
          <item alpha="255" value="5" label="NOT_VEGETATED" color="#fff63a"/>
          <item alpha="255" value="6" label="WATER" color="#0815c6"/>
          <item alpha="255" value="7" label="UNCLASSIFIED" color="#85289f"/>
          <item alpha="255" value="8" label="CLOUD_MEDIUM_PROBABILITY" color="#a3a2a8"/>
          <item alpha="255" value="9" label="CLOUD_HIGH_PROBABILITY" color="#909a97"/>
          <item alpha="255" value="10" label="THIN_CIRRUS" color="#53fce3"/>
          <item alpha="255" value="11" label="SNOW" color="#ff49ed"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
