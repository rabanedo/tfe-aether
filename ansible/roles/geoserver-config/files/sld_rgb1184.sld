<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
    xsi:schemaLocation="http://opengis.net StyledLayerDescriptor.xsd"
    xmlns="http://opengis.net"
    xmlns:ogc="http://opengis.net"
    xmlns:xlink="http://w3.org"
    xmlns:xsi="http://w3.org">
  <NamedLayer>
    <Name>rgb_11_8_4_agriculture</Name>
    <UserStyle>
      <Title>Falso Color Agricultura (11-8-4)</Title>
      <Abstract>Asignacion de Canales: SWIR (B11) al Rojo, NIR (B8) al Verde, Red (B4) al Azul</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <Opacity>1.0</Opacity>
            <ChannelSelection>
              <RedChannel>
                <SourceChannelName>1</SourceChannelName> <!-- Banda 11 (SWIR) -->
              </RedChannel>
              <GreenChannel>
                <SourceChannelName>2</SourceChannelName> <!-- Banda 8 (NIR) -->
              </GreenChannel>
              <BlueChannel>
                <SourceChannelName>3</SourceChannelName> <!-- Banda 4 (Red) -->
              </BlueChannel>
            </ChannelSelection>
            <!-- Contraste optimizado para resaltar los cultivos en pantalla -->
            <ContrastEnhancement>
              <Normalize/>
            </ContrastEnhancement>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
