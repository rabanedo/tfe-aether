<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
    xsi:schemaLocation="http://opengis.net StyledLayerDescriptor.xsd"
    xmlns="http://opengis.net"
    xmlns:ogc="http://opengis.net"
    xmlns:xlink="http://w3.org"
    xmlns:xsi="http://w3.org">
  <NamedLayer>
    <Name>ndvi_precision_agriculture</Name>
    <UserStyle>
      <Title>NDVI para Agricultura de Precision</Title>
      <Abstract>Rampa optimizada para discriminar vigor vegetal</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <Opacity>1.0</Opacity>
            <ColorMap type="ramp">
              <!-- Valores menores a 0.1: Agua, nubes o suelo desnudo puro -->
              <ColorMapEntry color="#a50026" quantity="-1.0" label="Agua / Inerte"/>
              <ColorMapEntry color="#d73027" quantity="0.1" label="Suelo Desnudo"/>
              <!-- Valores 0.1 a 0.30: Suelo con rastrojo o brotes muy incipientes -->
              <ColorMapEntry color="#f46d43" quantity="0.2" label="Vigor Muy Bajo"/>
              <ColorMapEntry color="#fee08b" quantity="0.3" label="Vigor Bajo"/>
              <!-- Valores 0.4 a 0.6: Cultivo en desarrollo medio / estrés moderado -->
              <ColorMapEntry color="#d9ef8b" quantity="0.4" label="Vigor Moderado-Bajo"/>
              <ColorMapEntry color="#a6d96a" quantity="0.6" label="Vigor Moderado-Alto"/>
              <!-- Valores > 0.6: Densidad foliar máxima y excelente salud -->
              <ColorMapEntry color="#66bd63" quantity="0.75" label="Vigor Alto"/>
              <ColorMapEntry color="#1a9850" quantity="1.0" label="Vigor Máximo / Canopia Cerrada"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
