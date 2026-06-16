<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
    xmlns="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>rgb_11_8_4_agriculture</Name>
    <UserStyle>
      <Title>Falso Color Agricultura (11-8-4)</Title>
      <Abstract>SWIR→Rojo, NIR→Verde, Red→Azul</Abstract>
      <FeatureTypeStyle>
        <Name>vegetation_enhancement</Name>
        <Rule>
          <RasterSymbolizer>
            <Opacity>1.0</Opacity>
            <ChannelSelection>
              <RedChannel>
                <SourceChannelName>1</SourceChannelName>
              </RedChannel>
              <GreenChannel>
                <SourceChannelName>2</SourceChannelName>
              </GreenChannel>
              <BlueChannel>
                <SourceChannelName>3</SourceChannelName>
              </BlueChannel>
            </ChannelSelection>
            <ContrastEnhancement>
              <Normalize/>
            </ContrastEnhancement>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
