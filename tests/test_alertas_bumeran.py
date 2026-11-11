"""Analizador de las alertas de Bumeran, con el formato real de sus correos (RF-REC-03)."""

from radar.collectors.gmail import ANALIZADORES, Correo, analizar_bumeran, analizar_sin_ofertas

TARJETA = """
<a href="https://delivery.bumeran.com/{n}" target="_blank" style="text-decoration: none;">
<div style="margin: 0px 12px;">
<p><span>Nuevo</span><span style="margin-left: 8px;"> Publicado ayer </span></p>
<div><div><h3 style="margin: 0px;"> {titulo} </h3></div></div>
<p><span> {empresa} </span><span><img src="x" /></span></p>
<p><span> {lugar} </span></p>
<p><span> Full-time </span></p>
<p><span> {modalidad} </span></p>
</div></a>
"""


def correo():
    html = "<html><body><p>Hola</p>" + TARJETA.format(
        n="a1", titulo="Especialista en Google Ads", empresa="Agencia Sur",
        lugar="Capital Federal, Buenos Aires", modalidad="Remoto",
    ) + TARJETA.format(
        n="a2", titulo="Trafficker Digital Jr", empresa="Confidencial",
        lugar="Rosario, Santa Fe", modalidad="H&iacute;brido",
    ) + '<a href="https://delivery.bumeran.com/pie">Ver más empleos</a></body></html>'
    return Correo("m1", "Bumeran <no_reply@bumeran.com>", "Postulate", html, "")


def test_lee_una_oferta_por_tarjeta():
    ofertas = analizar_bumeran(correo(), "alertas")
    assert [o.titulo for o in ofertas] == ["Especialista en Google Ads", "Trafficker Digital Jr"]
    primera = ofertas[0]
    assert primera.empresa == "Agencia Sur"
    assert primera.ubicacion == "Capital Federal, Buenos Aires"
    assert primera.url == "https://delivery.bumeran.com/a1"
    assert "Remoto" in primera.descripcion
    assert primera.publicada == "Publicado ayer"
    assert ofertas[1].descripcion.endswith("Híbrido")


def test_el_correo_sin_tarjetas_no_da_ofertas():
    c = Correo("m2", "Bumeran <no_reply@bumeran.com>", "Hola", "<p>Sin avisos</p>", "")
    assert analizar_bumeran(c, "alertas") == []


def test_los_dominios_de_los_portales_tienen_analizador():
    assert ANALIZADORES["bumeran.com"] is analizar_bumeran
    assert ANALIZADORES["computrabajo.com"] is analizar_sin_ofertas
    c = Correo("m3", "Equipo <trabajos_ar@computrabajo.com>", "5 empleos", "<a>Revisa</a>", "")
    assert analizar_sin_ofertas(c, "alertas") == []
