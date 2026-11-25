# Lab 02: Descobrindo, Entendendo e Integrando os Dados

**Disciplina:** Ciência de Dados / Machine Learning  
**Docente:** Mário Henrique Akihiko da Costa Adaniya  
**Projeto:** Observatório de Londrina — Eixo Mobilidade  

---

## 1. Identificação do Grupo

* **Caio Gabriel Duque Cotting**
* **Victor Gomes Cardoso**

---

## 2. Síntese dos Arquivos Exemplares Entregues nesta Atividade

Seguindo a **Regra de Ouro** da disciplina (*"Nunca altere os dados brutos. Registre todas as transformações em código"* — Slide 39), organizamos na pasta `Atividade 2/` tanto os **exemplares no formato bruto nativo** de cada instituição quanto as **tabelas tratadas e consolidadas** geradas pelo pipeline reprodutível (`src/etl_pipeline.py`):

| Arquivo em `Atividade 2/` | Nível / Granularidade | Linhas | Formato e Codificação | Descrição |
| :--- | :--- | :---: | :---: | :--- |
| `base_consolidada_londrina_diaria_2022_2024.csv` | **1 linha = 1 dia civil em Londrina** (Unidade de Análise do Projeto) | 1.096 dias | CSV (`,`, `UTF-8`) | Base integrada final do recorte oficial (2022–2024), unindo contagens/severidade da PRF e variáveis meteorológicas diárias. |
| `base_consolidada_londrina_diaria_2022_2025.csv` | **1 linha = 1 dia civil em Londrina** (Série estendida c/ 2025) | 1.461 dias | CSV (`,`, `UTF-8`) | Base integrada estendida (2022–2025), utilizada para validação temporal e teste cego (*holdout*) de modelos de Machine Learning. |
| `prf_ocorrencias_londrina_2022_2024.csv` | **1 linha = 1 sinistro na PRF** em Londrina | 509 sinistros | CSV (`,`, `UTF-8`) | Microdados de ocorrências da PRF filtrados para `municipio == 'LONDRINA'` (2022–2024) e enriquecidos com o clima do dia. |
| `inmet_clima_diario_londrina_e_a835_2022_2024.csv` | **1 linha = 1 dia de medição climática** | 1.096 dias | CSV (`,`, `UTF-8`) | Série diária da Estação Oficial INMET Londrina (`83766`), Aeroporto SBLO (`83768`), Reanálise ERA5 e Estação Automática `A835`. |
| `exemplares_brutos/prf_datatran2024_londrina_bruto.csv` | **1 linha = 1 sinistro bruto** | 169 sinistros | CSV (`;`, `Latin-1`, decimal `,`) | Recorte bruto intocado do arquivo `datatran2024.csv` preservando exatamente a formatação original da PRF. |
| `exemplares_brutos/inmet_A835_2024_amostra_horaria_bruta.csv` | **1 linha = 1 hora UTC** (+ 8 linhas de metadados) | 250 linhas | CSV (`;`, `Latin-1`, decimal `,`) | Amostra bruta original extraída de `2024.zip` (`portal.inmet.gov.br/dadoshistoricos`), exibindo os metadados no cabeçalho. |
| `exemplares_brutos/inmet_83766_londrina_convencional_diario_bruto.csv` | **1 linha = 1 dia** | 1.461 dias | CSV (`,`, `UTF-8`) | Série bruta diária da Estação Meteorológica Convencional do INMET em Londrina (código OMM/INMET `83766`). |

---

## 3. Respostas às Perguntas de Reflexão do Encontro 01 (Slide 57)

