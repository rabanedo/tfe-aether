<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>aether:s2ndvi</sld:Name>
    <sld:UserStyle>
      <sld:Name>NDVIb_agricultura</sld:Name>
      <sld:Title>NDVI para Agricultura de Precisión (Byte)</sld:Title>
      <sld:Abstract>Rampa adaptada a valores 0-200 (NDVIb)</sld:Abstract>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ColorMap>
              <sld:ColorMapEntry color="#a50026" quantity="0" label="Agua / Inerte" opacity="1.0"/>
              <sld:ColorMapEntry color="#d73027" quantity="110" label="Suelo Desnudo" opacity="1.0"/>
              <sld:ColorMapEntry color="#f46d43" quantity="120" label="Vigor Muy Bajo" opacity="1.0"/>
              <sld:ColorMapEntry color="#fee08b" quantity="130" label="Vigor Bajo" opacity="1.0"/>
              <sld:ColorMapEntry color="#d9ef8b" quantity="140" label="Vigor Moderado-Bajo" opacity="1.0"/>
              <sld:ColorMapEntry color="#a6d96a" quantity="160" label="Vigor Moderado-Alto" opacity="1.0"/>
              <sld:ColorMapEntry color="#66bd63" quantity="175" label="Vigor Alto" opacity="1.0"/>
              <sld:ColorMapEntry color="#1a9850" quantity="200" label="Vigor Máximo / Canopia Cerrada" opacity="1.0"/>
              <!-- NoData: transparente -->
              <sld:ColorMapEntry color="#000000" quantity="255" opacity="0.0"/>
            </sld:ColorMap>
            <sld:ContrastEnhancement/>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>