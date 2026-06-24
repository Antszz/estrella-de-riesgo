---
title: Estrella de Riesgo
sdk: docker
app_port: 7860
pinned: false
---

# Estrella de Riesgo

Implementacion de la metafora visual **Estrella de Riesgo** para explorar datos
multidimensionales de tipo mixto, aplicada a un conjunto de reclamos de seguros de
auto. Cada segmento de asegurados se representa como un glifo radial: nucleo =
objetivo (color = tasa de reclamo, tamano = monto), radar = variables numericas
(radio = percentil), anillo = variables categoricas (ancho del arco = proporcion).
Una escala de color divergente anclada en la tasa global (26.7%) tine todo el glifo:
azul = menor riesgo, rojo = mayor riesgo.

Trabajo final del curso de Visualizacion de datos (UCSP).

## App en vivo

> **https://antszz-estrella-de-riesgo.hf.space/**

## Ejecutar con Docker (local)

```
docker build -t estrella-de-riesgo .
docker run -p 8050:8050 estrella-de-riesgo
```

Luego abrir http://localhost:8050

## Ejecutar sin Docker

```
pip install -r requirements.txt
python app.py
```

Abrir http://localhost:8050

## Uso

- **Segmentar por**: perfiles automaticos (clusters FAMD) o por una variable
  categorica (zona, tipo de auto, educacion, ocupacion, estado civil).
- **Numero de perfiles (k)**: ajustable (solo en modo "Perfil de riesgo").
- **Orden de los ejes**: por asociacion con el reclamo (IV) o alfabetico.
- **Filtro de zona**: urbana / rural / todos.
- **Hover**: muestra los valores exactos de cada radio y cada arco.

## Contenido

- `app.py` — aplicacion web (Dash + Plotly).
- `datos.py` — carga, limpieza, Information Value y segmentacion (FAMD + k-means).
- `estrella.py` / `estrella_plotly.py` — el glifo en matplotlib y en Plotly.
- `car_insurance_claim.csv` — dataset.
- `trabajo_final.ipynb` — notebook que documenta el proceso y genera las figuras.
- `Dockerfile` — para construir y desplegar la app.