| Pergunta Norteadora (Slide 57) | Fonte 1: Polícia Rodoviária Federal (PRF) | Fonte 2: Instituto Nacional de Meteorologia (INMET) |
| :--- | :--- | :--- |
| **1. Os dados de que precisamos existem?** | **Sim.** Os arquivos `datatran2022.csv` a `datatran2025.csv` estão publicamente disponíveis no Portal de Dados Abertos da PRF e contêm todos os sinistros atendidos em rodovias federais em Londrina ($509\text{ ocorrências}$ em 2022–2024; $692$ em 2022–2025). | **Sim, mas exigiram investigação técnica crucial (ver Seção 4).** Os pacotes `.zip` de estações automáticas contêm a estação regional `A835` (Maringá), enquanto a estação oficial localizada dentro de Londrina é a **Estação Convencional INMET `83766`** (complementada pela estação do Aeroporto de Londrina `83768` e série ERA5). |
| **2. Em que formato estão?** | Arquivos compactados `.zip` contendo arquivos `.csv` delimitados por ponto e vírgula (`;`), codificação `ISO-8859-1` (`Latin-1`) e separador decimal com vírgula (`,`). | Nos pacotes anuais de estações automáticas: arquivos `.csv` com **8 linhas iniciais de metadados**, delimitador `;`, codificação `Latin-1` e decimal `,`. Na série diária OMM/INMET `83766`: `.csv` delimitado por `,` em `UTF-8` e decimal `.`. |
| **3. Quem os produziu e para quê?** | **Polícia Rodoviária Federal (Ministério da Justiça e Segurança Pública)**, a partir do preenchimento do Boletim de Acidente de Trânsito (BAT) pelos agentes em campo para fins operacionais, estatísticos e legais. | **Instituto Nacional de Meteorologia (MAPA)** e rede sinótica da **Organização Meteorológica Mundial (OMM)**, para monitoramento climático, agrometeorológico e segurança aeronáutica/civil. |
| **4. Têm a mesma unidade de análise?** | **Não na origem.** Na PRF bruta, $1\text{ linha} = 1\text{ ocorrência de sinistro}$ (evento pontual no tempo e espaço). | **Não na origem.** No INMET Automático (`A835`), $1\text{ linha} = 1\text{ medição horária (UTC)}$. Na estação convencional `83766`, $1\text{ linha} = 1\text{ dia}$. Ambas são agregadas/unificadas para **$1\text{ linha} = 1\text{ dia civil em Londrina}$**. |
| **5. Cobrem o período que queremos estudar?** | **Sim.** Cobertura integral de `01/01/2022` a `31/12/2024` ($1.096\text{ dias}$, com ano bissexto em 2024), além de `2025` completo ($1.461\text{ dias}$ no total). | **Sim.** Cobertura completa de `01/01/2022` a `31/12/2024` ($1.096\text{ dias}$). Em 2025, a estação automática `A835` apresenta falha de transmissão após fevereiro, enquanto a estação Londrina `83766` / SBLO `83768` / ERA5 mantém cobertura até `31/12/2025`. |
| **6. Usam os mesmos recortes territoriais?** | Filtrado por `municipio == 'LONDRINA'` e `uf == 'PR'`. Quase a totalidade dos registros ($99{,}4\%$) ocorre no perímetro de Londrina da **BR-369** (notadamente entre o $\text{km }142$ e o $\text{km }160$). | A estação INMET `83766` (`-23,3255°, -51,1416°`) e o Aeroporto SBLO `83768` (`-23,3336°, -51,1301°`) ficam exatamente no perímetro urbano de Londrina, a menos de $5\text{ km}$ do trecho crítico da BR-369. Já a estação automática `A835` fica em Maringá ($\approx 80\text{ km}$ a oeste). |
| **7. Podemos combinar essas fontes? Por qual chave?** | **Sim.** Após agregar a base da PRF por data (`groupby('data')`) e converter o horário UTC do INMET para o fuso local (`America/Sao_Paulo`, GMT-3), realizamos um `LEFT JOIN` a partir do calendário completo de dias civis usando a chave primária padronizada `data` (`AAAA-MM-DD`). | Os dias sem ocorrências na PRF não aparecem no arquivo bruto de sinistros; ao partir do calendário contínuo de $1.096\text{ dias}$ (2022–2024) e preencher ausências da PRF com `0`, respeitamos a regra do **Slide 34** (*"Quem não aparece também conta"*). |

---

## 4. Descoberta Crítica na Exploração das Fontes ("Um Processo que Vai e Volta" — Slide 9)

No **Encontro 01 (Slide 9)**, discutimos que a Ciência de Dados é um ciclo iterativo em que a inspeção real dos dados frequentemente exige ajustar premissas iniciais. Durante a extração dos pacotes `.zip` do INMET (`2022.zip` a `2025.zip` em `portal.inmet.gov.br/dadoshistoricos`), fizemos uma descoberta técnica fundamental:

