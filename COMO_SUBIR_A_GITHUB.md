# Cómo subir AGROCOL a GitHub (archivos livianos)

GitHub **en el navegador** falla con archivos ~25 MB ("file is too large").
Solución: usar los CSV **comprimidos** (`.csv.gz` ≈ 1.3 MB cada uno).

## Archivos en `data/`

```
data/Precios_agricolas_consolidados_2019_2024.csv.gz   (~1.3 MB)
data/EVA_COLOMBIA_AGRICOLA.csv.gz                      (~1.4 MB)
```

La app los detecta y carga **automáticamente** al arrancar (modo REAL).

## Opción A – Subir por la web de GitHub (fácil)

1. Crea el repo vacío en github.com.
2. Sube **primero** el código (app.py, src/, requirements.txt, etc.) sin los datos grandes.
3. Entra a la carpeta `data/` del repo en GitHub → **Add file** → **Upload files**.
4. Arrastra solo los dos `.csv.gz` (pesan ~1.3 MB; el navegador los acepta).
5. Commit.

## Opción B – Desde la terminal (recomendado)

```bash
cd agrocol-streamlit
git init
git add .
git status   # deben aparecer los .csv.gz
git commit -m "AGROCOL + datos comprimidos (carga automática)"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/agrocol-streamlit.git
git push -u origin main
```

## Streamlit Cloud

1. https://share.streamlit.io → New app → tu repo
2. Main file: `app.py`
3. Deploy

Al iniciar debe verse: **✅ Modo REAL** en el sidebar.

## Si aún falla el push

```bash
git config http.postBuffer 524288000
git push -u origin main
```

O usa **Git LFS** solo si algún archivo supera 100 MB (no es el caso de los `.gz`).
