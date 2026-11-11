#!/usr/bin/env python3
"""
Pipeline de ETL (Extração, Transformação e Carga) e Qualidade de Dados
Projeto: Observatório de Londrina - Clima e Sinistros Rodoviários (PRF + INMET)
Autores: Caio Gabriel Duque Cotting e Victor Gomes Cardoso
Disciplina: Ciência de Dados / Machine Learning - Prof. Mário Henrique Akihiko da Costa Adaniya

Regra de Ouro (Encontro 01, Slide 39):
"Nunca altere os dados brutos. Registre todas as transformações em código."
"""

from pathlib import Path
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PRF_DIR = BASE_DIR / "data" / "raw" / "prf"
RAW_INMET_DIR = BASE_DIR / "data" / "raw" / "inmet"
RAW_LONDRINA_COMP_DIR = BASE_DIR / "data" / "raw" / "inmet_londrina_complementar"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ATIVIDADE2_DIR = BASE_DIR / "Atividade 2"

DIAS_SEMANA_PT = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}

METEO_COLS_FOR_JOIN = [
    "data",
    "temp_media_c",
    "temp_min_c",
    "temp_max_c",
    "amplitude_termica_c",
    "precip_londrina_mm",
    "fonte_precip_londrina",
    "inmet_83766_precip_mm",
    "era5_londrina_precip_mm",
    "a835_precip_mm",
    "a835_temp_media_c",
    "dia_chuvoso_londrina",
    "dia_chuvoso_a835",
    "faixa_precipitacao",
    "faixa_temperatura_media",
    "faixa_temperatura_maxima",
]


