#!/usr/bin/env python3
"""
Script automatizado para download e extração das bases brutas oficiais (PRF e INMET).
Permite reproduzir integralmente a aquisição dos dados a partir dos links originais:
1. PRF Ocorrências (datatran2022..2025.zip)
2. PRF Pessoas e Veículos (acidentes2022..2025_pessoa.zip -> filtro Londrina-PR)
3. INMET Estações Automáticas Históricas (2022..2025.zip -> A835 e A842)
4. Série Local Oficial de Londrina (INMET Convencional 83766, Aeroporto SBLO 83768 e ERA5)
"""

import argparse
import csv
import gzip
import json
import shutil
import ssl
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PRF_DIR = BASE_DIR / "data" / "raw" / "prf"
RAW_INMET_DIR = BASE_DIR / "data" / "raw" / "inmet"
RAW_LONDRINA_COMP_DIR = BASE_DIR / "data" / "raw" / "inmet_londrina_complementar"
CACHE_DIR = BASE_DIR.parent / "material" / "downloads_brutos"

PRF_OCORRENCIAS_IDS = {
    "2022": "1PRQjuV5gOn_nn6UNvaJyVURDIfbSAK4-",
    "2023": "1-WO3SfNrwwZ5_l7fRTiwBKRw7mi1-HUq",
    "2024": "14lB0vqMFkaZj8HZ44b0njYgxs9nAN8KO",
    "2025": "1-G3MdmHBt6CprDwcW99xxC4BZ2DU5ryR",
}

PRF_PESSOAS_IDS = {
    "2022": "1sd8YIqIHapYaxQeaa-6yeWMdVLTl6hgD",
    "2023": "1-Yk6TV00CH3PixTkKmkoUJQsNiUc5xLm",
    "2024": "14lVfqdoE2gxDliaKZu7K9Mx6847maPtl",
    "2025": "1-Gp9S-ALO0D1nT8S_OKoC8xlW7BY8F82",
}

METEOSTAT_STATIONS = [
    ("83766", "inmet_convencional_83766_londrina_diario_2022_2025.csv"),
    ("83768", "aeroporto_sblo_83768_londrina_diario_2022_2025.csv"),
]