1. **O que estava previsto no Lab 01:** Utilizar a *"Estação Meteorológica Automática de Londrina (Estação A835)"* a partir dos pacotes anuais de estações automáticas do INMET.
2. **O que a inspeção dos metadados revelou:** Ao abrir os pacotes anuais `2022.zip`–`2025.zip` (que reúnem apenas as 26 **Estações Automáticas** do Paraná), verificamos as 8 linhas iniciais de metadados do arquivo `A835`:
   ```text
   REGIAO:;S
   UF:;PR
   ESTACAO:;MARINGA
   CODIGO (WMO):;A835
   LATITUDE:;-23,40527777
   LONGITUDE:;-51,93277777
   ```
   Ou seja, o código **`A835` pertence à Estação Automática de Maringá (PR)**, e a estação automática mais próxima a leste é **`A842` (Nova Fátima - PR)**. Por que Londrina não aparecia na lista de estações automáticas do arquivo `.zip`?
3. **A explicação institucional no cadastro do INMET:** Consultando a API oficial de estações do INMET (`apitempo.inmet.gov.br/estacoes/M`), constatamos que a estação meteorológica oficial do INMET sediada dentro do município de **Londrina** é uma **Estação Convencional (Tipo M)** — **Código OMM/INMET `83766` (`LONDRINA`, lat `-23,3255°`, lon `-51,1416°`, altitude $566\text{ m}$, operante desde 10/12/1953 junto ao IAPAR/IDR-Paraná)** — acompanhada pela estação meteorológica aeronáutica do **Aeroporto de Londrina (`83768` / SBLO)**.
4. **Decisão de Engenharia e Metodologia Adotada:**
   * Em vez de descartar a `A835` ou depender apenas de uma estação a $80\text{ km}$ de distância, **incorporamos ambas na base consolidada**!
   * Mantivemos as variáveis diárias agregadas da **Estação Automática `A835`** (extraídas diretamente dos `.zip` de dados históricos do INMET) **E** integramos a série diária oficial medida **dentro de Londrina** pela **Estação Convencional INMET `83766`**, complementada pela estação do **Aeroporto de Londrina (`83768`)** e pela reanálise **Open-Meteo / ERA5** para os dias em que o boletim sinótico convencional não reportou acumulado pluviométrico em 2022.
   * **Ganho analítico direto:** Isso nos permitiu inclusive medir o impacto espacial na **Pergunta Secundária 4** (Índice de Concordância): enquanto a estação local de Londrina tem **concordância de $100{,}0\%$ ($> 0\text{ mm}$) e $95{,}1\%$ ($\ge 1\text{ mm}$)** com os sinistros em que o policial da PRF anotou `"Chuva"` ou `"Garoa/Chuvisco"`, na estação `A835` (a $80\text{ km}$) essa concordância cai para **$85{,}4\%$ ($> 0\text{ mm}$) e $82{,}9\%$ ($\ge 1\text{ mm}$)** devido a chuvas convectivas localizadas!

---

## 5. Avaliação das 6 Dimensões da Qualidade dos Dados (Slide 38)

Aplicamos o framework de qualidade de dados apresentado no **Slide 38** sobre as bases brutas da PRF (`datatran2022..2025.csv`) e do INMET (`A835`, `A842`, `83766` Londrina):