def _clean_decimal_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Converte colunas numéricas formatadas com vírgula decimal para float."""
    for col in cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.strip().str.replace(",", ".", regex=False),
            errors="coerce",
        )
    return df


def map_modal_categoria(tipo_veiculo: object, tipo_envolvido: object) -> str:
    """Agrupa `tipo_veiculo` e `tipo_envolvido` em modais analíticos padronizados."""
    env = str(tipo_envolvido).strip()
    if env == "Pedestre":
        return "Pedestre"
    veic = str(tipo_veiculo).strip()
    if veic in ["Motocicleta", "Motoneta", "Ciclomotor", "Triciclo"]:
        return "Moto"
    if veic in ["Automóvel", "Caminhonete", "Camioneta", "Utilitário"]:
        return "Carro"
    if veic in ["Caminhão", "Caminhão-trator", "Reboque", "Semi-reboque", "Semireboque"]:
        return "Caminhão"
    if veic == "Bicicleta":
        return "Bicicleta"
    if veic in ["Ônibus", "Micro-ônibus"]:
        return "Ônibus"
    return "Outros"


def clean_sexo_label(sexo: object) -> str:
    """Padroniza a variável categórica de sexo dos envolvidos na PRF."""
    txt = str(sexo).strip()
    if "Masc" in txt:
        return "Masculino"
    if "Fem" in txt:
        return "Feminino"
    return "Não Informado / Ignorado"


def load_prf_londrina(years=(2022, 2023, 2024, 2025)) -> pd.DataFrame:
    """
    Carrega os arquivos brutos anuais da PRF (datatranYYYY.csv),
    filtra para o município de Londrina (PR) e padroniza tipos e formatos.
    """
    frames = []
    for yr in years:
        fpath = RAW_PRF_DIR / f"datatran{yr}.csv"
        df = pd.read_csv(fpath, sep=";", encoding="latin-1", low_memory=False)
        # Filtrar município == LONDRINA (padronizando maiúsculas e espaços)
        mask = df["municipio"].astype(str).str.strip().str.upper() == "LONDRINA"
        df_lond = df.loc[mask].copy()
        df_lond["ano_arquivo"] = yr
        frames.append(df_lond)

    prf = pd.concat(frames, ignore_index=True)

    # Padronização de data (ISO-8601: YYYY-MM-DD)
    prf["data"] = pd.to_datetime(prf["data_inversa"].astype(str).str.strip(), format="%Y-%m-%d")

    # Conversão de coordenadas e km (vírgula decimal -> ponto decimal)
    prf = _clean_decimal_columns(prf, ["km", "latitude", "longitude"])

    # Colunas inteiras de contagem
    int_cols = [
        "pessoas",
        "mortos",
        "feridos_leves",
        "feridos_graves",
        "ilesos",
        "ignorados",
        "feridos",
        "veiculos",
    ]
    for col in int_cols:
        prf[col] = pd.to_numeric(prf[col], errors="coerce").fillna(0).astype(int)

    # Limpeza de strings categóricas
    str_cols = [
        "dia_semana",
        "uf",
        "br",
        "municipio",
        "causa_acidente",
        "tipo_acidente",
        "classificacao_acidente",
        "fase_dia",
        "sentido_via",
        "condicao_metereologica",
        "tipo_pista",
        "tracado_via",
        "uso_solo",
    ]
    for col in str_cols:
        prf[col] = prf[col].astype(str).str.strip()

    # Flags de severidade e condição climática reportada pelo agente da PRF
    prf["tem_vitima"] = ((prf["feridos"] > 0) | (prf["mortos"] > 0)).astype(int)
    prf["tem_grave_ou_morte"] = ((prf["feridos_graves"] > 0) | (prf["mortos"] > 0)).astype(int)
    prf["tem_obito"] = (prf["mortos"] > 0).astype(int)
    prf["condicao_tempo_adverso_prf"] = prf["condicao_metereologica"].isin(
        ["Chuva", "Garoa/Chuvisco", "Nevoeiro/Neblina"]
    ).astype(int)
    prf["condicao_chuva_prf"] = prf["condicao_metereologica"].isin(
        ["Chuva", "Garoa/Chuvisco"]
    ).astype(int)

    prf = prf.sort_values(["data", "horario", "id"]).reset_index(drop=True)
    return prf


def aggregate_prf_daily(prf: pd.DataFrame, start_date="2022-01-01", end_date="2025-12-31") -> pd.DataFrame:
    """
    Agrega os sinistros individuais da PRF para a unidade de análise do projeto:
    1 linha = 1 dia civil em Londrina (incluindo dias com 0 acidentes).
    """
    grouped = (
        prf.groupby("data")
        .agg(
            total_acidentes=("id", "count"),
            acidentes_br369=("br", lambda s: (s == "369").sum()),
            acidentes_com_vitimas=("tem_vitima", "sum"),
            acidentes_graves_ou_fatais=("tem_grave_ou_morte", "sum"),
            acidentes_fatais=("tem_obito", "sum"),
            acidentes_chuva_prf=("condicao_chuva_prf", "sum"),
            acidentes_tempo_adverso_prf=("condicao_tempo_adverso_prf", "sum"),
            total_pessoas=("pessoas", "sum"),
            total_veiculos=("veiculos", "sum"),
            total_mortos=("mortos", "sum"),
            total_feridos_graves=("feridos_graves", "sum"),
            total_feridos_leves=("feridos_leves", "sum"),
            total_feridos=("feridos", "sum"),
            total_ilesos=("ilesos", "sum"),
        )
        .reset_index()
    )

    # Criar calendário completo para não descartar dias sem acidentes (Slide 34: "Quem não aparece também conta")
    calendar = pd.DataFrame({"data": pd.date_range(start_date, end_date, freq="D")})
    daily = calendar.merge(grouped, on="data", how="left")

    count_cols = [c for c in daily.columns if c != "data"]
    daily[count_cols] = daily[count_cols].fillna(0).astype(int)
    return daily


def _read_raw_inmet_hourly(station_code="A835", years=(2022, 2023, 2024, 2025)) -> pd.DataFrame:
    """
    Lê e limpa os registros horários brutos de estação automática do INMET (ex: A835),
    retornando as colunas meteorológicas tratadas e o timestamp local (America/Sao_Paulo).
    """
    frames = []
    for yr in years:
        matches = list(RAW_INMET_DIR.glob(f"*{station_code}*{yr}*.CSV"))
        if not matches:
            continue
        df = pd.read_csv(
            matches[0],
            sep=";",
            encoding="latin-1",
            skiprows=8,
            decimal=",",
            na_values=["-9999", "-9999.0", "-9999,0", ""],
        )
        df["ano_arquivo"] = yr
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)

    # Renomear colunas principais por posição (padrão INMET automático)
    col_map = {
        raw.columns[0]: "data_str",
        raw.columns[1]: "hora_utc_str",
        raw.columns[2]: "precip_horaria_mm",
        raw.columns[3]: "pressao_estacao_mb",
        raw.columns[6]: "radiacao_kj_m2",
        raw.columns[7]: "temp_ar_c",
        raw.columns[8]: "temp_orvalho_c",
        raw.columns[9]: "temp_max_ant_c",
        raw.columns[10]: "temp_min_ant_c",
        raw.columns[15]: "umid_rel_pct",
        raw.columns[17]: "vento_rajada_ms",
        raw.columns[18]: "vento_vel_ms",
    }
    raw = raw.rename(columns=col_map)

    for c in [
        "precip_horaria_mm",
        "pressao_estacao_mb",
        "temp_ar_c",
        "temp_max_ant_c",
        "temp_min_ant_c",
        "umid_rel_pct",
        "vento_rajada_ms",
        "vento_vel_ms",
    ]:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
        if c in ("precip_horaria_mm", "umid_rel_pct", "vento_vel_ms", "vento_rajada_ms"):
            raw.loc[raw[c] < 0, c] = np.nan
        if c in ("temp_ar_c", "temp_max_ant_c", "temp_min_ant_c"):
            raw.loc[raw[c] < -50, c] = np.nan

    hora_clean = (
        raw["hora_utc_str"]
        .astype(str)
        .str.replace(" UTC", "", regex=False)
        .str.replace(":", "", regex=False)
        .str.strip()
        .str.zfill(4)
    )
    dt_utc = pd.to_datetime(
        raw["data_str"].astype(str).str.strip().str.replace("/", "-", regex=False)
        + " "
        + hora_clean.str[:2]
        + ":"
        + hora_clean.str[2:],
        format="%Y-%m-%d %H:%M",
        utc=True,
    )
    dt_local = dt_utc.dt.tz_convert("America/Sao_Paulo")
    raw["data"] = pd.to_datetime(dt_local.dt.date)
    raw["ano"] = dt_local.dt.year
    raw["hora_local"] = dt_local.dt.hour
    return raw


def compute_inmet_hourly_rain_stats(
    station_code="A835",
    years=(2022, 2023, 2024),
) -> tuple[dict, pd.DataFrame]:
    """
    Calcula a fração real de horas com precipitação (> 0 mm) na série horária do INMET,
    explicando por que médias de dias inteiros (24h) subestimam o risco da hora chuvosa.
    """
    raw = _read_raw_inmet_hourly(station_code=station_code, years=years)
    valid = raw[raw["precip_horaria_mm"].notna()].copy()
    valid["teve_chuva"] = (valid["precip_horaria_mm"] > 0).astype(int)

    n_valid = int(len(valid))
    n_rain = int(valid["teve_chuva"].sum())
    by_hour = (
        valid.groupby("hora_local")
        .agg(
            horas_validas=("precip_horaria_mm", "count"),
            horas_com_chuva=("teve_chuva", "sum"),
            precip_media_mm=("precip_horaria_mm", "mean"),
        )
        .reset_index()
    )
    by_hour["pct_horas_chuva"] = (by_hour["horas_com_chuva"] / by_hour["horas_validas"] * 100.0).round(2)

    summary = {
        "estacao": station_code,
        "periodo": f"{min(years)}-{max(years)}",
        "horas_validas": n_valid,
        "horas_com_chuva": n_rain,
        "fracao_horas_chuva_pct": round(n_rain / n_valid * 100.0, 2) if n_valid else 0.0,
    }
    return summary, by_hour


def load_inmet_automatic_station(station_code="A835", years=(2022, 2023, 2024, 2025)) -> pd.DataFrame:
    """
    Agrega os registros horários da estação automática do INMET (convertidos para GMT-3)
    para o nível diário civil em Londrina.
    """
    raw = _read_raw_inmet_hourly(station_code=station_code, years=years)

    prefix = station_code.lower()
    daily = (
        raw.groupby("data")
        .agg(
            **{
                f"{prefix}_horas_validas_temp": ("temp_ar_c", lambda s: s.notna().sum()),
                f"{prefix}_horas_validas_precip": ("precip_horaria_mm", lambda s: s.notna().sum()),
                f"{prefix}_precip_mm": ("precip_horaria_mm", lambda s: s.sum(min_count=12)),
                f"{prefix}_temp_media_c": ("temp_ar_c", lambda s: s.mean() if s.notna().sum() >= 12 else np.nan),
                f"{prefix}_temp_max_c": ("temp_max_ant_c", lambda s: s.max() if s.notna().sum() >= 12 else np.nan),
                f"{prefix}_temp_min_c": ("temp_min_ant_c", lambda s: s.min() if s.notna().sum() >= 12 else np.nan),
                f"{prefix}_umid_media_pct": ("umid_rel_pct", lambda s: s.mean() if s.notna().sum() >= 12 else np.nan),
                f"{prefix}_vento_max_ms": ("vento_rajada_ms", lambda s: s.max() if s.notna().sum() >= 12 else np.nan),
            }
        )
        .reset_index()
    )
    return daily


def load_londrina_meteorological_series() -> pd.DataFrame:
    """
    Carrega e integra as séries meteorológicas diárias medidas diretamente em Londrina:
    1. Estação Convencional Oficial do INMET em Londrina (Código OMM/INMET 83766)
    2. Estação Meteorológica do Aeroporto de Londrina - SBLO (Código OMM 83768)
    3. Reanálise de alta resolução Open-Meteo / ERA5 para Londrina (-23.3103, -51.1628)
    """
    df_83766 = pd.read_csv(RAW_LONDRINA_COMP_DIR / "inmet_convencional_83766_londrina_diario_2022_2025.csv")
    df_83768 = pd.read_csv(RAW_LONDRINA_COMP_DIR / "aeroporto_sblo_83768_londrina_diario_2022_2025.csv")
    df_om = pd.read_csv(RAW_LONDRINA_COMP_DIR / "openmeteo_era5_londrina_diario_2022_2025.csv")

    df_83766["data"] = pd.to_datetime(df_83766["data"])
    df_83768["data"] = pd.to_datetime(df_83768["data"])
    df_om["data"] = pd.to_datetime(df_om["time"])

    df_83766 = df_83766[["data", "tavg_c", "tmin_c", "tmax_c", "precip_mm", "vento_vel_kmh", "pressao_hpa"]].rename(
        columns={
            "tavg_c": "inmet_83766_temp_media_c",
            "tmin_c": "inmet_83766_temp_min_c",
            "tmax_c": "inmet_83766_temp_max_c",
            "precip_mm": "inmet_83766_precip_mm",
            "vento_vel_kmh": "inmet_83766_vento_kmh",
            "pressao_hpa": "inmet_83766_pressao_hpa",
        }
    )

    df_83768 = df_83768[["data", "tavg_c", "tmin_c", "tmax_c", "precip_mm"]].rename(
        columns={
            "tavg_c": "sblo_83768_temp_media_c",
            "tmin_c": "sblo_83768_temp_min_c",
            "tmax_c": "sblo_83768_temp_max_c",
            "precip_mm": "sblo_83768_precip_mm",
        }
    )

    df_om = df_om[
        [
            "data",
            "temperature_2m_mean",
            "temperature_2m_min",
            "temperature_2m_max",
            "precipitation_sum",
            "precipitation_hours",
            "wind_speed_10m_max",
        ]
    ].rename(
        columns={
            "temperature_2m_mean": "era5_londrina_temp_media_c",
            "temperature_2m_min": "era5_londrina_temp_min_c",
            "temperature_2m_max": "era5_londrina_temp_max_c",
            "precipitation_sum": "era5_londrina_precip_mm",
            "precipitation_hours": "era5_londrina_horas_chuva",
            "wind_speed_10m_max": "era5_londrina_vento_max_kmh",
        }
    )

    merged = df_83766.merge(df_83768, on="data", how="outer").merge(df_om, on="data", how="outer")

    # Série meteorológica oficial consolidada de Londrina:
    # Prioridade 1: Estação INMET Convencional 83766 (Londrina)
    # Prioridade 2 (para os dias sem registro pluviométrico no GTS em 2022): Estação SBLO 83768 / Open-Meteo Londrina
    merged["temp_media_c"] = merged["inmet_83766_temp_media_c"].combine_first(merged["era5_londrina_temp_media_c"])
    merged["temp_min_c"] = merged["inmet_83766_temp_min_c"].combine_first(merged["era5_londrina_temp_min_c"])
    merged["temp_max_c"] = merged["inmet_83766_temp_max_c"].combine_first(merged["era5_londrina_temp_max_c"])
    merged["amplitude_termica_c"] = (merged["temp_max_c"] - merged["temp_min_c"]).round(2)

    merged["precip_londrina_mm"] = (
        merged["inmet_83766_precip_mm"]
        .combine_first(merged["sblo_83768_precip_mm"])
        .combine_first(merged["era5_londrina_precip_mm"])
    )
    merged["fonte_precip_londrina"] = np.where(
        merged["inmet_83766_precip_mm"].notna(),
        "INMET_83766_LONDRINA",
        np.where(
            merged["sblo_83768_precip_mm"].notna(),
            "SBLO_83768_LONDRINA",
            "OPENMETEO_ERA5_LONDRINA",
        ),
    )

    return merged


def build_consolidated_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executa o pipeline completo e retorna:
    - prf_londrina: DataFrame de ocorrências individuais em Londrina (2022-2025)
    - daily_full: DataFrame diário consolidado (1 linha = 1 dia civil em Londrina, 2022-2025)
    """
    prf_londrina = load_prf_londrina(years=(2022, 2023, 2024, 2025))
    prf_daily = aggregate_prf_daily(prf_londrina, start_date="2022-01-01", end_date="2025-12-31")

    inmet_a835 = load_inmet_automatic_station("A835", years=(2022, 2023, 2024, 2025))
    londrina_meteo = load_londrina_meteorological_series()

    daily = (
        prf_daily.merge(londrina_meteo, on="data", how="left")
        .merge(inmet_a835, on="data", how="left")
    )

    # Atributos de calendário
    daily["ano"] = daily["data"].dt.year
    daily["mes"] = daily["data"].dt.month
    daily["dia_semana_num"] = daily["data"].dt.day_of_week  # 0=Seg, 6=Dom
    daily["dia_semana"] = daily["dia_semana_num"].map(DIAS_SEMANA_PT)
    daily["fim_de_semana"] = daily["dia_semana_num"].isin([5, 6]).astype(int)

    # Indicadores do Project Canvas (Lab 01):
    # 1. Dia chuvoso (>= 1.0 mm) vs Dia seco (< 1.0 mm) - Londrina e A835
    daily["dia_chuvoso_londrina"] = (daily["precip_londrina_mm"] >= 1.0).astype(int)
    daily["cenario_chuva_londrina"] = np.where(daily["dia_chuvoso_londrina"] == 1, "Chuvoso (>= 1 mm)", "Seco (< 1 mm)")

    daily["dia_chuvoso_a835"] = np.where(
        daily["a835_precip_mm"].isna(),
        np.nan,
        (daily["a835_precip_mm"] >= 1.0).astype(float),
    )

    # Categorização de intensidade de chuva (Londrina)
    daily["faixa_precipitacao"] = pd.cut(
        daily["precip_londrina_mm"],
        bins=[-0.01, 0.99, 10.0, 30.0, 500.0],
        labels=["Seco (<1 mm)", "Chuva Leve (1-10 mm)", "Chuva Moderada (10-30 mm)", "Chuva Forte (>30 mm)"],
    )

    # 2. Faixas de temperatura média diária (Frio, Ameno, Quente/Calor Extremo)
    # Baseado nos quantis / limiares climatológicos de Londrina (< 19°C, 19-24°C, > 24°C)
    daily["faixa_temperatura_media"] = pd.cut(
        daily["temp_media_c"],
        bins=[-50.0, 19.0, 24.0, 60.0],
        labels=["Frio (<= 19°C)", "Ameno (19-24°C)", "Quente (> 24°C)"],
    )
    daily["faixa_temperatura_maxima"] = pd.cut(
        daily["temp_max_c"],
        bins=[-50.0, 25.0, 30.0, 60.0],
        labels=["Amena (<= 25°C)", "Quente (25-30°C)", "Calor Extremo (> 30°C)"],
    )

    # 3. Indicadores relativos de severidade e letalidade no dia (NaN quando total_acidentes == 0)
    daily["taxa_severidade_vitimas_pct"] = np.where(
        daily["total_acidentes"] > 0,
        (daily["acidentes_com_vitimas"] / daily["total_acidentes"] * 100.0).round(2),
        np.nan,
    )
    daily["taxa_severidade_graves_fatais_pct"] = np.where(
        daily["total_acidentes"] > 0,
        (daily["acidentes_graves_ou_fatais"] / daily["total_acidentes"] * 100.0).round(2),
        np.nan,
    )
    daily["taxa_letalidade_pct"] = np.where(
        daily["total_acidentes"] > 0,
        (daily["acidentes_fatais"] / daily["total_acidentes"] * 100.0).round(2),
        np.nan,
    )

    # Enriquecer ocorrências individuais com os dados meteorológicos do dia correspondente
    prf_enriched = prf_londrina.merge(daily[METEO_COLS_FOR_JOIN], on="data", how="left")

    return prf_enriched, daily


