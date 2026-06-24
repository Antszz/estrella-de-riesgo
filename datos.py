from pathlib import Path
import numpy as np
import pandas as pd

NUMERICAS = ["AGE", "YOJ", "INCOME", "HOME_VAL", "TRAVTIME", "BLUEBOOK",
             "TIF", "OLDCLAIM", "MVR_PTS", "CAR_AGE",
             "KIDSDRIV", "HOMEKIDS", "CLM_FREQ"]

CATEGORICAS = ["PARENT1", "MSTATUS", "GENDER", "EDUCATION", "OCCUPATION",
               "CAR_USE", "CAR_TYPE", "RED_CAR", "REVOKED", "URBANICITY"]

ORDEN_EDUCACION = ["<High School", "High School", "Bachelors", "Masters", "PhD"]

OBJETIVO_FLAG = "CLAIM_FLAG"
OBJETIVO_MONTO = "CLM_AMT"

MONETARIAS = ["INCOME", "HOME_VAL", "BLUEBOOK", "OLDCLAIM", "CLM_AMT"]


def localizar_csv(nombre="car_insurance_claim.csv"):
    ruta = Path(nombre)
    if ruta.exists():
        return ruta
    aqui = Path(__file__).resolve().parent
    if (aqui / nombre).exists():
        return aqui / nombre
    for base in [aqui, Path.cwd()]:
        encontrados = list(base.rglob(nombre))
        if encontrados:
            return encontrados[0]
    return ruta


def cargar(nombre="car_insurance_claim.csv"):
    df = pd.read_csv(localizar_csv(nombre))

    for c in MONETARIAS:
        df[c] = df[c].replace(r"[\$,]", "", regex=True).astype(float)

    for c in CATEGORICAS:
        df[c] = df[c].astype(str).str.replace("^z_", "", regex=True).str.strip()
    df["GENDER"] = df["GENDER"].map({"M": "Male", "F": "Female"}).fillna(df["GENDER"])
    df["URBANICITY"] = df["URBANICITY"].str.replace("Highly ", "", regex=False)
    df["URBANICITY"] = df["URBANICITY"].str.split("/").str[0].str.strip()

    df = df.drop(columns=["ID", "BIRTH"], errors="ignore")
    df = df.drop_duplicates().reset_index(drop=True)

    df.loc[df["CAR_AGE"] < 0, "CAR_AGE"] = np.nan

    for c in NUMERICAS:
        df[c] = df[c].fillna(df[c].median())
    for c in CATEGORICAS:
        df[c] = df[c].replace({"nan": "Unknown", "": "Unknown"}).fillna("Unknown")

    return df


def information_value(df, columna, objetivo=OBJETIVO_FLAG, bins=5):
    if columna in NUMERICAS:
        if df[columna].nunique() <= 12:
            grupo = df[columna]
        else:
            try:
                grupo = pd.qcut(df[columna], q=bins, duplicates="drop")
            except ValueError:
                grupo = df[columna]
    else:
        grupo = df[columna]

    tabla = pd.crosstab(grupo, df[objetivo])
    if tabla.shape[1] < 2:
        return 0.0
    buenos = tabla[0].replace(0, 0.5)
    malos = tabla[1].replace(0, 0.5)
    p_buenos = buenos / buenos.sum()
    p_malos = malos / malos.sum()
    woe = np.log(p_buenos / p_malos)
    return float(((p_buenos - p_malos) * woe).sum())


def tabla_iv(df):
    filas = [(c, information_value(df, c)) for c in NUMERICAS + CATEGORICAS]
    iv = pd.DataFrame(filas, columns=["variable", "iv"]).set_index("variable")
    return iv.sort_values("iv", ascending=False)


def matriz_famd(df, n_componentes=5, semilla=0):
    import prince
    famd = prince.FAMD(n_components=n_componentes, random_state=semilla)
    famd = famd.fit(df[NUMERICAS + CATEGORICAS])
    coords = famd.row_coordinates(df[NUMERICAS + CATEGORICAS])
    return famd, coords


def segmentar_clusters(df, k=6, n_componentes=5, semilla=0):
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    k = max(1, min(k, len(df)))
    _, coords = matriz_famd(df, n_componentes, semilla)
    z = StandardScaler().fit_transform(coords.values)
    km = KMeans(n_clusters=k, random_state=semilla, n_init=10)
    etiquetas = km.fit_predict(z)
    tasa = pd.Series(df[OBJETIVO_FLAG].values).groupby(etiquetas).mean()
    orden = {viejo: nuevo for nuevo, viejo in enumerate(tasa.sort_values().index)}
    etiquetas = np.array([orden[e] for e in etiquetas])
    return pd.Series(etiquetas, index=df.index, name="segmento")


def segmentar_por_categoria(df, variable):
    return pd.Series(df[variable].values, index=df.index, name="segmento")


def resumen_segmentos(df, etiquetas):
    resumenes = {}
    etiquetas = pd.Series(np.asarray(etiquetas), index=df.index)
    rangos = {c: df[c].rank(pct=True) for c in NUMERICAS}
    for seg in sorted(pd.unique(etiquetas)):
        mask = (etiquetas == seg).values
        sub = df[mask]
        perfil_num = {c: float(rangos[c][mask].mean()) for c in NUMERICAS}
        comp_cat = {c: sub[c].value_counts(normalize=True).to_dict() for c in CATEGORICAS}
        reclamos = sub[sub[OBJETIVO_FLAG] == 1]
        resumenes[seg] = {
            "n": int(mask.sum()),
            "proporcion": float(mask.mean()),
            "tasa_reclamo": float(sub[OBJETIVO_FLAG].mean()),
            "monto_medio": float(reclamos[OBJETIVO_MONTO].mean()) if len(reclamos) else 0.0,
            "perfil_numerico": perfil_num,
            "composicion_categorica": comp_cat,
            "medias_numericas": {c: float(sub[c].mean()) for c in NUMERICAS},
        }
    return resumenes


def preparar(nombre="car_insurance_claim.csv", k=6, semilla=0):
    df = cargar(nombre)
    iv = tabla_iv(df)
    etiquetas = segmentar_clusters(df, k=k, semilla=semilla)
    resumen = resumen_segmentos(df, etiquetas)
    return df, iv, etiquetas, resumen


if __name__ == "__main__":
    df = cargar()
    print("filas:", len(df), "| columnas:", df.shape[1])
    print("tasa de reclamo global:", round(df[OBJETIVO_FLAG].mean(), 3))
    print("\nInformation Value por variable:")
    print(tabla_iv(df).round(3).to_string())