| Dimensão (Slide 38) | Problemas Reais Encontrados nas Bases Brutas | Tratamento Aplicado em Código (`src/etl_pipeline.py`) |
| :--- | :--- | :--- |
| **1. Completude**<br>*(Há valores faltantes?)* | • **PRF:** $0\%$ de nulos nos campos de data, vítimas e condição meteorológica em Londrina.<br>• **INMET `A842` (Nova Fátima):** Grave incompletude ($48{,}6\%$ de horas vazias em 2022, $90{,}8\%$ em 2023 e $100\%$ em 2025) — descartada como fonte principal.<br>• **INMET `A835` (Maringá):** Excelente completude em 2022–2024 ($98{,}0\%$ das horas válidas; apenas 9 dias com $< 12\text{h}$ medidas em 3 anos), mas em 2025 interrompeu registros após fevereiro ($11{,}0\%$ do ano).<br>• **INMET `83766` (Londrina):** $100\%$ completa para temperatura nos 4 anos ($1.461/1.461\text{ dias}$); precipitação $100\%$ em 2023, $96{,}4\%$ em 2024, $95{,}6\%$ em 2025 e $60{,}0\%$ em 2022. | Exigência mínima de $12\text{ horas}$ válidas no dia (`min_count=12`) para agregação diária da `A835`; preenchimento hierárquico documentado na série de Londrina (`INMET_83766` $\rightarrow$ `SBLO_83768` $\rightarrow$ `ERA5_LONDRINA`) com coluna rastreadora `fonte_precip_londrina` (Slide 37: *"Registre qual versão usou e de onde ela veio"*). |
| **2. Validade**<br>*(Respeita formato e domínio?)* | • **PRF:** Identificados **4 registros em Londrina com `br = 0` e `km = 0`** (1 em 2022 e 3 em 2025), embora as coordenadas geográficas (`latitude`/`longitude`) confirmem que ocorreram em alças/acessos da BR-369 em Londrina.<br>• **INMET:** Uso de valores sentinela `-9999` para representar falha de sensor. | Preservação dos registros no total municipal da PRF, criação de indicador específico `acidentes_br369` e conversão explícita de `-9999` e valores negativos espúrios de precipitação/umidade para `NaN` antes de qualquer cálculo de média ou soma. |
| **3. Consistência**<br>*(Mesmo fato, mesma forma?)* | • **Separador decimal e de colunas (Slide 36):** PRF e INMET Automático usam `;` como separador de colunas e vírgula (`,`) como decimal (`-23,3103`), enquanto `83766` e bibliotecas Python usam ponto (`.`).<br>• **Datas e Fusos:** PRF usa `AAAA-MM-DD` em horário local (`GMT-3`); INMET Automático usa `AAAA/MM/DD` e `Hora UTC` (`0000 UTC` a `2300 UTC`). | Padronização de todos os arquivos processados para `UTF-8`, separador `,`, ponto decimal `.`, datas em `ISO-8601` (`AAAA-MM-DD`) e conversão prévia dos registros horários do INMET de `UTC` para `America/Sao_Paulo (GMT-3)` antes de agrupar por dia. |
| **4. Unicidade**<br>*(Há duplicatas?)* | • Verificação da chave `id` nos microdados da PRF ($509\text{ ocorrências}$ em 2022–2024; $692$ em 2022–2025) e da chave `data` na base diária consolidada ($1.096\text{ dias}$ em 2022–2024; $1.461\text{ dias}$ em 2022–2025). | Confirmado **$0\%$ de duplicatas** tanto nas ocorrências individuais (`id` único por boletim) quanto na série diária (`1 linha = 1 data única`). |
| **5. Atualidade**<br>*(É recente o suficiente?)* | • Os dados cobrem integralmente o triênio planejado no Project Canvas (**2022 a 2024**) e já contam com a extensão de **2025** disponibilizada pela PRF. | Mantivemos duas versões da base consolidada: `2022_2024` (fiel ao recorte do Lab 01) e `2022_2025` (permitindo usar 2025 como conjunto de teste temporal em Machine Learning). |
| **6. Acurácia**<br>*(Corresponde à realidade?)* | • A variável `condicao_metereologica` da PRF depende da percepção subjetiva do agente em campo (`"Céu Claro"`, `"Sol"`, `"Nublado"`, `"Chuva"`, `"Garoa/Chuvisco"`). Além disso, `"Céu Claro"` e `"Sol"` coexistem como categorias distintas para tempo aberto diurno. | Cruzamento instrumental na Pergunta Secundária 4 comprovou altíssima acurácia quando o agente reporta chuva ($100\%$ dos casos ocorreram em dias com precipitação registrada em Londrina) e justificou unificar `"Chuva"` + `"Garoa/Chuvisco"` na flag analítica `condicao_chuva_prf`. |

---

## 6. Dicionário de Dados e Tipologia de Variáveis (Slide 32 — *Tidy Data*)

Na tabela consolidada (`base_consolidada_londrina_diaria_2022_2024.csv`), cada linha é uma observação (**1 dia civil em Londrina**) e cada coluna é uma variável classificada conforme o **Slide 32**:

| Variável na Base Consolidada | Origem | Tipo Estatístico (Slide 32) | Unidade / Domínio | Descrição |
| :--- | :---: | :--- | :---: | :--- |
| `data` | Chave (`JOIN`) | Qualitativa Ordinal (Temporal) | `AAAA-MM-DD` | Data civil no fuso de Londrina (`America/Sao_Paulo`). |
| `ano`, `mes`, `dia_semana` | Derivada | Qualitativa Nominal / Ordinal | Categorias | Atributos de calendário e sazonalidade semanal. |
| `fim_de_semana` | Derivada | Qualitativa Nominal (Binária) | `0` ou `1` | `1` para sábado ou domingo; `0` para segunda a sexta-feira. |
| `total_acidentes` | PRF | **Quantitativa Discreta** | Contagem ($\ge 0$) | Total de sinistros registrados pela PRF em Londrina no dia. |
| `acidentes_br369` | PRF | **Quantitativa Discreta** | Contagem ($\ge 0$) | Total de sinistros registrados especificamente na rodovia BR-369. |
| `acidentes_com_vitimas` | PRF | **Quantitativa Discreta** | Contagem ($\ge 0$) | Sinistros no dia que tiveram ao menos 1 ferido (leve/grave) ou morto. |
| `acidentes_graves_ou_fatais` | PRF | **Quantitativa Discreta** | Contagem ($\ge 0$) | Sinistros no dia com pelo menos 1 ferido grave ou vítima fatal. |
| `acidentes_fatais` | PRF | **Quantitativa Discreta** | Contagem ($\ge 0$) | Sinistros no dia com registro de óbito (`mortos > 0`). |
| `total_mortos`, `total_feridos_graves`, `total_feridos_leves` | PRF | **Quantitativa Discreta** | Pessoas ($\ge 0$) | Somatório diário de vítimas fatais, feridos graves e feridos leves. |
| `acidentes_chuva_prf` | PRF | **Quantitativa Discreta** | Contagem ($\ge 0$) | Sinistros no dia cujo boletim da PRF registrou `"Chuva"` ou `"Garoa/Chuvisco"`. |
| `temp_media_c`, `temp_min_c`, `temp_max_c` | INMET `83766` | **Quantitativa Contínua** | Graus Celsius ($^\circ\text{C}$) | Temperatura diária média, mínima e máxima registrada em Londrina. |
| `amplitude_termica_c` | INMET `83766` | **Quantitativa Contínua** | Graus Celsius ($^\circ\text{C}$) | Diferença diária entre temperatura máxima e mínima (`temp_max_c - temp_min_c`). |
| `precip_londrina_mm` | INMET `83766` / SBLO / ERA5 | **Quantitativa Contínua** | Milímetros ($\text{mm}$) | Precipitação pluviométrica acumulada nas 24 horas do dia em Londrina. |
| `a835_precip_mm`, `a835_temp_media_c` | INMET `A835` | **Quantitativa Contínua** | $\text{mm}$ / $^\circ\text{C}$ | Precipitação acumulada e temperatura média diária na Estação Automática `A835`. |
| `dia_chuvoso_londrina` | Indicador (Canvas) | Qualitativa Nominal (Binária) | `0` ($<1\text{ mm}$) ou `1` ($\ge 1\text{ mm}$) | Classificação diária segundo o critério do Project Canvas ($\ge 1{,}0\text{ mm}$). |
| `faixa_precipitacao` | Indicador | **Qualitativa Ordinal** | 4 faixas ordenadas | `Seco (<1 mm)`, `Chuva Leve (1-10 mm)`, `Chuva Moderada (10-30 mm)`, `Chuva Forte (>30 mm)`. |
| `faixa_temperatura_media` | Indicador (Canvas) | **Qualitativa Ordinal** | 3 faixas ordenadas | `Frio (<= 19°C)`, `Ameno (19-24°C)`, `Quente (> 24°C)`. |
| `taxa_severidade_vitimas_pct` | Indicador Relativo | **Quantitativa Contínua** | Percentual ($0\text{--}100\%$) | Proporção de sinistros com vítimas no dia (`NaN` em dias sem acidentes). |
| `taxa_letalidade_pct` | Indicador Relativo | **Quantitativa Contínua** | Percentual ($0\text{--}100\%$) | Proporção de sinistros com óbito no dia (`NaN` em dias sem acidentes). |

---

## 7. Resultados Analíticos Preliminares (Respondendo às Perguntas do Project Canvas — 2022 a 2024)

No período de **01/01/2022 a 31/12/2024 ($1.096\text{ dias}$)**, foram registrados **$509\text{ sinistros}$** nas rodovias federais em Londrina (média geral de **$0{,}464\text{ acidentes/dia}$**), distribuídos em $420\text{ dias}$ com ocorrências ($38{,}3\%$) e $676\text{ dias}$ sem sinistros ($61{,}7\%$), resultando em **$541\text{ feridos}$** ($398$ leves e $143$ graves) e **$15\text{ mortos}$**.