def load_prf_pessoas_londrina(
    daily_df: pd.DataFrame,
    years=(2022, 2023, 2024, 2025),
) -> pd.DataFrame:
    """
    Carrega os microdados por pessoa/veículo da PRF (acidentesYYYY_pessoa_londrina.csv),
    padroniza modais, gênero, horários e cruza com a série meteorológica diária.
    """
    frames = []
    for yr in years:
        fpath = RAW_PRF_DIR / f"acidentes{yr}_pessoa_londrina.csv"
        df = pd.read_csv(fpath, sep=";", encoding="latin-1", low_memory=False)
        mask = df["municipio"].astype(str).str.strip().str.upper() == "LONDRINA"
        df_lond = df.loc[mask].copy()
        df_lond["ano_arquivo"] = yr
        frames.append(df_lond)

    pes = pd.concat(frames, ignore_index=True)
    pes["data"] = pd.to_datetime(pes["data_inversa"].astype(str).str.strip(), format="%Y-%m-%d")
    pes = _clean_decimal_columns(pes, ["km", "latitude", "longitude"])

    for col in ["ilesos", "feridos_leves", "feridos_graves", "mortos"]:
        pes[col] = pd.to_numeric(pes[col], errors="coerce").fillna(0).astype(int)
    pes["idade_num"] = pd.to_numeric(pes["idade"], errors="coerce")
    pes["hora"] = pd.to_numeric(pes["horario"].astype(str).str.slice(0, 2), errors="coerce").fillna(0).astype(int)

    for col in ["condicao_metereologica", "tipo_veiculo", "tipo_envolvido", "estado_fisico", "sexo", "tipo_acidente", "causa_acidente", "fase_dia"]:
        pes[col] = pes[col].astype(str).str.strip()

    pes["dia_semana"] = pes["data"].dt.day_of_week.map(DIAS_SEMANA_PT)
    pes["fim_de_semana"] = pes["data"].dt.day_of_week.isin([5, 6]).astype(int)
    pes["tipo_envolvido_clean"] = pes["tipo_envolvido"]
    pes["modal"] = [map_modal_categoria(v, e) for v, e in zip(pes["tipo_veiculo"], pes["tipo_envolvido"])]
    pes["genero"] = pes["sexo"].map(clean_sexo_label)

    pes["condicao_chuva_prf"] = pes["condicao_metereologica"].isin(["Chuva", "Garoa/Chuvisco"]).astype(int)
    pes["tem_vitima"] = ((pes["feridos_leves"] > 0) | (pes["feridos_graves"] > 0) | (pes["mortos"] > 0)).astype(int)
    pes["tem_grave_ou_morte"] = ((pes["feridos_graves"] > 0) | (pes["mortos"] > 0)).astype(int)
    pes["tem_obito"] = (pes["mortos"] > 0).astype(int)

    pes = pes.merge(daily_df[METEO_COLS_FOR_JOIN + ["cenario_chuva_londrina"]], on="data", how="left")
    pes = pes.sort_values(["data", "horario", "id", "pesid"]).reset_index(drop=True)
    return pes