def _build_ssl_context() -> ssl.SSLContext:
    """Cria contexto SSL compatível para downloads de portais governamentais."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _download_file(url: str, dest: Path, ctx: ssl.SSLContext, label: str, force: bool = False) -> None:
    """Baixa um arquivo remoto para `dest` caso ainda não exista localmente."""
    if dest.exists() and dest.stat().st_size > 1000 and not force:
        return
    print(f"Baixando {label}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=300) as resp, open(dest, "wb") as fout:
        shutil.copyfileobj(resp, fout)


def download_and_extract_prf_ocorrencias(ctx: ssl.SSLContext, force: bool = False) -> None:
    """Baixa e extrai os microdados anuais de ocorrências da PRF (`datatranYYYY.csv`)."""
    for yr, fid in PRF_OCORRENCIAS_IDS.items():
        zip_dest = CACHE_DIR / "prf" / f"datatran{yr}.zip"
        url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
        _download_file(url, zip_dest, ctx, f"PRF Ocorrências {yr}", force=force)
        with zipfile.ZipFile(zip_dest) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".csv"):
                    out_csv = RAW_PRF_DIR / Path(name).name
                    if not out_csv.exists() or force:
                        with zf.open(name) as src, open(out_csv, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        print(f"Extraído: {out_csv}")


def download_and_extract_prf_pessoas(ctx: ssl.SSLContext, force: bool = False) -> None:
    """Baixa os microdados por pessoa/veículo da PRF e extrai o recorte de Londrina-PR."""
    for yr, fid in PRF_PESSOAS_IDS.items():
        out_csv = RAW_PRF_DIR / f"acidentes{yr}_pessoa_londrina.csv"
        if out_csv.exists() and not force:
            continue
        zip_dest = CACHE_DIR / "prf" / f"acidentes{yr}_pessoa.zip"
        url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
        _download_file(url, zip_dest, ctx, f"PRF Pessoas/Veículos {yr}", force=force)
        with zipfile.ZipFile(zip_dest) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                continue
            with zf.open(csv_names[0]) as fin, open(out_csv, "w", encoding="latin-1") as fout:
                header = fin.readline().decode("latin-1")
                fout.write(header)
                count = 0
                for raw_line in fin:
                    line = raw_line.decode("latin-1", errors="ignore")
                    upper = line.upper()
                    if ";LONDRINA;" in upper or ';"LONDRINA";' in upper:
                        fout.write(line)
                        count += 1
        print(f"Extraído recorte Londrina ({count} linhas): {out_csv}")


def download_and_extract_inmet_auto(ctx: ssl.SSLContext, force: bool = False) -> None:
    """Baixa os arquivos históricos do INMET e extrai as estações automáticas A835 e A842."""
    for yr in ["2022", "2023", "2024", "2025"]:
        zip_dest = CACHE_DIR / "inmet" / f"{yr}.zip"
        url = f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{yr}.zip"
        _download_file(url, zip_dest, ctx, f"INMET Automáticas {yr}", force=force)
        with zipfile.ZipFile(zip_dest) as zf:
            for name in zf.namelist():
                if any(code in name.upper() for code in ["A835", "A842"]):
                    out_csv = RAW_INMET_DIR / Path(name).name
                    if not out_csv.exists() or force:
                        with zf.open(name) as src, open(out_csv, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        print(f"Extraído: {out_csv}")


def download_londrina_complementary(ctx: ssl.SSLContext, force: bool = False) -> None:
    """Baixa as séries diárias locais de Londrina (INMET 83766, SBLO 83768 e Open-Meteo ERA5)."""
    cols_daily = [
        "data", "tavg_c", "tmin_c", "tmax_c", "precip_mm", "neve_mm",
        "vento_dir_graus", "vento_vel_kmh", "vento_rajada_kmh", "pressao_hpa", "insolacao_min",
    ]
    for st_code, fname in METEOSTAT_STATIONS:
        out_path = RAW_LONDRINA_COMP_DIR / fname
        if out_path.exists() and not force:
            continue
        url = f"https://bulk.meteostat.net/v2/daily/{st_code}.csv.gz"
        print(f"Baixando série diária OMM/INMET {st_code}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = gzip.decompress(urllib.request.urlopen(req, context=ctx, timeout=60).read()).decode("utf-8")
        rows = [ln.split(",") for ln in raw.splitlines() if ln.startswith(("2022", "2023", "2024", "2025"))]
        with open(out_path, "w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout)
            writer.writerow(cols_daily)
            writer.writerows(rows)
        print(f"Salvo ({len(rows)} dias): {out_path}")

    out_om = RAW_LONDRINA_COMP_DIR / "openmeteo_era5_londrina_diario_2022_2025.csv"
    if not out_om.exists() or force:
        om_url = (
            "https://archive-api.open-meteo.com/v1/archive?"
            "latitude=-23.3103&longitude=-51.1628&start_date=2022-01-01&end_date=2025-12-31&"
            "daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
            "precipitation_sum,rain_sum,precipitation_hours,wind_speed_10m_max&"
            "timezone=America%2FSao_Paulo"
        )
        print("Baixando reanálise Open-Meteo / ERA5 para Londrina...")
        req = urllib.request.Request(om_url, headers={"User-Agent": "Mozilla/5.0"})
        daily_data = json.loads(urllib.request.urlopen(req, context=ctx, timeout=60).read().decode("utf-8"))["daily"]
        keys = list(daily_data.keys())
        with open(out_om, "w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout)
            writer.writerow(keys)
            for idx in range(len(daily_data["time"])):
                writer.writerow([daily_data[k][idx] for k in keys])
        print(f"Salvo ({len(daily_data['time'])} dias): {out_om}")


def main(force: bool = False) -> None:
    RAW_PRF_DIR.mkdir(parents=True, exist_ok=True)
    RAW_INMET_DIR.mkdir(parents=True, exist_ok=True)
    RAW_LONDRINA_COMP_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "prf").mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "inmet").mkdir(parents=True, exist_ok=True)

    ctx = _build_ssl_context()
    download_and_extract_prf_ocorrencias(ctx, force=force)
    download_and_extract_prf_pessoas(ctx, force=force)
    download_and_extract_inmet_auto(ctx, force=force)
    download_londrina_complementary(ctx, force=force)
    print("Verificação, downloads e extrações concluídos com sucesso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download e extração reprodutível das bases PRF e INMET.")
    parser.add_argument("--force", action="store_true", help="Força novo download/extração mesmo se os arquivos já existirem.")
    args = parser.parse_args()
    main(force=args.force)

