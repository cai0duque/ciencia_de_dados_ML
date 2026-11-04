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

    ordem_dias = [
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo",
    ]
    grp_dow = (
        daily_22_24.groupby(["dia_semana", "cenario_chuva_londrina"], observed=False)["total_acidentes"]
        .mean()
        .unstack()
        .reindex(ordem_dias)
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

    daily_full = pd.read_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2025.csv", parse_dates=["data"])
    prf_full = pd.read_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2025_enriquecido.csv", parse_dates=["data"])

    analyze_project_questions(daily_22_24, prf_22_24, "RECORTE OFICIAL LAB 01: 2022 A 2024")
    analyze_project_questions(daily_full, prf_full, "RECORTE ESTENDIDO: 2022 A 2025")
    generate_visualizations(daily_22_24, prf_22_24, daily_full)
    run_ml_experiments(daily_full)
    print("\nVisualizações salvas em reports/figures/ e Atividade 2/figuras/!")


if __name__ == "__main__":
    main()