### 7.1. Pergunta Secundária 1: Média diária de acidentes em dias chuvosos vs. dias secos

| Cenário Diário (2022–2024) | Total de Dias | Total de Acidentes | Média Diária ($\text{acidentes/dia}$) | Desvio-Padrão | % de Dias com $\ge 1$ Acidente | Teste Estatístico (Chuvoso vs. Seco) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dias Secos ($< 1\text{ mm}$ em Londrina)** | $680$ ($62{,}0\%$) | $330$ | **$0{,}485$** | $0{,}693$ | $39{,}0\%$ | Welch $t$: $p = 0{,}1675$ |
| **Dias Chuvosos ($\ge 1\text{ mm}$ em Londrina)** | $416$ ($38{,}0\%$) | $179$ | **$0{,}430$** | $0{,}605$ | $37{,}3\%$ | Mann-Whitney: $p = 0{,}4043$ |
| *— Chuva Leve ($1\text{ a }10\text{ mm}$)* | $257$ | $111$ | $0{,}432$ | $0{,}616$ | $37{,}0\%$ | — |
| *— Chuva Moderada ($10\text{ a }30\text{ mm}$)* | $144$ | $62$ | $0{,}431$ | $0{,}587$ | $38{,}2\%$ | — |
| *— Chuva Forte ($> 30\text{ mm}$)* | $15$ | $6$ | $0{,}400$ | $0{,}632$ | $33{,}3\%$ | — |

* **Interpretação Crítica:** Ao contrário do senso comum inicial, a média bruta do dia inteiro em dias chuvosos ($0{,}430/\text{dia}$) **não supera** a média dos dias secos ($0{,}485/\text{dia}$, diferença de $-11{,}3\%$ sem significância estatística ao nível de $5\%$). Isso se explica por dois fatores fundamentais do domínio viário urbano da BR-369 em Londrina:
  1. **Efeito de exposição (VMD de vulneráveis):** Grande parte dos sinistros na travessia urbana da BR-369 envolve motociclistas e pedestres, cujo fluxo reduz drasticamente em dias de chuva contínua. No entanto, **aos sábados**, a média em dias chuvosos (**$0{,}55\text{ acidentes/dia}$**) supera a de sábados secos (**$0{,}47\text{ acidentes/dia}$**).
  2. **Duração da chuva dentro das 24 horas:** Dos $179\text{ acidentes}$ ocorridos em dias com acumulado $\ge 1\text{ mm}$, apenas **$21{,}8\%$ ($39\text{ sinistros}$)** aconteceram no exato momento em que chovia ou garoava; os outros $78{,}2\%$ ocorreram em horas de céu aberto/nublado do mesmo dia civil.

### 7.2. Pergunta Secundária 2: Comportamento nas faixas de temperatura

| Faixa de Temperatura Média Diária (Londrina, 2022–2024) | Total de Dias | Total de Acidentes | Média Diária ($\text{acidentes/dia}$) | % de Dias com $\ge 1$ Acidente |
| :--- | :---: | :---: | :---: | :---: |
| **Dias Frios ($\le 19{,}0^\circ\text{C}$)** | $201$ | $106$ | **$0{,}527$** | **$40{,}8\%$** |
| **Dias Amenos ($19{,}0^\circ\text{C}\text{ a }24{,}0^\circ\text{C}$)** | $497$ | $226$ | **$0{,}455$** | $37{,}8\%$ |
| **Dias Quentes ($> 24{,}0^\circ\text{C}$)** | $398$ | $177$ | **$0{,}445$** | $37{,}7\%$ |

* **Interpretação:** Os dias frios ($\le 19^\circ\text{C}$, típicos do outono/inverno seco com menor luminosidade ao amanhecer/anoitecer e maior amplitude térmica) apresentam a maior média diária de sinistros (**$0{,}527\text{ acidentes/dia}$**, $+18{,}5\%$ acima dos dias quentes).

### 7.3. Pergunta Secundária 3: Severidade e Letalidade (Teste da Hipótese do Grupo)

