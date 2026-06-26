"""Version Plotly del glifo Estrella de Riesgo, para la app web interactiva.

Reusa el mismo modelo de datos y la misma codificacion que la version matplotlib:
nucleo = objetivo, radar = numericas, anillo = categoricas, colormap divergente
anclado en la tasa global. Cada glifo es un subplot polar; el conjunto forma los
small multiples interactivos (hover con valores exactos)."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

import datos
from estrella import (TASA_GLOBAL, R_NUCLEO, R_RADAR, R_ANILLO, ABREV, contexto,
                      componer_arcos, oscurecer)

_CMAP = plt.get_cmap("RdBu_r")
_NORM = mcolors.TwoSlopeNorm(vmin=0.06, vcenter=TASA_GLOBAL, vmax=0.46)
GRIS = "rgba(70,70,70,0.22)"


def _rgb(tasa):
    r, g, b, _ = _CMAP(_NORM(tasa))
    return int(r * 255), int(g * 255), int(b * 255)


def color_riesgo(tasa):
    r, g, b = _rgb(tasa)
    return f"rgb({r},{g},{b})"


def color_borde(tasa):
    r, g, b = oscurecer(_CMAP(_NORM(tasa)))
    return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"


def _rgba(tasa, a):
    r, g, b = _rgb(tasa)
    return f"rgba({r},{g},{b},{a})"


def colorscale_riesgo(n=21):
    """Escala de color de riesgo para la leyenda, replicando el colormap divergente
    anclado en la tasa global (mismo que tine los glifos)."""
    ts = np.linspace(0.06, 0.46, n)
    return [[float((t - 0.06) / 0.40), color_riesgo(float(t))] for t in ts]


def _agregar_glifo(fig, seg, ctx, monto_rango, row, col, polar_id, etiquetas=False):
    orden_num, orden_cat = ctx["orden_num"], ctx["orden_cat"]
    ang = [90 - i * 360 / len(orden_num) for i in range(len(orden_num))]
    solido = color_riesgo(seg["tasa_reclamo"])

    # --- estructura (debajo de todo): circulos de percentil y radios ---
    th = list(np.linspace(0, 360, 73))
    r_circ, t_circ = [], []
    for p in (0.25, 0.5, 0.75):
        rr = R_RADAR[0] + p * (R_RADAR[1] - R_RADAR[0])
        r_circ += [rr] * len(th) + [None]
        t_circ += th + [None]
    r_circ += [R_ANILLO[1]] * len(th) + [None]  # borde exterior del glifo
    t_circ += th + [None]
    fig.add_trace(go.Scatterpolar(r=r_circ, theta=t_circ, mode="lines",
        line=dict(color=GRIS, width=0.8), hoverinfo="skip", showlegend=False),
        row=row, col=col)
    r_sp, t_sp = [], []
    for a in ang:
        r_sp += [R_NUCLEO[1], R_RADAR[1], None]
        t_sp += [a, a, None]
    fig.add_trace(go.Scatterpolar(r=r_sp, theta=t_sp, mode="lines",
        line=dict(color=GRIS, width=0.8), hoverinfo="skip", showlegend=False),
        row=row, col=col)

    # --- anillo categorico ---
    paso = 360 / len(orden_cat)
    for i, c in enumerate(orden_cat):
        top = 90 - i * paso
        acum = 0.0
        for etiqueta, prop, tasa in componer_arcos(seg["composicion_categorica"][c], ctx["tasas_cat"][c]):
            centro = top - (acum + prop / 2) * paso
            fig.add_trace(go.Barpolar(
                r=[R_ANILLO[1] - R_ANILLO[0]], theta=[centro], width=[prop * paso],
                base=[R_ANILLO[0]], marker_color=color_riesgo(tasa),
                marker_line_color="white", marker_line_width=0.6,
                hovertemplate=(f"<b>{ABREV[c]}</b><br>{etiqueta}: {prop*100:.0f}%<br>"
                               f"reclamo en {etiqueta}: {tasa*100:.0f}%<extra></extra>"),
                showlegend=False), row=row, col=col)
            acum += prop

    # --- radar numerico (relleno translucido, contorno y vertices nitidos) ---
    rs = [R_RADAR[0] + seg["perfil_numerico"][c] * (R_RADAR[1] - R_RADAR[0]) for c in orden_num]
    texto = [f"{ABREV[c]}<br>percentil {seg['perfil_numerico'][c]*100:.0f}<br>"
             f"media {seg['medias_numericas'][c]:,.1f}" for c in orden_num]
    fig.add_trace(go.Scatterpolar(
        r=rs + [rs[0]], theta=ang + [ang[0]], mode="lines+markers",
        fill="toself", fillcolor=_rgba(seg["tasa_reclamo"], 0.32),
        line=dict(color=color_borde(seg["tasa_reclamo"]), width=2),
        marker=dict(size=6, color=solido, line=dict(color="white", width=0.8)),
        text=texto + [texto[0]], hovertemplate="%{text}<extra></extra>",
        showlegend=False), row=row, col=col)

    # --- nucleo: disco + porcentaje ---
    amin, amax = monto_rango
    frac = (seg["monto_medio"] - amin) / (amax - amin) if amax > amin else 0.5
    r_nuc = R_NUCLEO[0] + np.clip(frac, 0, 1) * (R_NUCLEO[1] - R_NUCLEO[0])
    fig.add_trace(go.Barpolar(
        r=[r_nuc], theta=[0], width=[360], base=[0], marker_color=solido,
        marker_line_color="white", marker_line_width=1,
        hovertemplate=(f"Tasa de reclamo: {seg['tasa_reclamo']*100:.1f}%<br>"
                       f"Monto medio: ${seg['monto_medio']:,.0f}<extra></extra>"),
        showlegend=False), row=row, col=col)
    fig.add_trace(go.Scatterpolar(
        r=[0], theta=[0], mode="text", text=[f"{seg['tasa_reclamo']*100:.0f}%"],
        textfont=dict(color="white", size=12, family="Arial Black"),
        hoverinfo="skip", showlegend=False), row=row, col=col)

    # nombres de variables (sutiles): numericas junto al radar, categoricas fuera del anillo
    if etiquetas:
        rn = (R_RADAR[1] + R_ANILLO[0]) / 2
        fig.add_trace(go.Scatterpolar(
            r=[rn] * len(orden_num), theta=ang, mode="text",
            text=[ABREV[c] for c in orden_num],
            textfont=dict(size=7.5, color="rgba(80,80,80,0.8)"),
            hoverinfo="skip", showlegend=False), row=row, col=col)
        pasoc = 360 / len(orden_cat)
        angc = [90 - (i + 0.5) * pasoc for i in range(len(orden_cat))]
        fig.add_trace(go.Scatterpolar(
            r=[R_ANILLO[1] + 0.08] * len(orden_cat), theta=angc, mode="text",
            text=[ABREV[c] for c in orden_cat],
            textfont=dict(size=8.5, color="rgba(55,55,55,0.95)"),
            hoverinfo="skip", showlegend=False), row=row, col=col)

    rmax = (R_ANILLO[1] + 0.18) if etiquetas else (R_ANILLO[1] + 0.03)
    fig.layout[polar_id].update(
        radialaxis=dict(range=[0, rmax], visible=False),
        angularaxis=dict(visible=False, rotation=0, direction="counterclockwise"),
        bgcolor="white", hole=0)


def figura_segmentos(resumen, ctx, titulos=None, ncols=3, etiquetas=True):
    segs = sorted(resumen)
    n = len(segs)
    ncols = min(ncols, n)
    nrows = int(np.ceil(n / ncols))
    if titulos is None:
        titulos = [f"{s} · reclamo {resumen[s]['tasa_reclamo']*100:.0f}% · n={resumen[s]['n']}"
                   for s in segs]
    fig = make_subplots(rows=nrows, cols=ncols,
                        specs=[[{"type": "polar"} for _ in range(ncols)] for _ in range(nrows)],
                        subplot_titles=titulos, horizontal_spacing=0.03, vertical_spacing=0.10)
    montos = [resumen[s]["monto_medio"] for s in segs]
    rango = (min(montos), max(montos))
    for idx, s in enumerate(segs):
        row, col = idx // ncols + 1, idx % ncols + 1
        pid = "polar" if idx == 0 else f"polar{idx+1}"
        _agregar_glifo(fig, resumen[s], ctx, rango, row, col, pid, etiquetas)

    # leyenda de color (tasa de reclamo), anclada en la media global
    fig.add_trace(go.Scatterpolar(
        r=[0], theta=[0], mode="markers",
        marker=dict(colorscale=colorscale_riesgo(), cmin=0.06, cmax=0.46,
                    color=[TASA_GLOBAL], size=0.1, opacity=0, showscale=True,
                    colorbar=dict(title=dict(text="Tasa de reclamo", side="right"),
                                  tickvals=[0.06, TASA_GLOBAL, 0.46],
                                  ticktext=["6%", "27% (media)", "46%"],
                                  len=0.55, thickness=14, x=1.0, y=0.5,
                                  outlinewidth=0, tickfont=dict(size=10))),
        hoverinfo="skip", showlegend=False), row=1, col=1)

    fig.update_layout(
        height=380 * nrows, margin=dict(t=64, b=20, l=20, r=120),
        paper_bgcolor="white", plot_bgcolor="white", font=dict(size=11),
        title="Estrella de Riesgo — segmentos de asegurados")
    for a in fig.layout.annotations:
        a.font.size = 12
        a.font.color = "#333"
    return fig
