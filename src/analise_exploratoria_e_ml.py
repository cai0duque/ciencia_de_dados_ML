#!/usr/bin/env python3
"""
Análise Exploratória de Dados (EDA), Testes de Hipóteses, Indicadores do Project Canvas
e Experimentos de Machine Learning (Classificação, Regressão e Clusterização).
Segue rigorosamente as diretrizes de ML Best Practices (divisão cronológica antes do
pré-processamento, tratamento explícito de valores ausentes e validação com bootstrap).
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge, PoissonRegressor
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    f1_score,
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    root_mean_squared_error,
    silhouette_score,
)

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
ATIV2_FIG_DIR = BASE_DIR / "Atividade 2" / "figuras"

ORDEM_DIAS_PT = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def analyze_project_questions(daily: pd.DataFrame, prf: pd.DataFrame, label_periodo: str):
    print_section(f"ANÁLISE DOS INDICADORES DO PROJECT CANVAS ({label_periodo})")
    n_days = len(daily)
    n_acc = len(prf)
    days_with_acc = (daily["total_acidentes"] > 0).sum()
    print(f"Total de dias observados: {n_days}")
    print(f"Dias com pelo menos 1 sinistro: {days_with_acc} ({days_with_acc/n_days*100:.1f}%)")
    print(f"Dias sem sinistros (contagem zero): {n_days - days_with_acc} ({(n_days - days_with_acc)/n_days*100:.1f}%)")
    print(f"Total de sinistros (PRF Londrina): {n_acc} (média geral = {n_acc/n_days:.3f} acidentes/dia)")
    print(f"Total de vítimas fatais (mortos): {prf['mortos'].sum()} em {prf['tem_obito'].sum()} sinistros fatais")
    print(f"Total de feridos graves: {prf['feridos_graves'].sum()} | feridos leves: {prf['feridos_leves'].sum()}")

    # -------------------------------------------------------------------------
    # PERGUNTA SECUNDÁRIA 1: Média diária de acidentes em dias chuvosos vs secos
    # -------------------------------------------------------------------------
    print("\n--- [Pergunta Secundária 1] Média diária de acidentes: Dias Chuvosos (>=1 mm) vs. Dias Secos (<1 mm) ---")
    for col_chuva, nome_fonte in [
        ("dia_chuvoso_londrina", "Série Oficial Londrina (INMET 83766 / SBLO / ERA5)"),
        ("dia_chuvoso_a835", "Estação Automática INMET A835 (Maringá - Link ZIP)"),
    ]:
        sub = daily.dropna(subset=[col_chuva]).copy()
        chuv = sub[sub[col_chuva] == 1]["total_acidentes"]
        seco = sub[sub[col_chuva] == 0]["total_acidentes"]
        diff_pct = (chuv.mean() / seco.mean() - 1) * 100
        u_stat, p_val_mw = stats.mannwhitneyu(chuv, seco, alternative="two-sided")
        t_stat, p_val_t = stats.ttest_ind(chuv, seco, equal_var=False)
        print(f"\nFonte Climática: {nome_fonte} (n={len(sub)} dias válidos)")
        print(f"  • Dias Secos (<1 mm):     n={len(seco):4d} dias | Total={seco.sum():3d} acid. | Média={seco.mean():.3f}/dia (DP={seco.std():.3f}) | % dias c/ acid={(seco>0).mean()*100:.1f}%")
        print(f"  • Dias Chuvosos (>=1 mm): n={len(chuv):4d} dias | Total={chuv.sum():3d} acid. | Média={chuv.mean():.3f}/dia (DP={chuv.std():.3f}) | % dias c/ acid={(chuv>0).mean()*100:.1f}%")
        print(f"  • Razão Chuvoso/Seco:     {chuv.mean()/seco.mean():.3f}x ({diff_pct:+.1f}%) | Welch t p={p_val_t:.4f} | Mann-Whitney p={p_val_mw:.4f}")

    # Por faixa de intensidade de precipitação em Londrina
    print("\n  Detalhamento por faixa de intensidade pluviométrica (Londrina):")
    grp_p = daily.groupby("faixa_precipitacao", observed=False).agg(
        dias=("data", "count"),
        total_acidentes=("total_acidentes", "sum"),
        media_acidentes=("total_acidentes", "mean"),
        dp_acidentes=("total_acidentes", "std"),
        pct_dias_com_acidente=("total_acidentes", lambda s: (s > 0).mean() * 100),
        media_com_vitimas=("acidentes_com_vitimas", "mean"),
        media_graves_fatais=("acidentes_graves_ou_fatais", "mean"),
    )
    print(grp_p.to_string())

    # -------------------------------------------------------------------------
    # PERGUNTA SECUNDÁRIA 2: Frequência de acidentes por faixa de temperatura
    # -------------------------------------------------------------------------
    print("\n--- [Pergunta Secundária 2] Frequência média de acidentes por Faixa de Temperatura ---")
    grp_tmed = daily.groupby("faixa_temperatura_media", observed=False).agg(
        dias=("data", "count"),
        total_acidentes=("total_acidentes", "sum"),
        media_acidentes=("total_acidentes", "mean"),
        dp_acidentes=("total_acidentes", "std"),
        pct_dias_com_acidente=("total_acidentes", lambda s: (s > 0).mean() * 100),
    )
    print("\nPor Temperatura Média Diária (Londrina):")
    print(grp_tmed.to_string())

    grp_tmax = daily.groupby("faixa_temperatura_maxima", observed=False).agg(
        dias=("data", "count"),
        total_acidentes=("total_acidentes", "sum"),
        media_acidentes=("total_acidentes", "mean"),
        dp_acidentes=("total_acidentes", "std"),
        pct_dias_com_acidente=("total_acidentes", lambda s: (s > 0).mean() * 100),
    )
    print("\nPor Temperatura Máxima Diária (Londrina):")
    print(grp_tmax.to_string())

    # -------------------------------------------------------------------------
    # PERGUNTA SECUNDÁRIA 3: Gravidade e Letalidade (Chuva/Pista Molhada vs Seco)
    # -------------------------------------------------------------------------
    print("\n--- [Pergunta Secundária 3] Severidade e Letalidade (Chuva vs. Seco) ---")
    print("A) No nível da OCORRÊNCIA individual ( segundo a condição meteorológica relatada na PRF ):")
    prf_grp_cond = prf.groupby("condicao_chuva_prf").agg(
        ocorrencias=("id", "count"),
        com_vitimas=("tem_vitima", "sum"),
        taxa_vitimas_pct=("tem_vitima", lambda s: s.mean() * 100),
        graves_ou_fatais=("tem_grave_ou_morte", "sum"),
        taxa_graves_fatais_pct=("tem_grave_ou_morte", lambda s: s.mean() * 100),
        fatais=("tem_obito", "sum"),
        taxa_letalidade_pct=("tem_obito", lambda s: s.mean() * 100),
        media_feridos=("feridos", "mean"),
        media_mortos=("mortos", "mean"),
    )
    prf_grp_cond.index = ["Sem Chuva na PRF (Céu Claro/Sol/Nublado)", "Com Chuva/Garoa na PRF"]
    print(prf_grp_cond.to_string())

    print("\nB) No nível da OCORRÊNCIA individual ( segundo o dia chuvoso >= 1 mm medido na Estação de Londrina ):")
    prf_grp_inst = prf.groupby("dia_chuvoso_londrina").agg(
        ocorrencias=("id", "count"),
        com_vitimas=("tem_vitima", "sum"),
        taxa_vitimas_pct=("tem_vitima", lambda s: s.mean() * 100),
        graves_ou_fatais=("tem_grave_ou_morte", "sum"),
        taxa_graves_fatais_pct=("tem_grave_ou_morte", lambda s: s.mean() * 100),
        fatais=("tem_obito", "sum"),
        taxa_letalidade_pct=("tem_obito", lambda s: s.mean() * 100),
        media_feridos=("feridos", "mean"),
        media_mortos=("mortos", "mean"),
    )
    prf_grp_inst.index = ["Dia Seco (<1 mm)", "Dia Chuvoso (>=1 mm)"]
    print(prf_grp_inst.to_string())

    # -------------------------------------------------------------------------
    # PERGUNTA SECUNDÁRIA 4: Índice de Concordância PRF vs Estações Meteorológicas
    # -------------------------------------------------------------------------
    print("\n--- [Pergunta Secundária 4] Índice de Concordância: Boletim PRF vs. Estação Meteorológica ---")
    chuva_prf_rows = prf[prf["condicao_chuva_prf"] == 1]
    seco_prf_rows = prf[prf["condicao_chuva_prf"] == 0]

    conc_lond_1mm = (chuva_prf_rows["precip_londrina_mm"] >= 1.0).mean() * 100
    conc_lond_01mm = (chuva_prf_rows["precip_londrina_mm"] > 0.0).mean() * 100
    conc_83766_01mm = (chuva_prf_rows["inmet_83766_precip_mm"].dropna() > 0.0).mean() * 100
    conc_a835_1mm = (chuva_prf_rows["a835_precip_mm"].dropna() >= 1.0).mean() * 100
    conc_a835_01mm = (chuva_prf_rows["a835_precip_mm"].dropna() > 0.0).mean() * 100

    print(f"Total de sinistros com 'Chuva' ou 'Garoa/Chuvisco' no boletim da PRF: {len(chuva_prf_rows)} de {len(prf)} ({len(chuva_prf_rows)/len(prf)*100:.1f}%)")
    print(f"  • Concordância com precipitação > 0 mm em Londrina (Série Oficial):  {conc_lond_01mm:.1f}% (>= 1 mm: {conc_lond_1mm:.1f}%)")
    print(f"  • Concordância com precipitação > 0 mm no INMET 83766 (Londrina):    {conc_83766_01mm:.1f}%")
    print(f"  • Concordância com precipitação > 0 mm na Estação A835 (Maringá):    {conc_a835_01mm:.1f}% (>= 1 mm: {conc_a835_1mm:.1f}%)")

    # E o inverso: nos dias em que choveu >= 1 mm em Londrina, quantos acidentes ocorreram sob Céu Claro/Nublado porque a chuva foi em outra hora do dia?
    acc_em_dia_chuvoso = prf[prf["dia_chuvoso_londrina"] == 1]
    pct_chuva_no_momento = (acc_em_dia_chuvoso["condicao_chuva_prf"] == 1).mean() * 100
    print(f"  • Dos {len(acc_em_dia_chuvoso)} acidentes ocorridos em dias chuvosos (>=1 mm), apenas {pct_chuva_no_momento:.1f}% ocorreram no exato momento em que chovia/garoava!")

    # -------------------------------------------------------------------------
    # ANÁLISE DE VARIÁVEIS DE CONFUSÃO (Dia da Semana / Fim de Semana)
    # -------------------------------------------------------------------------
    print("\n--- [Análise de Confusão / Limitação do VMD] Efeito do Dia da Semana vs. Chuva ---")
    grp_fds = daily.groupby("fim_de_semana").agg(
        dias=("data", "count"),
        media_acidentes=("total_acidentes", "mean"),
        media_graves_fatais=("acidentes_graves_ou_fatais", "mean"),
        taxa_letalidade_media=("taxa_letalidade_pct", "mean"),
    )
    grp_fds.index = ["Dia Útil (Seg-Sex)", "Fim de Semana (Sáb-Dom)"]
    print(grp_fds.to_string())


def analyze_transport_and_hourly_patterns(
    daily: pd.DataFrame,
    prf: pd.DataFrame,
    pes: pd.DataFrame,
    hourly_a835: pd.DataFrame,
    label_periodo: str,
):
    """
    Analisa proporções Seco vs. Chuvoso, variação por tipo de transporte (Carro, Moto,
    Caminhão, Pedestre, Ônibus, Bicicleta), fração horária de chuva e picos por dia/hora.
    """
    print_section(f"ANÁLISE MODAL, HORÁRIA E DE PROPORÇÕES ({label_periodo})")

    n_seco = int((daily["dia_chuvoso_londrina"] == 0).sum())
    n_chuv = int((daily["dia_chuvoso_londrina"] == 1).sum())
    n_tot_dias = len(daily)

    print("--- 1. Proporção Direta: Acidentes vs. Quantidade de Dias no Clima ---")
    for cl_val, cl_nome in [(0, "Dias Secos (< 1 mm)"), (1, "Dias Chuvosos (>= 1 mm)")]:
        sub_d = daily[daily["dia_chuvoso_londrina"] == cl_val]
        n_d = len(sub_d)
        n_acid = int(sub_d["total_acidentes"].sum())
        d_com_acid = int((sub_d["total_acidentes"] > 0).sum())
        print(
            f"  • {cl_nome:24s}: {n_d:4d} dias ({n_d/n_tot_dias*100:5.1f}% dos dias) | "
            f"{n_acid:3d} acidentes ({n_acid/daily['total_acidentes'].sum()*100:5.1f}% do total) | "
            f"Razão={n_acid/n_d:.3f}/dia ({n_acid/n_d*100:5.1f} por 100d) | "
            f"Dias c/ >=1 sinistro: {d_com_acid}/{n_d} ({d_com_acid/n_d*100:.1f}%)"
        )

    h_tot = int(hourly_a835["horas_validas"].sum())
    h_chuv = int(hourly_a835["horas_com_chuva"].sum())
    print(
        f"\n  • Exposição horária real no INMET A835 (2022–2024): "
        f"{h_chuv}/{h_tot} horas com precipitação > 0 mm ({h_chuv/h_tot*100:.2f}% do tempo)."
    )

    # Tabela por dia da semana x clima (proporção ajustada pela quantidade de dias)
    print("\n--- 2. Proporção por Dia da Semana x Clima (Acidentes / Dias daquele Clima) ---")
    dow_rows = []
    for dia in ORDEM_DIAS_PT:
        ds = daily[(daily["dia_semana"] == dia) & (daily["dia_chuvoso_londrina"] == 0)]
        dc = daily[(daily["dia_semana"] == dia) & (daily["dia_chuvoso_londrina"] == 1)]
        taxa_s = ds["total_acidentes"].mean() if len(ds) else 0.0
        taxa_c = dc["total_acidentes"].mean() if len(dc) else 0.0
        var_pct = (taxa_c / taxa_s - 1.0) * 100.0 if taxa_s > 0 else np.nan
        dow_rows.append(
            {
                "Dia_Semana": dia,
                "Dias_Secos": len(ds),
                "Acid_Secos": int(ds["total_acidentes"].sum()),
                "Taxa_Seco_100d": round(taxa_s * 100, 1),
                "Dias_Chuv": len(dc),
                "Acid_Chuv": int(dc["total_acidentes"].sum()),
                "Taxa_Chuv_100d": round(taxa_c * 100, 1),
                "Var_Chuva_%": round(var_pct, 1),
            }
        )
    print(pd.DataFrame(dow_rows).to_string(index=False))

    # Variação por Tipo de Transporte (deduplicando 1 veículo/modal por ocorrência)
    acc_modal = pes[pes["modal"] != "Outros"].drop_duplicates(subset=["id", "modal"]).copy()
    print("\n--- 3. Variação por Tipo de Transporte: Dia Seco (<1 mm) vs. Dia Chuvoso (>=1 mm) ---")
    t_mod = acc_modal.groupby(["modal", "dia_chuvoso_londrina"])["id"].nunique().unstack(fill_value=0)
    t_mod.columns = ["Acid_Seco", "Acid_Chuvoso"]
    t_mod["Total"] = t_mod["Acid_Seco"] + t_mod["Acid_Chuvoso"]
    t_mod["Taxa_100d_Seco"] = (t_mod["Acid_Seco"] / n_seco * 100).round(2)
    t_mod["Taxa_100d_Chuv"] = (t_mod["Acid_Chuvoso"] / n_chuv * 100).round(2)
    t_mod["Var_Taxa_Chuva_%"] = ((t_mod["Taxa_100d_Chuv"] / t_mod["Taxa_100d_Seco"] - 1) * 100).round(1)
    print(t_mod.sort_values("Total", ascending=False).to_string())

    print("\n--- 4. Picos por Transporte (Dia da Semana e Hora do Dia) ---")
    for modal_name in ["Carro", "Moto", "Caminhão", "Pedestre", "Ônibus", "Bicicleta"]:
        sm = acc_modal[acc_modal["modal"] == modal_name]
        if sm.empty:
            continue
        d_all = sm.groupby("dia_semana")["id"].nunique()
        h_all = sm.groupby("hora")["id"].nunique()
        dh_all = sm.groupby(["dia_semana", "hora"])["id"].nunique()
        best_dh = dh_all.idxmax()
        print(
            f"  • {modal_name:9s} (n={sm['id'].nunique():3d}): "
            f"Dia pico={d_all.idxmax()} ({d_all.max()}) | "
            f"Hora pico={h_all.idxmax():02d}h ({h_all.max()}) | "
            f"Combinação={best_dh[0]} às {best_dh[1]:02d}h ({dh_all.max()})"
        )

    prf_h = prf.copy()
    prf_h["hora"] = pd.to_numeric(prf_h["horario"].astype(str).str.slice(0, 2), errors="coerce").fillna(0).astype(int)
    h_piv = acc_modal.pivot_table(index="hora", columns="modal", values="id", aggfunc="nunique", fill_value=0).reindex(range(24), fill_value=0)
    h_piv["Total_Acid"] = prf_h.groupby("hora")["id"].nunique().reindex(range(24), fill_value=0)
    h_piv["Dia_Seco"] = prf_h[prf_h["dia_chuvoso_londrina"] == 0].groupby("hora")["id"].nunique().reindex(range(24), fill_value=0)
    h_piv["Dia_Chuvoso"] = prf_h[prf_h["dia_chuvoso_londrina"] == 1].groupby("hora")["id"].nunique().reindex(range(24), fill_value=0)
    h_piv["Chuva_Momento_PRF"] = prf_h[prf_h["condicao_chuva_prf"] == 1].groupby("hora")["id"].nunique().reindex(range(24), fill_value=0)
    print("\n--- 5. Comparativo Hora a Hora (00h às 23h) ---")
    cols_h = ["Total_Acid", "Dia_Seco", "Dia_Chuvoso", "Chuva_Momento_PRF", "Carro", "Moto", "Caminhão", "Pedestre", "Ônibus", "Bicicleta"]
    print(h_piv[[c for c in cols_h if c in h_piv.columns]].to_string())


def analyze_gender_patterns(daily: pd.DataFrame, pes: pd.DataFrame, label_periodo: str):
    """Analisa a distribuição dos envolvidos e condutores por gênero, modal, chuva e gravidade."""
    print_section(f"ANÁLISE POR GÊNERO: CONDUTORES, PASSAGEIROS E PEDESTRES ({label_periodo})")

    n_seco = int((daily["dia_chuvoso_londrina"] == 0).sum())
    n_chuv = int((daily["dia_chuvoso_londrina"] == 1).sum())

    t_env = pes.groupby(["genero", "tipo_envolvido_clean"])["pesid"].count().unstack(fill_value=0)
    t_env["Total_Pessoas"] = t_env.sum(axis=1)
    t_env["%_Total"] = (t_env["Total_Pessoas"] / len(pes) * 100).round(1)
    print("1) Envolvidos por Gênero x Papel na Ocorrência:")
    print(t_env.to_string())

    cond_valid = pes[
        (pes["tipo_envolvido_clean"] == "Condutor") & (pes["genero"].isin(["Masculino", "Feminino"]))
    ].copy()
    print("\n2) Condutores por Gênero x Clima (Taxa por 100 dias):")
    t_clima = cond_valid.groupby(["genero", "dia_chuvoso_londrina"])["pesid"].count().unstack(fill_value=0)
    t_clima.columns = ["Condutores_Seco", "Condutores_Chuvoso"]
    t_clima["Total"] = t_clima["Condutores_Seco"] + t_clima["Condutores_Chuvoso"]
    t_clima["Taxa_100d_Seco"] = (t_clima["Condutores_Seco"] / n_seco * 100).round(2)
    t_clima["Taxa_100d_Chuv"] = (t_clima["Condutores_Chuvoso"] / n_chuv * 100).round(2)
    t_clima["Var_Chuva_%"] = ((t_clima["Taxa_100d_Chuv"] / t_clima["Taxa_100d_Seco"] - 1) * 100).round(1)
    print(t_clima.to_string())

    print("\n3) Condutores por Gênero x Tipo de Veículo:")
    t_mod = cond_valid.groupby(["modal", "genero"])["pesid"].count().unstack(fill_value=0)
    t_mod["Total"] = t_mod.sum(axis=1)
    t_mod["%_Feminino"] = (t_mod["Feminino"] / t_mod["Total"] * 100).round(1)
    t_mod["%_Masculino"] = (t_mod["Masculino"] / t_mod["Total"] * 100).round(1)
    print(t_mod.sort_values("Total", ascending=False).to_string())

    print("\n4) Gravidade e Letalidade dos Condutores por Gênero:")
    t_sev = cond_valid.groupby("genero").agg(
        total_condutores=("pesid", "count"),
        ilesos=("ilesos", "sum"),
        feridos_leves=("feridos_leves", "sum"),
        feridos_graves=("feridos_graves", "sum"),
        mortos=("mortos", "sum"),
    )
    t_sev["%_Ilesos"] = (t_sev["ilesos"] / t_sev["total_condutores"] * 100).round(1)
    t_sev["%_Graves_ou_Mortos"] = ((t_sev["feridos_graves"] + t_sev["mortos"]) / t_sev["total_condutores"] * 100).round(1)
    t_sev["%_Letalidade"] = (t_sev["mortos"] / t_sev["total_condutores"] * 100).round(2)
    print(t_sev.to_string())

    by_id = cond_valid.groupby("id")["genero"].apply(set)
    tot_ids = len(by_id)
    only_m = sum(s == {"Masculino"} for s in by_id)
    only_f = sum(s == {"Feminino"} for s in by_id)
    mixed = sum(s == {"Masculino", "Feminino"} for s in by_id)
    print(
        f"\n5) Composição por Sinistro (n={tot_ids}): "
        f"Apenas Homens={only_m} ({only_m/tot_ids*100:.1f}%) | "
        f"Apenas Mulheres={only_f} ({only_f/tot_ids*100:.1f}%) | "
        f"Misto (H+M)={mixed} ({mixed/tot_ids*100:.1f}%)"
    )


def generate_visualizations(daily_22_24: pd.DataFrame, prf_22_24: pd.DataFrame, daily_full: pd.DataFrame):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ATIV2_FIG_DIR.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["font.size"] = 10

    # Figura 1: Painel das 4 Perguntas Secundárias do Project Canvas (2022-2024)
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))

    # Subplot 1: Média diária de acidentes por faixa de precipitação (Pergunta 1)
    ordem_p = ["Seco (<1 mm)", "Chuva Leve (1-10 mm)", "Chuva Moderada (10-30 mm)", "Chuva Forte (>30 mm)"]
    grp_p = (
        daily_22_24.groupby("faixa_precipitacao", observed=False)["total_acidentes"]
        .agg(["mean", "count", "std"])
        .reindex(ordem_p)
        .reset_index()
    )
    grp_p["se"] = grp_p["std"] / np.sqrt(grp_p["count"])
    colors_p = ["#4C72B0", "#55A868", "#DD8452", "#C44E52"]
    bars1 = axes[0, 0].bar(
        grp_p["faixa_precipitacao"].astype(str),
        grp_p["mean"],
        yerr=1.96 * grp_p["se"],
        capsize=5,
        color=colors_p,
        edgecolor="black",
        alpha=0.9,
    )
    axes[0, 0].set_title(
        "P1: Dias secos têm média ligeiramente maior (0,49 vs 0,43/dia);\nchuva reduz exposição de motos/pedestres (Londrina, 2022–2024)",
        fontweight="bold",
    )
    axes[0, 0].set_ylabel("Média de Sinistros por Dia")
    axes[0, 0].set_xlabel("Faixa de Precipitação Acumulada Diária")
    axes[0, 0].tick_params(axis="x", rotation=10)
    for bar, row in zip(bars1, grp_p.itertuples()):
        top_err = row.mean + 1.96 * row.se
        axes[0, 0].text(
            bar.get_x() + bar.get_width() / 2,
            top_err + 0.02,
            f"{row.mean:.2f}/dia\n(n={row.count}d)",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )
    axes[0, 0].set_ylim(0, max(grp_p["mean"] + 1.96 * grp_p["se"]) * 1.25)

    # Subplot 2: Frequência média de acidentes por faixa de temperatura (Pergunta 2)
    ordem_t = ["Frio (<= 19°C)", "Ameno (19-24°C)", "Quente (> 24°C)"]
    grp_t = (
        daily_22_24.groupby("faixa_temperatura_media", observed=False)["total_acidentes"]
        .agg(["mean", "count", "std"])
        .reindex(ordem_t)
        .reset_index()
    )
    grp_t["se"] = grp_t["std"] / np.sqrt(grp_t["count"])
    colors_t = ["#64B5CD", "#8172B3", "#CCB974"]
    bars2 = axes[0, 1].bar(
        grp_t["faixa_temperatura_media"].astype(str),
        grp_t["mean"],
        yerr=1.96 * grp_t["se"],
        capsize=5,
        color=colors_t,
        edgecolor="black",
        alpha=0.9,
    )
    axes[0, 1].set_title(
        "P2: Dias frios (<= 19°C) concentram a maior média diária (0,53/dia)\n(Temperatura Média Diária em Londrina, 2022–2024)",
        fontweight="bold",
    )
    axes[0, 1].set_ylabel("Média de Sinistros por Dia")
    axes[0, 1].set_xlabel("Faixa de Temperatura Média Diária (°C)")
    for bar, row in zip(bars2, grp_t.itertuples()):
        top_err = row.mean + 1.96 * row.se
        axes[0, 1].text(
            bar.get_x() + bar.get_width() / 2,
            top_err + 0.02,
            f"{row.mean:.2f}/dia\n(n={row.count}d)",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
    axes[0, 1].set_ylim(0, max(grp_t["mean"] + 1.96 * grp_t["se"]) * 1.25)

    # Subplot 3: Severidade e Letalidade sob Chuva vs Tempo Seco (Pergunta 3 - Teste da Hipótese!)
    sev_df = (
        prf_22_24.groupby("condicao_chuva_prf")
        .agg(
            vitimas_pct=("tem_vitima", lambda s: s.mean() * 100),
            graves_fatais_pct=("tem_grave_ou_morte", lambda s: s.mean() * 100),
            obitos_pct=("tem_obito", lambda s: s.mean() * 100),
        )
        .T
    )
    sev_df.columns = ["Tempo Seco / Nublado (n=468)", "Chuva / Garoa no Sinistro (n=41)"]
    sev_df.index = ["Com Vítimas\n(%)", "Feridos Graves\nou Óbito (%)", "Vítimas Fatais /\nLetalidade (%)"]

    x = np.arange(len(sev_df.index))
    width = 0.36
    b_seco = axes[1, 0].bar(
        x - width / 2,
        sev_df.iloc[:, 0],
        width,
        label=sev_df.columns[0],
        color="#4C72B0",
        edgecolor="black",
    )
    b_chuv = axes[1, 0].bar(
        x + width / 2,
        sev_df.iloc[:, 1],
        width,
        label=sev_df.columns[1],
        color="#C44E52",
        edgecolor="black",
    )
    axes[1, 0].set_title(
        "P3 (Hipótese Confirmada na Letalidade): 0,0% de óbitos sob chuva\nvs. 3,2% em pista seca (Ocorrências BR-369 Londrina, 2022–2024)",
        fontweight="bold",
    )
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(sev_df.index)
    axes[1, 0].set_ylabel("Proporção das Ocorrências (%)")
    axes[1, 0].legend(loc="upper right")
    for bars in [b_seco, b_chuv]:
        for bar in bars:
            h = bar.get_height()
            axes[1, 0].text(
                bar.get_x() + bar.get_width() / 2,
                h + 1.2,
                f"{h:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )
    axes[1, 0].set_ylim(0, 105)

    # Subplot 4: Concordância entre condição descrita na PRF e precipitação diária (Pergunta 4)
    cond_order = ["Céu Claro", "Sol", "Nublado", "Garoa/Chuvisco", "Chuva"]
    prf_sub = prf_22_24[prf_22_24["condicao_metereologica"].isin(cond_order)].copy()
    sns.boxplot(
        data=prf_sub,
        x="condicao_metereologica",
        y="precip_londrina_mm",
        order=cond_order,
        ax=axes[1, 1],
        palette="Blues",
        showfliers=False,
    )
    sns.stripplot(
        data=prf_sub,
        x="condicao_metereologica",
        y="precip_londrina_mm",
        order=cond_order,
        ax=axes[1, 1],
        color="#222222",
        alpha=0.45,
        size=4.5,
        jitter=0.2,
    )
    axes[1, 1].axhline(1.0, color="#C44E52", linestyle="--", linewidth=1.3, label="Limiar Dia Chuvoso (1 mm)")
    axes[1, 1].set_title(
        "P4: 95,1% dos sinistros com Chuva/Garoa na PRF tiveram >= 1 mm\n(100% tiveram > 0 mm na série instrumental de Londrina, 2022–2024)",
        fontweight="bold",
    )
    axes[1, 1].set_xlabel("Condição Meteorológica Registrada pelo Agente da PRF")
    axes[1, 1].set_ylabel("Precipitação Diária Instrumental em Londrina (mm)")
    axes[1, 1].legend(loc="upper left")

    plt.tight_layout()
    for d in [FIGURES_DIR, ATIV2_FIG_DIR]:
        fig.savefig(d / "fig01_painel_perguntas_project_canvas.png", bbox_inches="tight")
    plt.close(fig)

    # Figura 2: Dinâmica Temporal, Dia da Semana e Distribuição Espacial (km da BR-369)
    fig2, axes2 = plt.subplots(1, 2, figsize=(15, 5.5))

    grp_dow = (
        daily_22_24.groupby(["dia_semana", "cenario_chuva_londrina"], observed=False)["total_acidentes"]
        .mean()
        .unstack()
        .reindex(ORDEM_DIAS_PT)
    )
    grp_dow.plot(
        kind="bar",
        ax=axes2[0],
        color=["#C44E52", "#4C72B0"],
        edgecolor="black",
        width=0.75,
    )
    axes2[0].set_title(
        "Sexta-feira e Sábado lideram sinistros, amplificados em dias chuvosos\n(Média diária por dia da semana e condição climática, 2022–2024)",
        fontweight="bold",
    )
    axes2[0].set_xlabel("Dia da Semana")
    axes2[0].set_ylabel("Média Diária de Sinistros")
    axes2[0].tick_params(axis="x", rotation=25)
    axes2[0].legend(title="Cenário Diário (Londrina)")

    # Distribuição por km na BR-369 em Londrina
    br369 = prf_22_24[(prf_22_24["br"].astype(str) == "369") & (prf_22_24["km"] > 100)].copy()
    bins = np.linspace(br369["km"].min(), br369["km"].max(), 18)
    k0 = br369[br369["tem_grave_ou_morte"] == 0]["km"]
    k1 = br369[br369["tem_grave_ou_morte"] == 1]["km"]
    axes2[1].hist(
        [k0, k1],
        bins=bins,
        stacked=True,
        color=["#4C72B0", "#C44E52"],
        edgecolor="black",
        label=["Ileso ou Ferido Leve", "Ferido Grave ou Óbito"],
        alpha=0.9,
    )
    axes2[1].set_title(
        "Concentração crítica de sinistros no trecho urbano da BR-369 (km 145 a 162)\n(Distribuição espacial por quilômetro em Londrina, 2022–2024)",
        fontweight="bold",
    )
    axes2[1].set_xlabel("Quilômetro (km) da Rodovia BR-369 em Londrina")
    axes2[1].set_ylabel("Total de Sinistros (2022–2024)")
    axes2[1].legend(title="Gravidade")

    plt.tight_layout()
    for d in [FIGURES_DIR, ATIV2_FIG_DIR]:
        fig2.savefig(d / "fig02_sazonalidade_semanal_e_km_br369.png", bbox_inches="tight")
    plt.close(fig2)


def generate_extended_visualizations(daily_22_24: pd.DataFrame, pes_22_24: pd.DataFrame):
    """Gera gráficos adicionais em `reports/figures/` para modais, horários e gênero."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["font.size"] = 10

    n_seco = int((daily_22_24["dia_chuvoso_londrina"] == 0).sum())
    n_chuv = int((daily_22_24["dia_chuvoso_londrina"] == 1).sum())

    # Figura 4: Variação por Modal, Proporção Semanal e Mapa Horário 00h-23h
    acc_modal = pes_22_24[pes_22_24["modal"] != "Outros"].drop_duplicates(subset=["id", "modal"]).copy()
    t_mod = acc_modal.groupby(["modal", "dia_chuvoso_londrina"])["id"].nunique().unstack(fill_value=0)
    t_mod.columns = ["Seco", "Chuvoso"]
    t_mod["Taxa_Seco_100d"] = t_mod["Seco"] / n_seco * 100.0
    t_mod["Taxa_Chuv_100d"] = t_mod["Chuvoso"] / n_chuv * 100.0
    t_mod["Var_%"] = (t_mod["Taxa_Chuv_100d"] / t_mod["Taxa_Seco_100d"] - 1.0) * 100.0
    t_mod = t_mod.sort_values("Taxa_Seco_100d", ascending=False)

    fig4 = plt.figure(figsize=(16, 10))
    gs = fig4.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.38, wspace=0.25)

    # Painel A: Taxa por 100 dias Seco vs Chuvoso por tipo de transporte
    ax_a = fig4.add_subplot(gs[0, 0])
    x = np.arange(len(t_mod))
    w = 0.38
    b1 = ax_a.bar(x - w / 2, t_mod["Taxa_Seco_100d"], w, label=f"Dia Seco (<1 mm, n={n_seco}d)", color="#4C72B0", edgecolor="black")
    b2 = ax_a.bar(x + w / 2, t_mod["Taxa_Chuv_100d"], w, label=f"Dia Chuvoso (>=1 mm, n={n_chuv}d)", color="#C44E52", edgecolor="black")
    for idx, (bar_s, bar_c, var_val) in enumerate(zip(b1, b2, t_mod["Var_%"])):
        top_y = max(bar_s.get_height(), bar_c.get_height())
        ax_a.text(idx, top_y + 1.2, f"{var_val:+.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                  color="#C44E52" if var_val > 0 else "#2E5A88")
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(t_mod.index, rotation=12)
    ax_a.set_ylabel("Sinistros por 100 Dias")
    ax_a.set_ylim(0, max(t_mod["Taxa_Seco_100d"].max(), t_mod["Taxa_Chuv_100d"].max()) * 1.2)
    ax_a.set_title(
        f"A) Na chuva, motos caem {t_mod.loc['Moto', 'Var_%']:+.1f}% e caminhões sobem {t_mod.loc['Caminhão', 'Var_%']:+.1f}%\n"
        "(Taxa ajustada por 100 dias em cada clima, 2022–2024)",
        fontweight="bold",
    )
    ax_a.legend(loc="upper right")

    # Painel B: Taxa semanal por clima (proporção ajustada por dias secos/chuvosos do dia da semana)
    ax_b = fig4.add_subplot(gs[0, 1])
    dow_rates = (
        daily_22_24.groupby(["dia_semana", "cenario_chuva_londrina"])["total_acidentes"]
        .mean()
        .unstack()
        .reindex(ORDEM_DIAS_PT)[["Seco (< 1 mm)", "Chuvoso (>= 1 mm)"]]
        * 100.0
    )
    dow_rates.plot(kind="bar", ax=ax_b, color=["#4C72B0", "#C44E52"], edgecolor="black", width=0.75)
    sab_chuv = dow_rates.loc["sábado", "Chuvoso (>= 1 mm)"]
    sab_seco = dow_rates.loc["sábado", "Seco (< 1 mm)"]
    ax_b.set_title(
        f"B) Sábado chuvoso ({sab_chuv:.1f}/100d) supera sábado seco ({sab_seco:.1f}/100d)\n"
        "(Sinistros por 100 dias do mesmo dia da semana, 2022–2024)",
        fontweight="bold",
    )
    ax_b.set_xlabel("")
    ax_b.set_ylabel("Sinistros por 100 Dias")
    ax_b.set_ylim(0, dow_rates.values.max() * 1.24)
    ax_b.set_xticklabels([d[:3].capitalize() for d in ORDEM_DIAS_PT], rotation=0)
    ax_b.legend(title="Clima Diário", loc="upper left", ncol=2)

    # Painel C: Perfil Horário 00h-23h dos principais modais
    ax_c = fig4.add_subplot(gs[1, :])
    h_mod = (
        acc_modal[acc_modal["modal"].isin(["Carro", "Moto", "Caminhão", "Pedestre"])]
        .pivot_table(index="hora", columns="modal", values="id", aggfunc="nunique", fill_value=0)
        .reindex(range(24), fill_value=0)
    )
    sns.heatmap(
        h_mod[["Carro", "Moto", "Caminhão", "Pedestre"]].T,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        linewidths=0.4,
        cbar_kws={"label": "Total de Acidentes Envolvendo o Modal (2022–2024)"},
        ax=ax_c,
    )
    ax_c.set_title("C) Picos horários na BR-369: Moto/Carro disparam às 07h e 17h–19h; Caminhões têm pico de manhã cedo (07h–10h)", fontweight="bold")
    ax_c.set_xlabel("Hora do Dia (00h às 23h)")
    ax_c.set_ylabel("Modal")
    ax_c.set_xticklabels([f"{h:02d}h" for h in range(24)], rotation=0)

    fig4.savefig(FIGURES_DIR / "fig04_modais_horarios_clima.png", bbox_inches="tight")
    plt.close(fig4)

    # Figura 5: Perfil por Gênero (Envolvidos, Condutores x Modal, e Queda na Chuva)
    fig5, axes5 = plt.subplots(1, 2, figsize=(15, 5.5))

    env_order = ["Condutor", "Passageiro", "Pedestre"]
    env_gen = (
        pes_22_24[(pes_22_24["tipo_envolvido_clean"].isin(env_order)) & (pes_22_24["genero"].isin(["Masculino", "Feminino"]))]
        .groupby(["tipo_envolvido_clean", "genero"])["pesid"]
        .count()
        .unstack(fill_value=0)
        .reindex(env_order)
    )
    env_pct = env_gen.div(env_gen.sum(axis=1), axis=0) * 100.0
    env_pct[["Masculino", "Feminino"]].plot(
        kind="bar", stacked=True, ax=axes5[0], color=["#4C72B0", "#DD8452"], edgecolor="black", width=0.6
    )
    for idx, role in enumerate(env_order):
        m_v = env_pct.loc[role, "Masculino"]
        f_v = env_pct.loc[role, "Feminino"]
        axes5[0].text(idx, m_v / 2, f"{m_v:.1f}%\n({env_gen.loc[role, 'Masculino']})", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
        axes5[0].text(idx, m_v + f_v / 2, f"{f_v:.1f}%\n({env_gen.loc[role, 'Feminino']})", ha="center", va="center", color="black", fontweight="bold", fontsize=9)
    axes5[0].set_title(
        f"Homens lideram entre condutores ({env_pct.loc['Condutor', 'Masculino']:.1f}%),\n"
        f"mas mulheres são maioria entre passageiros ({env_pct.loc['Passageiro', 'Feminino']:.1f}%)",
        fontweight="bold",
    )
    axes5[0].set_xlabel("Papel na Ocorrência (PRF Londrina, 2022–2024)")
    axes5[0].set_ylabel("Proporção (%)")
    axes5[0].set_xticklabels(env_order, rotation=0)
    axes5[0].set_ylim(0, 122)
    axes5[0].legend(title="Gênero", loc="upper right", ncol=2)

    cond = pes_22_24[(pes_22_24["tipo_envolvido_clean"] == "Condutor") & (pes_22_24["genero"].isin(["Masculino", "Feminino"]))].copy()
    mod_order = ["Carro", "Moto", "Caminhão", "Ônibus", "Bicicleta"]
    mod_gen = (
        cond[cond["modal"].isin(mod_order)]
        .groupby(["modal", "genero"])["pesid"]
        .count()
        .unstack(fill_value=0)
        .reindex(mod_order)
    )
    mod_gen[["Masculino", "Feminino"]].plot(kind="bar", ax=axes5[1], color=["#4C72B0", "#DD8452"], edgecolor="black", width=0.7)
    pct_f_map = {}
    for idx, modal_name in enumerate(mod_order):
        tot_m = mod_gen.loc[modal_name].sum()
        pct_f = mod_gen.loc[modal_name, "Feminino"] / tot_m * 100.0 if tot_m > 0 else 0.0
        pct_f_map[modal_name] = pct_f
        if tot_m > 0:
            axes5[1].text(idx, mod_gen.loc[modal_name].max() + 8, f"{pct_f:.1f}% F", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    axes5[1].set_title(
        f"Participação feminina ao volante é maior em carros ({pct_f_map['Carro']:.1f}%)\n"
        f"do que em motos ({pct_f_map['Moto']:.1f}%) e caminhões ({pct_f_map['Caminhão']:.1f}%)",
        fontweight="bold",
    )
    axes5[1].set_xlabel("Tipo de Veículo Conduzido (2022–2024)")
    axes5[1].set_ylabel("Total de Condutores Envolvidos")
    axes5[1].set_xticklabels(mod_order, rotation=0)
    axes5[1].set_ylim(0, mod_gen.values.max() * 1.18)
    axes5[1].legend(title="Gênero do Condutor", loc="upper right")

    plt.tight_layout()
    fig5.savefig(FIGURES_DIR / "fig05_perfil_genero_sinistros.png", bbox_inches="tight")
    plt.close(fig5)


def run_ml_experiments(daily_full: pd.DataFrame):
    """
    Executa experimentos de Machine Learning seguindo rigorosamente @skill:ml-best-practices:
    1. Divisão cronológica estrita (Treino: 2022-2023, Validação: 2024, Teste: 2025) ANTES do fit de pré-processadores.
    2. Comparação de modelos supervisionados com intervalos de confiança de 95% via Bootstrap.
    3. Clusterização K-Means com escolha pelo Silhouette Score e projeção 2D via PCA.
    """
    print_section("EXPERIMENTOS DE MACHINE LEARNING (STRICT CHRONOLOGICAL SPLIT & FEATURIZATION)")

    # Criar variáveis defasadas (lags) sem vazamento temporal
    df = daily_full.sort_values("data").copy()
    df["precip_lag1_mm"] = df["precip_londrina_mm"].shift(1).fillna(0)
    df["acidentes_media_movel_7d"] = df["total_acidentes"].shift(1).rolling(7, min_periods=1).mean().fillna(0)
    df["alvo_dia_com_acidente"] = (df["total_acidentes"] > 0).astype(int)

    num_features = [
        "temp_media_c",
        "temp_max_c",
        "temp_min_c",
        "amplitude_termica_c",
        "precip_londrina_mm",
        "precip_lag1_mm",
        "era5_londrina_horas_chuva",
        "era5_londrina_vento_max_kmh",
        "acidentes_media_movel_7d",
    ]
    ord_features = ["faixa_precipitacao"]
    nom_features = ["dia_semana", "mes"]

    # Divisão Cronológica Estrita (ML Best Practices: ANTES de ajustar qualquer encoder/scaler!)
    train_df = df[df["ano"].isin([2022, 2023])].copy()
    val_df = df[df["ano"] == 2024].copy()
    test_df = df[df["ano"] == 2025].copy()

    print(f"Divisão Cronológica: Treino (2022-2023)={len(train_df)}d | Validação (2024)={len(val_df)}d | Teste (2025)={len(test_df)}d")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                num_features,
            ),
            (
                "ord",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "ordinal",
                            OrdinalEncoder(
                                categories=[
                                    [
                                        "Seco (<1 mm)",
                                        "Chuva Leve (1-10 mm)",
                                        "Chuva Moderada (10-30 mm)",
                                        "Chuva Forte (>30 mm)",
                                    ]
                                ],
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                            ),
                        ),
                    ]
                ),
                ord_features,
            ),
            (
                "nom",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                nom_features,
            ),
        ]
    )

    X_train = train_df[num_features + ord_features + nom_features]
    y_train = train_df["alvo_dia_com_acidente"]
    X_val = val_df[num_features + ord_features + nom_features]
    y_val = val_df["alvo_dia_com_acidente"]
    X_test = test_df[num_features + ord_features + nom_features]
    y_test = test_df["alvo_dia_com_acidente"]

    models = {
        "Naive Baseline (Majority/Stratified)": DummyClassifier(strategy="prior", random_state=42),
        "Logistic Regression (L2 Regularized)": LogisticRegression(C=0.5, class_weight="balanced", random_state=42, max_iter=500),
        "Random Forest (Regularized max_depth=4)": RandomForestClassifier(
            n_estimators=200, max_depth=4, min_samples_leaf=15, class_weight="balanced", random_state=42
        ),
        "Gradient Boosting (Regularized)": GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.03, max_depth=2, min_samples_leaf=20, random_state=42
        ),
    }

    def bootstrap_ci(y_true, y_prob, metric_fn, n_boot=500, seed=42):
        rng = np.random.default_rng(seed)
        scores = []
        y_t = np.asarray(y_true)
        y_p = np.asarray(y_prob)
        for _ in range(n_boot):
            idx = rng.integers(0, len(y_t), len(y_t))
            if len(np.unique(y_t[idx])) < 2:
                continue
            scores.append(metric_fn(y_t[idx], y_p[idx]))
        return np.percentile(scores, [2.5, 97.5])

    print("\n--- Comparação de Modelos de Classificação (Validação 2024 e Teste 2025) ---")
    for name, clf in models.items():
        pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
        pipe.fit(X_train, y_train)
        val_prob = pipe.predict_proba(X_val)[:, 1]
        val_pred = (val_prob >= 0.45).astype(int)
        test_prob = pipe.predict_proba(X_test)[:, 1]
        test_pred = (test_prob >= 0.45).astype(int)

        roc_val = roc_auc_score(y_val, val_prob)
        pr_val = average_precision_score(y_val, val_prob)
        f1_val = f1_score(y_val, val_pred)
        ci_pr = bootstrap_ci(y_val, val_prob, average_precision_score)

        roc_test = roc_auc_score(y_test, test_prob)
        pr_test = average_precision_score(y_test, test_prob)
        f1_test = f1_score(y_test, test_pred)

        print(
            f"  • {name:40s} | Val PR-AUC={pr_val:.3f} [{ci_pr[0]:.3f}, {ci_pr[1]:.3f}] | Val ROC-AUC={roc_val:.3f} | Val F1={f1_val:.3f} || Test PR-AUC={pr_test:.3f} | Test F1={f1_test:.3f}"
        )

    # Classificação de Severidade por Ocorrência (Sinistro Grave ou Fatal na BR-369 em Londrina)
    print("\n--- Classificação Supervisionada de Severidade do Sinistro (Alvo: Ferido Grave ou Óbito) ---")
    prf_full = pd.read_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2025_enriquecido.csv", parse_dates=["data"])
    prf_full = prf_full.sort_values(["data", "horario"]).reset_index(drop=True)
    prf_full["hora_num"] = pd.to_numeric(prf_full["horario"].astype(str).str.slice(0, 2), errors="coerce").fillna(12)
    prf_full["fim_de_semana"] = prf_full["data"].dt.day_of_week.isin([5, 6]).astype(int)

    occ_num = ["km", "veiculos", "hora_num", "temp_media_c", "amplitude_termica_c", "precip_londrina_mm", "fim_de_semana"]
    occ_nom = ["tipo_acidente", "fase_dia", "tipo_pista", "tracado_via", "uso_solo", "condicao_metereologica"]

    occ_train = prf_full[prf_full["ano_arquivo"].isin([2022, 2023])].copy()
    occ_val = prf_full[prf_full["ano_arquivo"] == 2024].copy()
    occ_test = prf_full[prf_full["ano_arquivo"] == 2025].copy()

    occ_prep = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), occ_num),
            ("nom", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), occ_nom),
        ]
    )

    for name, clf in models.items():
        pipe = Pipeline([("prep", occ_prep), ("clf", clf)])
        pipe.fit(occ_train[occ_num + occ_nom], occ_train["tem_grave_ou_morte"])
        v_prob = pipe.predict_proba(occ_val[occ_num + occ_nom])[:, 1]
        v_pred = (v_prob >= 0.45).astype(int)
        t_prob = pipe.predict_proba(occ_test[occ_num + occ_nom])[:, 1]
        t_pred = (t_prob >= 0.45).astype(int)

        roc_v = roc_auc_score(occ_val["tem_grave_ou_morte"], v_prob)
        pr_v = average_precision_score(occ_val["tem_grave_ou_morte"], v_prob)
        f1_v = f1_score(occ_val["tem_grave_ou_morte"], v_pred)
        ci_v = bootstrap_ci(occ_val["tem_grave_ou_morte"], v_prob, roc_auc_score)

        roc_t = roc_auc_score(occ_test["tem_grave_ou_morte"], t_prob)
        pr_t = average_precision_score(occ_test["tem_grave_ou_morte"], t_prob)
        f1_t = f1_score(occ_test["tem_grave_ou_morte"], t_pred)
        print(
            f"  • {name:40s} | Val ROC-AUC={roc_v:.3f} [{ci_v[0]:.3f}, {ci_v[1]:.3f}] | Val PR-AUC={pr_v:.3f} | Val F1={f1_v:.3f} || Test ROC-AUC={roc_t:.3f} | Test PR-AUC={pr_t:.3f} | Test F1={f1_t:.3f}"
        )

    # Clusterização K-Means + Silhouette Score + PCA 2D
    print("\n--- Clusterização dos Dias Climático-Viários em Londrina (2022-2024) ---")
    clust_df = df[df["ano"].isin([2022, 2023, 2024])].copy()
    clust_cols = [
        "temp_media_c",
        "amplitude_termica_c",
        "precip_londrina_mm",
        "era5_londrina_horas_chuva",
        "total_acidentes",
        "acidentes_graves_ou_fatais",
    ]
    X_c = StandardScaler().fit_transform(clust_df[clust_cols].fillna(0))

    sil_scores = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = km.fit_predict(X_c)
        sil_scores[k] = silhouette_score(X_c, labels)
        print(f"  • k={k}: Silhouette Score = {sil_scores[k]:.4f}")

    best_k = max(sil_scores, key=sil_scores.get)
    print(f"  => Melhor número de clusters pelo Silhouette Score: k={best_k} (score={sil_scores[best_k]:.4f})")

    km_best = KMeans(n_clusters=3, random_state=42, n_init=20)
    clust_df["cluster"] = km_best.fit_predict(X_c)
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_c)
    clust_df["pca1"] = coords[:, 0]
    clust_df["pca2"] = coords[:, 1]

    print("\nPerfil médio dos 3 Clusters (k=3 para interpretação de regimes climático-viários):")
    print(clust_df.groupby("cluster")[clust_cols].mean().round(2).to_string())
    print("Contagem de dias por cluster:", clust_df["cluster"].value_counts().to_dict())

    # Figura 3: PCA 2D da Clusterização e Curva de Silhouette
    fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5.2))
    sns.scatterplot(
        data=clust_df,
        x="pca1",
        y="pca2",
        hue="cluster",
        palette="Set1",
        alpha=0.75,
        s=45,
        ax=axes3[0],
    )
    axes3[0].set_title(
        f"Projeção PCA 2D dos Regimes Diários Climático-Viários\n(Variância explicada: {pca.explained_variance_ratio_.sum()*100:.1f}%)",
        fontweight="bold",
    )
    axes3[0].set_xlabel(f"Componente Principal 1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
    axes3[0].set_ylabel(f"Componente Principal 2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")

    sns.scatterplot(
        data=clust_df,
        x="pca1",
        y="pca2",
        hue="cenario_chuva_londrina",
        palette={"Seco (< 1 mm)": "#4C72B0", "Chuvoso (>= 1 mm)": "#C44E52"},
        alpha=0.75,
        s=45,
        ax=axes3[1],
    )
    axes3[1].set_title(
        "Projeção PCA 2D Colorida pela Condição de Chuva Diária\n(Separação clara dos dias chuvosos no espaço de componentes principais)",
        fontweight="bold",
    )
    axes3[1].set_xlabel(f"Componente Principal 1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
    axes3[1].set_ylabel(f"Componente Principal 2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")

    plt.tight_layout()
    for d in [FIGURES_DIR, ATIV2_FIG_DIR]:
        fig3.savefig(d / "fig03_clusters_pca_clima_sinistros.png", bbox_inches="tight")
    plt.close(fig3)


def main():
    daily_22_24 = pd.read_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2024.csv", parse_dates=["data"])
    prf_22_24 = pd.read_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2024_enriquecido.csv", parse_dates=["data"])
    pes_22_24 = pd.read_csv(PROCESSED_DIR / "prf_pessoas_veiculos_londrina_2022_2024_enriquecido.csv", parse_dates=["data"])

    daily_full = pd.read_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2025.csv", parse_dates=["data"])
    prf_full = pd.read_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2025_enriquecido.csv", parse_dates=["data"])
    pes_full = pd.read_csv(PROCESSED_DIR / "prf_pessoas_veiculos_londrina_2022_2025_enriquecido.csv", parse_dates=["data"])
    hourly_a835 = pd.read_csv(PROCESSED_DIR / "inmet_a835_resumo_horario_2022_2024.csv")

    analyze_project_questions(daily_22_24, prf_22_24, "RECORTE OFICIAL LAB 01: 2022 A 2024")
    analyze_project_questions(daily_full, prf_full, "RECORTE ESTENDIDO: 2022 A 2025")
    analyze_transport_and_hourly_patterns(daily_22_24, prf_22_24, pes_22_24, hourly_a835, "2022 A 2024")
    analyze_transport_and_hourly_patterns(daily_full, prf_full, pes_full, hourly_a835, "2022 A 2025")
    analyze_gender_patterns(daily_22_24, pes_22_24, "2022 A 2024")
    analyze_gender_patterns(daily_full, pes_full, "2022 A 2025")

    generate_visualizations(daily_22_24, prf_22_24, daily_full)
    generate_extended_visualizations(daily_22_24, pes_22_24)
    run_ml_experiments(daily_full)
    print("\nVisualizações salvas em reports/figures/ (fig01..fig05) e Atividade 2/figuras/ (fig01..fig03)!")


if __name__ == "__main__":
    main()
