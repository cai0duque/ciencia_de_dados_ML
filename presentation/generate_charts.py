#!/usr/bin/env python3
"""
Gera gráficos sob medida (300 DPI, tipografia >= 14pt, fundo limpo)
para a apresentação Marp (`presentation/slides.md`) diretamente a partir
das bases validadas em `data/processed/`.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

NAVY = "#0F2942"
BLUE = "#2563EB"
CORAL = "#DC2626"
TEAL = "#0D9488"
AMBER = "#D97706"
SLATE = "#475569"
GRID_COLOR = "#E2E8F0"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Inter", "Segoe UI"],
        "font.size": 14,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "axes.labelsize": 14,
        "xtick.labelsize": 13.5,
        "ytick.labelsize": 13.5,
        "axes.edgecolor": "#CBD5E1",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FFFFFF",
    }
)


def make_chart01_clima_modais(daily_24: pd.DataFrame, pes_24: pd.DataFrame, daily_25: pd.DataFrame, pes_25: pd.DataFrame) -> None:
    """Gráfico 1: Taxa por 100 dias (Seco vs. Chuvoso) por tipo de transporte."""
    n_seco = int((daily_24["dia_chuvoso_londrina"] == 0).sum())
    n_chuv = int((daily_24["dia_chuvoso_londrina"] == 1).sum())

    acc_m = pes_24[pes_24["modal"] != "Outros"].drop_duplicates(subset=["id", "modal"])
    t_mod = acc_m.groupby(["modal", "dia_chuvoso_londrina"])["id"].nunique().unstack(fill_value=0)
    t_mod.columns = ["Seco", "Chuv"]
    t_mod["Taxa_Seco"] = t_mod["Seco"] / n_seco * 100.0
    t_mod["Taxa_Chuv"] = t_mod["Chuv"] / n_chuv * 100.0
    t_mod["Var_%"] = (t_mod["Taxa_Chuv"] / t_mod["Taxa_Seco"] - 1.0) * 100.0

    # Confirmar Caminhão 2022-2025 para nota de rodapé
    ns25 = int((daily_25["dia_chuvoso_londrina"] == 0).sum())
    nc25 = int((daily_25["dia_chuvoso_londrina"] == 1).sum())
    acc_m25 = pes_25[pes_25["modal"] == "Caminhão"].drop_duplicates(subset=["id", "modal"])
    c25_s = acc_m25[acc_m25["dia_chuvoso_londrina"] == 0]["id"].nunique() / ns25 * 100.0
    c25_c = acc_m25[acc_m25["dia_chuvoso_londrina"] == 1]["id"].nunique() / nc25 * 100.0
    var_cam_25 = (c25_c / c25_s - 1.0) * 100.0

    ordem = ["Bicicleta", "Ônibus", "Pedestre", "Caminhão", "Moto", "Carro"]
    df_p = t_mod.reindex(ordem)

    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    y = np.arange(len(df_p))
    h = 0.36

    b1 = ax.barh(y + h / 2, df_p["Taxa_Seco"], height=h, color=BLUE, edgecolor=NAVY, linewidth=0.8, label=f"Dia Seco (< 1 mm, n={n_seco}d)")
    b2 = ax.barh(y - h / 2, df_p["Taxa_Chuv"], height=h, color=CORAL, edgecolor=NAVY, linewidth=0.8, label=f"Dia Chuvoso (>= 1 mm, n={n_chuv}d)")

    for idx, (modal_name, row) in enumerate(df_p.iterrows()):
        max_x = max(row["Taxa_Seco"], row["Taxa_Chuv"])
        var_v = row["Var_%"]
        is_up = var_v > 0
        txt_color = CORAL if is_up else SLATE
        bg_color = "#FEE2E2" if is_up else "#F1F5F9"
        ax.text(
            max_x + 1.0,
            idx,
            f"{var_v:+.1f}%",
            va="center",
            ha="left",
            fontsize=14,
            fontweight="bold",
            color=txt_color,
            bbox=dict(boxstyle="round,pad=0.25", facecolor=bg_color, edgecolor="none"),
        )

    ax.set_yticks(y)
    ax.set_yticklabels(df_p.index, fontweight="bold", color=NAVY)
    ax.set_xlabel("Sinistros por 100 Dias do Mesmo Clima (2022–2024)", fontweight="bold", color=NAVY)
    ax.set_xlim(0, 44)
    ax.grid(axis="x", color=GRID_COLOR, linestyle="--", linewidth=0.9)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=13)
    ax.set_title("Variação de Sinistros na Chuva por Modal", loc="left", color=NAVY, pad=10)
    fig.text(
        0.02,
        0.01,
        f"Nota: Em 2022–2025 (1.461d), Caminhões ampliam alta na chuva para {var_cam_25:+.1f}% (8,76 vs. 6,90/100d).",
        fontsize=11.5,
        color=SLATE,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(ASSETS_DIR / "chart01_clima_modais.png", dpi=300)
    plt.close(fig)


def make_chart02_letalidade_severidade(prf_24: pd.DataFrame, prf_25: pd.DataFrame) -> None:
    """Gráfico 2: Severidade e Letalidade (Momento PRF vs. Dia Instrumental)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 5.3), gridspec_kw={"width_ratios": [1.35, 1.05]})

    # Painel Esquerdo: Momento exato do sinistro (PRF 2022-2024)
    s_prf = (
        prf_24.groupby("condicao_chuva_prf")
        .agg(
            vit=("tem_vitima", lambda s: s.mean() * 100.0),
            gf=("tem_grave_ou_morte", lambda s: s.mean() * 100.0),
            let=("tem_obito", lambda s: s.mean() * 100.0),
        )
    )
    cats = ["Com Vítimas\n(%)", "Graves ou\nÓbito (%)", "Letalidade /\nÓbitos (%)"]
    vals_seco = [s_prf.loc[0, "vit"], s_prf.loc[0, "gf"], s_prf.loc[0, "let"]]
    vals_chuv = [s_prf.loc[1, "vit"], s_prf.loc[1, "gf"], s_prf.loc[1, "let"]]

    x = np.arange(len(cats))
    w = 0.36
    b1 = ax1.bar(x - w / 2, vals_seco, width=w, color=BLUE, edgecolor=NAVY, label="Sem Chuva PRF (n=468)")
    b2 = ax1.bar(x + w / 2, vals_chuv, width=w, color=TEAL, edgecolor=NAVY, label="Chuva/Garoa PRF (n=41)")

    for bars, is_rain in [(b1, False), (b2, True)]:
        for idx, bar in enumerate(bars):
            val = bar.get_height()
            lbl = f"{val:.2f}%" if idx == 2 else f"{val:.1f}%"
            col = TEAL if (is_rain and idx == 2) else NAVY
            x_nudge = 0.04 if is_rain else -0.04
            y_off = 2.2 if idx != 2 else (2.5 if not is_rain else 1.5)
            ax1.text(
                bar.get_x() + bar.get_width() / 2 + x_nudge,
                val + y_off,
                lbl,
                ha="center",
                va="bottom",
                fontsize=11.5,
                fontweight="bold",
                color=col,
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(cats, fontweight="bold", color=NAVY)
    ax1.set_ylabel("Proporção das Ocorrências (%)", fontweight="bold", color=NAVY)
    ax1.set_ylim(0, 114)
    ax1.grid(axis="y", color=GRID_COLOR, linestyle="--", linewidth=0.9)
    ax1.set_axisbelow(True)
    ax1.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=11)
    ax1.set_title("A) Momento do Sinistro (PRF)", loc="left", fontsize=15, color=NAVY, pad=10)

    # Painel Direito: Letalidade por Dia Instrumental (>= 1 mm) em 2022-24 e 2022-25
    l24_s = prf_24[prf_24["dia_chuvoso_londrina"] == 0]["tem_obito"].mean() * 100.0
    l24_c = prf_24[prf_24["dia_chuvoso_londrina"] == 1]["tem_obito"].mean() * 100.0
    l25_s = prf_25[prf_25["dia_chuvoso_londrina"] == 0]["tem_obito"].mean() * 100.0
    l25_c = prf_25[prf_25["dia_chuvoso_londrina"] == 1]["tem_obito"].mean() * 100.0

    x2 = np.arange(2)
    b2_s = ax2.bar(x2 - w / 2, [l24_s, l25_s], width=w, color=BLUE, edgecolor=NAVY, label="Dia Seco (< 1 mm)")
    b2_c = ax2.bar(x2 + w / 2, [l24_c, l25_c], width=w, color=TEAL, edgecolor=NAVY, label="Dia Chuvoso (>= 1 mm)")

    for bars, col in [(b2_s, NAVY), (b2_c, TEAL)]:
        for bar in bars:
            val = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                val + 0.12,
                f"{val:.2f}%",
                ha="center",
                va="bottom",
                fontsize=12.5,
                fontweight="bold",
                color=col,
            )

    ax2.set_xticks(x2)
    ax2.set_xticklabels(["2022–2024\n(509 sin.)", "2022–2025\n(692 sin.)"], fontweight="bold", color=NAVY)
    ax2.set_ylabel("Letalidade Viária (%)", fontweight="bold", color=NAVY)
    ax2.set_ylim(0, 5.25)
    ax2.grid(axis="y", color=GRID_COLOR, linestyle="--", linewidth=0.9)
    ax2.set_axisbelow(True)
    ax2.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=11)
    ax2.set_title("B) Dia Instrumental (>= 1 mm)", loc="left", fontsize=14, color=NAVY, pad=10)

    plt.tight_layout(pad=1.3, w_pad=2.0)
    fig.savefig(ASSETS_DIR / "chart02_letalidade_severidade.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_chart03_espacial_semanal_horarios(daily_24: pd.DataFrame, pes_24: pd.DataFrame) -> None:
    """Gráfico 3: Sábado chuvoso vs. Sexta seca + Picos horários por modal."""
    ordem_dias = [
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo",
    ]
    labels_curtos = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    dow = (
        daily_24.groupby(["dia_semana", "dia_chuvoso_londrina"])["total_acidentes"]
        .mean()
        .unstack()
        .reindex(ordem_dias)
        * 100.0
    )

    acc_m = pes_24[pes_24["modal"].isin(["Carro", "Moto", "Caminhão"])].drop_duplicates(subset=["id", "modal"])
    h_piv = acc_m.pivot_table(index="hora", columns="modal", values="id", aggfunc="nunique", fill_value=0).reindex(range(24), fill_value=0)

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(9.0, 6.4), gridspec_kw={"height_ratios": [1.0, 1.1]})

    # Topo: Semanal Seco vs Chuvoso
    x = np.arange(len(ordem_dias))
    w = 0.36
    ax_top.bar(x - w / 2, dow[0], width=w, color=BLUE, edgecolor=NAVY, label="Dia Seco (< 1 mm)")
    ax_top.bar(x + w / 2, dow[1], width=w, color=CORAL, edgecolor=NAVY, label="Dia Chuvoso (>= 1 mm)")

    # Destacar Sexta Seca e Sábado Chuvoso bem acima das barras e longe da legenda à esquerda
    ax_top.text(4 - w / 2, dow.loc["sexta-feira", 0] + 2.0, f"{dow.loc['sexta-feira', 0]:.1f}", ha="center", va="bottom", fontsize=12.5, fontweight="bold", color=NAVY)
    ax_top.text(5 + w / 2, dow.loc["sábado", 1] + 2.0, f"{dow.loc['sábado', 1]:.1f}\n(+16,4%)", ha="center", va="bottom", fontsize=12, fontweight="bold", color=CORAL)

    ax_top.set_xticks(x)
    ax_top.set_xticklabels(labels_curtos, fontweight="bold", color=NAVY)
    ax_top.set_ylabel("Sinistros / 100 dias", fontweight="bold", color=NAVY)
    ax_top.set_ylim(0, 96)
    ax_top.grid(axis="y", color=GRID_COLOR, linestyle="--", linewidth=0.9)
    ax_top.set_axisbelow(True)
    ax_top.legend(loc="upper left", ncol=2, frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=10.5)
    ax_top.set_title("A) Taxa Semanal por Clima (2022–2024)", loc="left", fontsize=14.5, color=NAVY, pad=8)

    # Base: Assinatura Horária 00h-23h
    hrs = np.arange(24)
    ax_bot.axvspan(6.5, 8.5, color="#DBEAFE", alpha=0.65, label="Pico Manhã (07h–08h)")
    ax_bot.axvspan(16.5, 18.5, color="#FEE2E2", alpha=0.55, label="Pico Tarde (17h–18h)")

    ax_bot.plot(hrs, h_piv["Moto"], marker="o", markersize=5, linewidth=2.6, color=CORAL, label="Moto")
    ax_bot.plot(hrs, h_piv["Carro"], marker="s", markersize=5, linewidth=2.4, color=BLUE, label="Carro")
    ax_bot.plot(hrs, h_piv["Caminhão"], marker="^", markersize=6, linewidth=2.4, color=AMBER, label="Caminhão")

    ax_bot.annotate("Moto 18h (40)", xy=(18, h_piv.loc[18, "Moto"]), xytext=(18.9, 39.5),
                    fontsize=11.5, fontweight="bold", color=CORAL,
                    arrowprops=dict(arrowstyle="->", color=CORAL, lw=1.3))
    ax_bot.annotate("Carro 17h (37)", xy=(17, h_piv.loc[17, "Carro"]), xytext=(11.3, 27.5),
                    fontsize=11.5, fontweight="bold", color=BLUE,
                    arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.3))
    ax_bot.annotate("Caminhão 08h (13)", xy=(8, h_piv.loc[8, "Caminhão"]), xytext=(9.4, 21.5),
                    fontsize=11.5, fontweight="bold", color="#B45309",
                    arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.3))

    ax_bot.set_xticks(range(0, 24, 2))
    ax_bot.set_xticklabels([f"{h:02d}h" for h in range(0, 24, 2)], fontweight="bold", color=NAVY)
    ax_bot.set_ylabel("Total de Sinistros (3 anos)", fontweight="bold", color=NAVY)
    ax_bot.set_ylim(0, 54)
    ax_bot.grid(axis="y", color=GRID_COLOR, linestyle="--", linewidth=0.9)
    ax_bot.set_axisbelow(True)
    ax_bot.legend(loc="upper left", ncol=3, frameon=True, facecolor="#FFFFFF", edgecolor="#CBD5E1", fontsize=10.5)
    ax_bot.set_title("B) Perfil Horário (00h–23h) por Modal (2022–2024)", loc="left", fontsize=15, color=NAVY, pad=8)

    plt.tight_layout(pad=1.2, h_pad=1.8)
    fig.savefig(ASSETS_DIR / "chart03_espacial_semanal_horarios.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (Path(__file__).resolve().parent / "preview").mkdir(parents=True, exist_ok=True)

    daily_24 = pd.read_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2024.csv", parse_dates=["data"])
    daily_25 = pd.read_csv(PROCESSED_DIR / "base_consolidada_londrina_diaria_2022_2025.csv", parse_dates=["data"])
    prf_24 = pd.read_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2024_enriquecido.csv", parse_dates=["data"])
    prf_25 = pd.read_csv(PROCESSED_DIR / "prf_sinistros_londrina_2022_2025_enriquecido.csv", parse_dates=["data"])
    pes_24 = pd.read_csv(PROCESSED_DIR / "prf_pessoas_veiculos_londrina_2022_2024_enriquecido.csv", parse_dates=["data"])
    pes_25 = pd.read_csv(PROCESSED_DIR / "prf_pessoas_veiculos_londrina_2022_2025_enriquecido.csv", parse_dates=["data"])

    make_chart01_clima_modais(daily_24, pes_24, daily_25, pes_25)
    make_chart02_letalidade_severidade(prf_24, prf_25)
    make_chart03_espacial_semanal_horarios(daily_24, pes_24)
    print(f"Gráficos em 300 DPI gerados com sucesso em: {ASSETS_DIR}")


if __name__ == "__main__":
    main()
