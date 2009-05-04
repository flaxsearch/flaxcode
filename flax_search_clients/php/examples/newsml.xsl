<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
<html>
<body>
    <h2><xsl:value-of select="newsitem/headline"/></h2>
    <h4><xsl:value-of select="newsitem/byline"/></h4>
    <h4><xsl:value-of select="newsitem/dateline"/></h4>
    <xsl:for-each select="newsitem/text/p">
        <p><xsl:value-of select="current()"/></p>
    </xsl:for-each>
</body>
</html>
</xsl:template>
</xsl:stylesheet>