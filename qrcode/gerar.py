"""Gera os QR codes da página (SVG e PNG), sem depender do Pillow.

Uso: python gerar.py [URL]
Precisa só da biblioteca `qrcode` (pip install qrcode); o PNG é escrito à mão com zlib.
"""
import struct
import sys
import zlib
from pathlib import Path

import qrcode

URL = sys.argv[1] if len(sys.argv) > 1 else "https://enzozampronio.github.io/proj_em_serv_landingpage/"
PASTA = Path(__file__).resolve().parent
ESCALA_PNG = 30  # px por módulo: ~1200 px de lado, nítido em slide de tela cheia

# Tinta sobre papel, nas cores da página; e um de alto contraste para projetor que desbota o azul.
VERSOES = {
    "qrcode": ("#2036CE", "#F2F0E6"),
    "qrcode-contraste": ("#111111", "#FFFFFF"),
}


def matriz(url):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.get_matrix()  # já inclui a borda branca de 4 módulos


def svg(m, escuro, claro):
    n = len(m)
    caminho = "".join(f"M{x} {y}h1v1h-1z" for y, linha in enumerate(m) for x, v in enumerate(linha) if v)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
        f'<rect width="{n}" height="{n}" fill="{claro}"/><path fill="{escuro}" d="{caminho}"/></svg>\n'
    )


def png(m, escuro, claro, escala):
    rgb = lambda h: bytes.fromhex(h.lstrip("#"))
    cor = {True: rgb(escuro), False: rgb(claro)}
    lado = len(m) * escala
    linhas = bytearray()
    for linha in m:
        pixels = b"".join(cor[v] * escala for v in linha)
        for _ in range(escala):
            linhas += b"\x00" + pixels  # filtro 0 em cada linha

    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    return (
        b"\x89PNG\r\n\x1a\n"
        + bloco(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 2, 0, 0, 0))
        + bloco(b"IDAT", zlib.compress(bytes(linhas), 9))
        + bloco(b"IEND", b"")
    )


m = matriz(URL)
for nome, (escuro, claro) in VERSOES.items():
    (PASTA / f"{nome}.svg").write_text(svg(m, escuro, claro))
    (PASTA / f"{nome}.png").write_bytes(png(m, escuro, claro, ESCALA_PNG))
print(f"QR code ({len(m)}x{len(m)} módulos) gerado para {URL}")
