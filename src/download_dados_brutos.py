#!/usr/bin/env python3
"""
Script automatizado para download e extração das bases brutas oficiais (PRF e INMET).
Permite reproduzir integralmente a aquisição dos dados a partir dos links originais.
"""

from pathlib import Path
import urllib.request
import ssl
import zipfile
import shutil
import gzip
import json
import csv

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PRF_DIR = BASE_DIR / "data" / "raw" / "prf"
RAW_INMET_DIR = BASE_DIR / "data" / "raw" / "inmet"
RAW_LONDRINA_COMP_DIR = BASE_DIR / "data" / "raw" / "inmet_londrina_complementar"
CACHE_DIR = BASE_DIR.parent / "material" / "downloads_brutos"


def main():
    RAW_PRF_DIR.mkdir(parents=True, exist_ok=True)
    RAW_INMET_DIR.mkdir(parents=True, exist_ok=True)
    RAW_LONDRINA_COMP_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "prf").mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "inmet").mkdir(parents=True, exist_ok=True)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    prf_links = {
        "2022": "1PRQjuV5gOn_nn6UNvaJyVURDIfbSAK4-",
        "2023": "1-WO3SfNrwwZ5_l7fRTiwBKRw7mi1-HUq",
        "2024": "14lB0vqMFkaZj8HZ44b0njYgxs9nAN8KO",
        "2025": "1-G3MdmHBt6CprDwcW99xxC4BZ2DU5ryR",
    }

    for yr, fid in prf_links.items():
        zip_dest = CACHE_DIR / "prf" / f"datatran{yr}.zip"
        if not zip_dest.exists():
            url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
            print(f"Baixando PRF {yr}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=300) as r, open(zip_dest, "wb") as f:
                shutil.copyfileobj(r, f)
        with zipfile.ZipFile(zip_dest) as z:
            for name in z.namelist():
                if name.lower().endswith(".csv"):
                    out_csv = RAW_PRF_DIR / Path(name).name
                    with z.open(name) as src, open(out_csv, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"Extraído: {out_csv}")

    for yr in ["2022", "2023", "2024", "2025"]:
        zip_dest = CACHE_DIR / "inmet" / f"{yr}.zip"
        if not zip_dest.exists():
            url = f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{yr}.zip"
            print(f"Baixando INMET {yr}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=300) as r, open(zip_dest, "wb") as f:
                shutil.copyfileobj(r, f)
        with zipfile.ZipFile(zip_dest) as z:
            for name in z.namelist():
                if any(code in name.upper() for code in ["A835", "A842"]):
                    out_csv = RAW_INMET_DIR / Path(name).name
                    with z.open(name) as src, open(out_csv, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"Extraído: {out_csv}")

    print("Downloads e extrações concluídos com sucesso!")


if __name__ == "__main__":
    main()

