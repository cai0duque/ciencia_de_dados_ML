# Observatório de Londrina — Clima e Sinistros Rodoviários (PRF + INMET)

**Disciplina:** Ciência de Dados / Machine Learning  
**Docente:** Prof. Mário Henrique Akihiko da Costa Adaniya  
**Autores (Dupla):**
* **Caio Gabriel Duque Cotting**
* **Victor Gomes Cardoso**

---

## 1. Sobre o Projeto

Este repositório investiga de que forma as oscilações meteorológicas diárias (precipitação pluviométrica e temperatura) se relacionam com a **frequência diária** e a **gravidade/letalidade** dos sinistros de trânsito registrados nas rodovias federais que cortam o município de **Londrina-PR** (notadamente a **BR-369**), adotando uma unidade de análise atômica diária (**$1\text{ linha} = 1\text{ dia civil em Londrina}$**) entre **2022 e 2024** (com extensão de validação e teste em **2025**).

---

## 2. Estrutura do Repositório

```text
ciencia_de_dados_ML/
├── Atividade 1/
│   └── lab_01_defini_o_do_tema_e_poss_veis_fontes (1).md     # Definição do tema, Project Canvas e checklist (Lab 01)
├── Atividade 2/
│   ├── lab_02_descoberta_e_entendimento_dos_dados.md         # Relatório completo da Atividade 2 (qualidade, dicionário, EDA)
│   ├── base_consolidada_londrina_diaria_2022_2024.csv        # CSV Exemplar Integrado (1.096 dias: PRF + INMET, 2022-2024)
│   ├── base_consolidada_londrina_diaria_2022_2025.csv        # CSV Integrado Estendido (1.461 dias: 2022-2025)
│   ├── prf_ocorrencias_londrina_2022_2024.csv                # CSV Exemplar PRF (509 ocorrências em Londrina, 2022-2024)
│   ├── inmet_clima_diario_londrina_e_a835_2022_2024.csv      # CSV Exemplar INMET (clima diário Londrina 83766 + A835)
│   ├── exemplares_brutos/                                    # Amostras intocadas no formato bruto original (; / Latin-1)
│   └── figuras/                                              # Gráficos analíticos de alta resolução das Perguntas 1 a 4
├── data/
│   ├── raw/
│   │   ├── prf/                                              # Microdados anuais brutos da PRF (datatran2022..2025.csv)
│   │   ├── inmet/                                            # Estações Automáticas brutas extraídas dos ZIPs (A835, A842)
│   │   └── inmet_londrina_complementar/                      # Estação INMET Convencional Londrina (83766), SBLO (83768) e ERA5
│   └── processed/                                            # Bases limpas, enriquecidas e consolidadas prontas para análise
├── notebooks/
│   └── 01_eda_integracao_e_ml_londrina.ipynb                 # Notebook interativo completo (EDA, Testes Estatísticos e ML)
├── reports/
│   └── figures/                                              # Painéis visuais gerados pelos scripts analíticos
├── src/
│   ├── download_dados_brutos.py                              # Script reprodutível de download e extração das fontes oficiais
│   ├── etl_pipeline.py                                       # Pipeline de limpeza, padronização e integração (PRF + INMET)
│   └── analise_exploratoria_e_ml.py                          # Análises estatísticas, gráficos e experimentos de Machine Learning
├── requirements.txt                                          # Dependências do ambiente virtual Python
└── .gitignore
```

---

## 3. Como Reproduzir o Ambiente (Para Caio e Victor)

1. **Criar e ativar o ambiente virtual Python (`.venv`):**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
2. **Executar o pipeline de ETL (gera todas as bases em `data/processed/` e `Atividade 2/`):**
   ```bash
   .venv/bin/python src/etl_pipeline.py
   ```
3. **Executar a Análise Exploratória, Testes Estatísticos e Modelos de Machine Learning:**
   ```bash
   .venv/bin/python src/analise_exploratoria_e_ml.py
   ```
4. **Abrir o Jupyter Notebook interativo:**
   ```bash
   .venv/bin/jupyter notebook notebooks/01_eda_integracao_e_ml_londrina.ipynb
   ```

