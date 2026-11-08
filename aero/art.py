"""Illustration vectorielle de la page d'accueil : soufflante de turboréacteur vue de face."""
from __future__ import annotations

import base64
import math


def _point(rayon: float, angle: float) -> tuple[float, float]:
    return 200 + rayon * math.cos(angle), 200 + rayon * math.sin(angle)


def _pale(index: int, nombre: int) -> str:
    a = index / nombre * math.tau
    pas = math.tau / nombre
    x1, y1 = _point(46, a - pas * 0.26)
    x2, y2 = _point(150, a + pas * 0.40)
    cx, cy = _point(100, a - pas * 0.32)
    x3, y3 = _point(150, a + pas * 0.92)
    x4, y4 = _point(46, a + pas * 0.26)
    cx2, cy2 = _point(106, a + pas * 0.46)
    teinte = "url(#p1)" if index % 2 else "url(#p2)"
    return (
        f'<path d="M{x1:.1f} {y1:.1f} Q{cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f} '
        f'L{x3:.1f} {y3:.1f} Q{cx2:.1f} {cy2:.1f} {x4:.1f} {y4:.1f}Z" fill="{teinte}" '
        f'stroke="#0B1F3A" stroke-opacity=".28" stroke-width=".6"/>'
    )


def _graduations() -> str:
    # Couronne graduée, clin d'œil aux instruments de métrologie de l'atelier.
    traits = []
    for i in range(120):
        a = i / 120 * math.tau
        long_trait = i % 10 == 0
        x1, y1 = _point(187, a)
        x2, y2 = _point(197 if long_trait else 192, a)
        traits.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{"#F59E0B" if long_trait else "#0B1F3A"}" stroke-opacity="{1 if long_trait else .35}" '
            f'stroke-width="{1.6 if long_trait else .7}"/>'
        )
    return "".join(traits)


def turbine_svg() -> str:
    pales = "".join(_pale(i, 26) for i in range(26))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
<style>
.r{{transform-origin:200px 200px;animation:s 16s linear infinite}}
.c{{transform-origin:200px 200px;animation:s 90s linear infinite reverse}}
@keyframes s{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion:reduce){{.r,.c{{animation:none}}}}
</style>
<defs>
<linearGradient id="p1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F4F7FF"/><stop offset="1" stop-color="#9FB2D3"/></linearGradient>
<linearGradient id="p2" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E3E9F7"/><stop offset="1" stop-color="#7F95BC"/></linearGradient>
<linearGradient id="n" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2A4A78"/><stop offset=".5" stop-color="#0B1F3A"/><stop offset="1" stop-color="#3C5E90"/></linearGradient>
<radialGradient id="h" cx=".38" cy=".32" r=".85"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".55" stop-color="#C5D1E8"/><stop offset="1" stop-color="#5E76A0"/></radialGradient>
<radialGradient id="f" cx=".5" cy=".5" r=".5"><stop offset=".3" stop-color="#16325A"/><stop offset="1" stop-color="#0B1F3A"/></radialGradient>
</defs>
<g class="c">{_graduations()}</g>
<circle cx="200" cy="200" r="175" fill="none" stroke="url(#n)" stroke-width="15"/>
<circle cx="200" cy="200" r="168" fill="none" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="1"/>
<circle cx="200" cy="200" r="166" fill="url(#f)"/>
<g class="r">{pales}
<circle cx="200" cy="200" r="50" fill="#0B1F3A"/>
<circle cx="200" cy="200" r="44" fill="url(#h)"/>
<path d="M200 164 C226 176 226 204 204 212 C190 216 182 204 190 196" fill="none" stroke="#0B1F3A" stroke-width="3" stroke-linecap="round"/>
</g>
</svg>"""


LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
<rect width="48" height="48" rx="13" fill="#0B1F3A"/>
<path d="M36.6 11.4c-1.5-1.5-3.8-1.2-5.2.2l-5.6 5.6-14-4.2-2.4 2.4 11.4 7-5.8 5.8-4.2-.8-1.9 1.9 6.1 3.4 3.4 6.1 1.9-1.9-.8-4.2 5.8-5.8 7 11.4 2.4-2.4-4.2-14 5.6-5.6c1.4-1.4 1.7-3.7.5-5.1z" fill="#F59E0B"/>
</svg>"""


def data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
