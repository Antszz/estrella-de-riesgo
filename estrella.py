import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Wedge, Circle, Polygon

import datos

TASA_GLOBAL = 0.267
R_NUCLEO = (0.085, 0.165)
R_RADAR = (0.18, 0.66)
R_ANILLO = (0.70, 0.92)

ABREV = {
    "AGE": "Edad", "YOJ": "AntEmp", "INCOME": "Ingreso", "HOME_VAL": "ValCasa",
    "TRAVTIME": "Trayecto", "BLUEBOOK": "ValAuto", "TIF": "Antig", "OLDCLAIM": "ReclPrev",
    "MVR_PTS": "Puntos", "CAR_AGE": "EdadAuto", "KIDSDRIV": "HijosCond",
    "HOMEKIDS": "Hijos", "CLM_FREQ": "FrecRecl",
    "PARENT1": "MonoParent", "MSTATUS": "Casado", "GENDER": "Sexo",
    "EDUCATION": "Educacion", "OCCUPATION": "Ocupacion", "CAR_USE": "UsoAuto",
    "CAR_TYPE": "TipoAuto", "RED_CAR": "AutoRojo", "REVOKED": "LicRevoc",
    "URBANICITY": "Zona",
}


def oscurecer(color, f=0.68):
    r, g, b = mcolors.to_rgb(color)
    return (r * f, g * f, b * f)


def componer_arcos(comp, tasas_c, umbral=0.05):
    grandes = [(k, p) for k, p in comp.items() if p >= umbral]
    chicas = [(k, p) for k, p in comp.items() if 0 < p < umbral]
    arcos = [(k, p, tasas_c.get(k, TASA_GLOBAL)) for k, p in grandes]
    if chicas:
        total = sum(p for _, p in chicas)
        tasa = sum(p * tasas_c.get(k, TASA_GLOBAL) for k, p in chicas) / total
        arcos.append(("Otros", total, tasa))
    arcos.sort(key=lambda x: x[2])
    return arcos


def contexto(df, orden="iv"):
    cmap = plt.get_cmap("RdBu_r")
    norm = mcolors.TwoSlopeNorm(vmin=0.06, vcenter=TASA_GLOBAL, vmax=0.46)

    if orden == "iv":
        iv = datos.tabla_iv(df)
        orden_num = [c for c in iv.index if c in datos.NUMERICAS]
        orden_cat = [c for c in iv.index if c in datos.CATEGORICAS]
    else:
        orden_num, orden_cat = list(datos.NUMERICAS), list(datos.CATEGORICAS)

    tasas_cat = {}
    for c in datos.CATEGORICAS:
        tasas_cat[c] = df.groupby(c)[datos.OBJETIVO_FLAG].mean().to_dict()

    return {"cmap": cmap, "norm": norm, "orden_num": orden_num,
            "orden_cat": orden_cat, "tasas_cat": tasas_cat}


def _angulos(n, inicio=90):
    return [np.deg2rad(inicio - i * 360 / n) for i in range(n)]


def dibujar(ax, seg, ctx, monto_rango, etiquetas=False, titulo=None):
    cmap, norm = ctx["cmap"], ctx["norm"]
    orden_num, orden_cat = ctx["orden_num"], ctx["orden_cat"]
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.axis("off")

    for p in (0.25, 0.5, 0.75):
        r = R_RADAR[0] + p * (R_RADAR[1] - R_RADAR[0])
        ax.add_artist(plt.Circle((0, 0), r, fill=False, color="0.85", lw=0.6, zorder=1))
    ax.add_artist(plt.Circle((0, 0), R_ANILLO[1], fill=False, color="0.8", lw=0.9, zorder=1))

    ang = _angulos(len(orden_num))
    perfil = seg["perfil_numerico"]
    pts = []
    for a, c in zip(ang, orden_num):
        r = R_RADAR[0] + perfil[c] * (R_RADAR[1] - R_RADAR[0])
        pts.append((r * np.cos(a), r * np.sin(a)))
        ax.plot([R_NUCLEO[1] * np.cos(a), R_RADAR[1] * np.cos(a)],
                [R_NUCLEO[1] * np.sin(a), R_RADAR[1] * np.sin(a)],
                color="0.9", lw=0.5, zorder=1)
    col_seg = cmap(norm(seg["tasa_reclamo"]))
    borde = oscurecer(col_seg)
    ax.add_patch(Polygon(pts, closed=True, facecolor=col_seg, alpha=0.32,
                         edgecolor=borde, lw=1.7, zorder=3))
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=12,
               color=borde, edgecolor="white", lw=0.4, zorder=4)

    paso = 360 / len(orden_cat)
    for i, c in enumerate(orden_cat):
        theta_top = 90 - i * paso
        arcos = componer_arcos(seg["composicion_categorica"][c], ctx["tasas_cat"][c])
        acum = 0.0
        for etiqueta, prop, tasa in arcos:
            t2 = theta_top - acum * paso
            t1 = theta_top - (acum + prop) * paso
            ax.add_patch(Wedge((0, 0), R_ANILLO[1], t1, t2,
                               width=R_ANILLO[1] - R_ANILLO[0],
                               facecolor=cmap(norm(tasa)), edgecolor="white", lw=0.4, zorder=2))
            acum += prop
        a0 = np.deg2rad(theta_top)
        ax.plot([R_ANILLO[0] * np.cos(a0), R_ANILLO[1] * np.cos(a0)],
                [R_ANILLO[0] * np.sin(a0), R_ANILLO[1] * np.sin(a0)],
                color="white", lw=1.2, zorder=3)
        if etiquetas:
            am = np.deg2rad(theta_top - paso / 2)
            rl = R_ANILLO[1] + 0.07
            ax.text(rl * np.cos(am), rl * np.sin(am), ABREV[c], fontsize=8.5,
                    ha="center", va="center", rotation=0, color="0.2")

    if etiquetas:
        for a, c in zip(ang, orden_num):
            rl = R_RADAR[1] + 0.02
            ax.text(rl * np.cos(a), rl * np.sin(a), ABREV[c], fontsize=7.5,
                    ha="center", va="center", color="0.3")

    amin, amax = monto_rango
    if amax > amin:
        frac = (seg["monto_medio"] - amin) / (amax - amin)
    else:
        frac = 0.5
    r_nuc = R_NUCLEO[0] + np.clip(frac, 0, 1) * (R_NUCLEO[1] - R_NUCLEO[0])
    ax.add_patch(Circle((0, 0), r_nuc, facecolor=cmap(norm(seg["tasa_reclamo"])),
                        edgecolor=oscurecer(cmap(norm(seg["tasa_reclamo"]))), lw=1.2, zorder=5))
    ax.text(0, 0, f"{seg['tasa_reclamo']*100:.0f}%", ha="center", va="center",
            fontsize=8.5, fontweight="bold", color="white", zorder=6)

    if titulo:
        ax.set_title(titulo, fontsize=10, pad=4)