| Recorte de Condição Meteorológica (2022–2024) | Ocorrências ($n$) | Taxa com Vítimas ($\%$) | Taxa com Feridos Graves ou Óbito ($\%$) | Vítimas Fatais (Óbitos) | Taxa de Letalidade Viária ($\%$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Pelo Boletim da PRF (Momento exato do sinistro):** | | | | | |
| • Sem Chuva (`Céu Claro` / `Sol` / `Nublado` / `Vento`) | $468$ | $83{,}1\%$ | $25{,}2\%$ | $15$ | **$3{,}21\%$** |
| • Com Chuva (`Chuva` / `Garoa/Chuvisco`) | $41$ | $82{,}9\%$ | $31{,}7\%$ | **$0$** | **$0{,}00\%$** |
| **2. Pela Medição Instrumental Diária em Londrina:** | | | | | |
| • Dia Seco ($< 1{,}0\text{ mm}$) | $330$ | $84{,}5\%$ | $26{,}4\%$ | $12$ | **$3{,}64\%$** |
| • Dia Chuvoso ($\ge 1{,}0\text{ mm}$) | $179$ | $80{,}4\%$ | $24{,}6\%$ | $3$ | **$1{,}68\%$** |

* **Veredito sobre a Hipótese do Lab 01:** A hipótese do grupo previa que *"dias com registro de precipitação apresentam proporção similar ou inferior de vítimas fatais devido à redução preventiva da velocidade média adotada pelos condutores sob pista molhada"*. **Essa hipótese sobre a letalidade se confirmou de forma contundente:**
  * Nos **41 sinistros ocorridos sob chuva/garoa** entre 2022 e 2024, houve **zero óbitos ($0{,}00\%$ de letalidade)**, contra **$3{,}21\%$** nos sinistros sem chuva ($15\text{ óbitos}$)! Mesmo expandindo para os 4 anos (2022–2025, $n = 692$), a letalidade sob chuva na PRF foi de apenas **$1{,}82\%$ ($1/55$)** contra **$2{,}67\%$ ($17/637$)** sem chuva.
  * No agregado diário instrumental ($\ge 1\text{ mm}$), a taxa de letalidade nos dias chuvosos (**$1{,}68\%$**) é **menos da metade** da registrada nos dias secos (**$3{,}64\%$**).

### 7.4. Pergunta Secundária 4: Índice de Concordância entre Boletim da PRF e Estação Meteorológica

* Dos **$41\text{ sinistros}$** (2022–2024) em que o agente da PRF preencheu `condicao_metereologica` como `"Chuva"` ($22$) ou `"Garoa/Chuvisco"` ($19$):
  * **$100{,}0\%$ ($41/41$)** ocorreram em dias com precipitação instrumental registrada ($> 0\text{ mm}$) em Londrina!
  * **$95{,}1\%$ ($39/41$)** ocorreram em dias classificados como chuvosos pelo limiar de $\ge 1{,}0\text{ mm}$ em Londrina (os 2 casos restantes tiveram registro de `"Chuva"` na PRF em dias com precipitação instrumental de $0{,}5\text{ mm}$ e $0{,}6\text{ mm}$ no INMET `83766`).
  * Quando comparados à Estação Automática `A835` (Maringá), a concordância cai para **$85{,}4\%$ ($> 0\text{ mm}$) e $82{,}9\%$ ($\ge 1{,}0\text{ mm}$)**, evidenciando a variabilidade espacial da chuva no Norte do Paraná.

---

## 8. Visualizações Geradas

As figuras abaixo foram geradas automaticamente pelo script `src/analise_exploratoria_e_ml.py` e salvas em `Atividade 2/figuras/`:

1. **`figuras/fig01_painel_perguntas_project_canvas.png`**: Painel completo respondendo visualmente às 4 Perguntas Secundárias do Project Canvas com títulos-mensagem (Knaflic, *Storytelling with Data* — Slide 48).
2. **`figuras/fig02_sazonalidade_semanal_e_km_br369.png`**: Comparação por dia da semana (evidenciando o pico às sextas-feiras secas e a alta nos sábados chuvosos) e distribuição espacial por quilômetro da BR-369 (evidenciando a concentração crítica no trecho urbano de Londrina entre o $\text{km }145$ e o $\text{km }159{,}3$).
3. **`figuras/fig03_clusters_pca_clima_sinistros.png`**: Projeção em 2 componentes principais (PCA, $65{,}5\%$ da variância explicada) da clusterização K-Means ($k = 3$, *Silhouette Score* $= 0{,}4040$), identificando três regimes diários distintos em Londrina.