def save_outputs():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ATIVIDADE2_DIR.mkdir(parents=True, exist_ok=True)

    prf_enriched, daily = build_consolidated_dataset()
    pes_enriched = load_prf_pessoas_londrina(daily_df=daily, years=(2022, 2023, 2024, 2025))
    _, hourly_a835 = compute_inmet_hourly_rain_stats(station_code="A835", years=(2022, 2023, 2024))

    # 1. Salvar em data/processed/
    prf_enriched.to_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2025_enriquecido.csv", index=False, encoding="utf-8")
    prf_22_24 = prf_enriched[prf_enriched["ano_arquivo"].isin([2022, 2023, 2024])].copy()
    prf_22_24.to_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2024_enriquecido.csv", index=False, encoding="utf-8")

    pes_enriched.to_csv(PROCESSED_DIR / "prf_pessoas_veiculos_londrina_2022_2025_enriquecido.csv", index=False, encoding="utf-8")
    pes_22_24 = pes_enriched[pes_enriched["ano_arquivo"].isin([2022, 2023, 2024])].copy()
    pes_22_24.to_csv(PROCESSED_DIR / "prf_pessoas_veiculos_londrina_2022_2024_enriquecido.csv", index=False, encoding="utf-8")

    daily.to_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2025.csv", index=False, encoding="utf-8")
    daily_22_24 = daily[daily["ano"].isin([2022, 2023, 2024])].copy()
    daily_22_24.to_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2024.csv", index=False, encoding="utf-8")

    hourly_a835.to_csv(PROCESSED_DIR / "inmet_a835_resumo_horario_2022_2024.csv", index=False, encoding="utf-8")

    # 2. Salvar exemplares na pasta Atividade 2/ para entrega imediata ao professor
    # 2a. Base consolidada diária (recorte 2022-2024 do Project Canvas e recorte completo 2022-2025)
    daily_22_24.to_csv(ATIVIDADE2_DIR / "base_consolidada_londrina_diaria_2022_2024.csv", index=False, encoding="utf-8")
    daily.to_csv(ATIVIDADE2_DIR / "base_consolidada_londrina_diaria_2022_2025.csv", index=False, encoding="utf-8")

    # 2b. Exemplar da fonte PRF filtrada para Londrina (2022-2024 e 2022-2025)
    prf_22_24.to_csv(ATIVIDADE2_DIR / "prf_ocorrencias_londrina_2022_2024.csv", index=False, encoding="utf-8")

    # 2c. Exemplar da fonte INMET diária em Londrina + Estação Automática A835 (2022-2024)
    inmet_cols = [
        "data",
        "ano",
        "mes",
        "inmet_83766_temp_media_c",
        "inmet_83766_temp_min_c",
        "inmet_83766_temp_max_c",
        "inmet_83766_precip_mm",
        "inmet_83766_vento_kmh",
        "inmet_83766_pressao_hpa",
        "sblo_83768_precip_mm",
        "era5_londrina_precip_mm",
        "temp_media_c",
        "temp_min_c",
        "temp_max_c",
        "amplitude_termica_c",
        "precip_londrina_mm",
        "fonte_precip_londrina",
        "a835_temp_media_c",
        "a835_temp_min_c",
        "a835_temp_max_c",
        "a835_precip_mm",
        "a835_umid_media_pct",
    ]
    daily_22_24[inmet_cols].to_csv(
        ATIVIDADE2_DIR / "inmet_clima_diario_londrina_e_a835_2022_2024.csv",
        index=False,
        encoding="utf-8",
    )

    # 2d. Exemplares no formato bruto original de cada órgão (Atividade 2 / exemplares_brutos)
    brutos_dir = ATIVIDADE2_DIR / "exemplares_brutos"
    brutos_dir.mkdir(parents=True, exist_ok=True)

    # Extrair linhas brutas de Londrina preservando cabeçalho, separador ';' e codificação latin-1 da PRF
    raw_2024_path = RAW_PRF_DIR / "datatran2024.csv"
    with open(raw_2024_path, "r", encoding="latin-1") as fin:
        header_line = fin.readline()
        lond_2024_lines = [line for line in fin if ";LONDRINA;" in line.upper() or ";\"LONDRINA\";" in line.upper()]
    with open(brutos_dir / "prf_datatran2024_londrina_bruto.csv", "w", encoding="latin-1") as fout:
        fout.write(header_line)
        fout.writelines(lond_2024_lines)

    # Amostra bruta original da Estação Automática INMET A835 (primeiras 250 linhas com cabeçalho de 8 linhas de metadados)
    inmet_2024_src = RAW_INMET_DIR / "INMET_S_PR_A835_MARINGA_01-01-2024_A_31-12-2024.CSV"
    with open(inmet_2024_src, "r", encoding="latin-1") as fin:
        inmet_sample_lines = [fin.readline() for _ in range(250)]
    with open(brutos_dir / "inmet_A835_2024_amostra_horaria_bruta.csv", "w", encoding="latin-1") as fout:
        fout.writelines(inmet_sample_lines)

    # Cópia da série diária bruta da Estação Convencional INMET 83766 (Londrina)
    import shutil
    shutil.copyfile(
        RAW_LONDRINA_COMP_DIR / "inmet_convencional_83766_londrina_diario_2022_2025.csv",
        brutos_dir / "inmet_83766_londrina_convencional_diario_bruto.csv",
    )

    print("Arquivos gerados com sucesso!")
    print(f"  - Ocorrências PRF Londrina (2022-2024):         {len(prf_22_24)} linhas")
    print(f"  - Ocorrências PRF Londrina (2022-2025):         {len(prf_enriched)} linhas")
    print(f"  - Pessoas/Veículos PRF Londrina (2022-2024):    {len(pes_22_24)} registros")
    print(f"  - Pessoas/Veículos PRF Londrina (2022-2025):    {len(pes_enriched)} registros")
    print(f"  - Base Diária Consolidada (2022-2024):          {len(daily_22_24)} dias")
    print(f"  - Base Diária Consolidada (2022-2025):          {len(daily)} dias")
    print(
        f"  - Série Horária INMET A835 (2022-2024):         "
        f"{int(hourly_a835['horas_com_chuva'].sum())}/{int(hourly_a835['horas_validas'].sum())} h com chuva "
        f"({hourly_a835['horas_com_chuva'].sum()/hourly_a835['horas_validas'].sum()*100:.2f}%)"
    )


if __name__ == "__main__":
    save_outputs()
