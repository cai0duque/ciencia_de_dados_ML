# Lab 01: Definição do Tema e Possíveis Fontes

**Disciplina:** Ciência de Dados  
**Docente:** Mário Henrique Akihiko da Costa Adaniya  
**Projeto:** Observatório de Londrina  

---

## 1. Identificação do Grupo

* **Caio Gabriel Duque Cotting**
* **Victor Gomes Cardoso**

---

## 2. Eixo Temático e Contextualização

* **Eixo Escolhido:** Mobilidade
* **Recorte Territorial:** Trechos de rodovias federais que cortam o município de Londrina (notadamente a BR-369).
* **Tema Delimitado:** Relação entre condições meteorológicas diárias (temperatura e precipitação) e a ocorrência/severidade de sinistros de trânsito em rodovias federais em Londrina.
* **Justificativa da Abordagem Atômica:** Em vez de trabalhar com consolidados anuais agregados, o projeto adota uma abordagem temporal atômica: a análise por data (granularidade diária). A base aberta da Polícia Rodoviária Federal (PRF) disponibiliza microdados de cada ocorrência individual com marcação temporal exata (`data_inversa`), o que viabiliza a integração direta com as medições diárias da estação meteorológica de Londrina, permitindo testar hipóteses sobre o impacto imediato do tempo adverso na segurança viária.

---

## 3. Project Canvas da Equipe

| Campo | Especificação do Projeto |
| :--- | :--- |
| **Eixo** | Mobilidade |
| **Problema a investigar** | Desconhece-se de que forma e em que magnitude as oscilações meteorológicas diárias (dias chuvosos vs. secos e variações de temperatura) estão associadas à frequência diária e à gravidade dos sinistros de trânsito nas rodovias federais no perímetro de Londrina. |
| **Pergunta Principal** | Como a frequência diária e a gravidade dos sinistros de trânsito nas rodovias federais que cortam o município de Londrina variam segundo as condições meteorológicas diárias registradas entre 2022 e 2024? |
| **Perguntas Secundárias** | **1.** Qual é a média diária de acidentes em dias chuvosos em comparação com dias secos?<br>**2.** Como a frequência média de acidentes se comporta nas diferentes faixas de temperatura (dias frios, amenos e de calor extremo)?<br>**3.** A proporção de acidentes com feridos graves ou óbitos é maior em dias com pista molhada/chuva do que em dias secos?<br>**4.** Há consistência entre a variável descritiva `condicao_metereologica` preenchida no boletim da PRF e os registros pluviométricos instrumentais da estação meteorológica? |
| **Hipótese (opcional)** | Dias com registro de precipitação pluviométrica apresentam uma média diária maior de colisões em relação a dias secos, porém com proporção similar ou inferior de vítimas fatais devido à redução preventiva da velocidade média adotada pelos condutores sob pista molhada. |
| **Unidade de Análise** | **O dia civil** ($1\text{ linha} = 1\text{ data em Londrina}$). As ocorrências da PRF e as medições horárias do INMET serão agregadas e unificadas no nível diário. |
| **Dados Necessários** | • Registros individuais de sinistros (data, rodovia, km, causa presumível, total de veículos, feridos, mortos, condição meteorológica descrita).<br>• Dados climáticos diários instrumentais (temperatura média, máxima, mínima e precipitação acumulada diária em milímetros). |
| **Fontes de Dados** | **1. Polícia Rodoviária Federal (PRF) – Portal de Dados Abertos:** Microdados anuais de acidentes agrupados por ocorrência (filtrados para `municipio == 'LONDRINA'`).<br>**2. Instituto Nacional de Meteorologia (INMET) – BDMEP:** Série histórica diária da Estação Meteorológica Automática de Londrina (Estação A835). |
| **Indicadores** | • **Média diária de acidentes:** total de acidentes do período dividido pelo total de dias observados (calculado separadamente para dias com chuva $\ge 1\text{ mm}$ e dias secos $< 1\text{ mm}$).<br>• **Taxa de severidade:** percentual de sinistros com vítimas (leves, graves ou óbitos) em relação ao total de sinistros no dia ($\%$ de acidentes com vítimas).<br>• **Taxa de letalidade viária:** percentual de acidentes com óbito registrado no dia.<br>• **Índice de concordância:** percentual de acidentes classificados com "Chuva" na PRF que de fato coincidiram com precipitação registrada no INMET. |
| **Limitações Previstas** | • **Ausência de dado de volume de tráfego:** A base da PRF não registra o fluxo diário de veículos (VMD - Volume Médio Diário). Feriados e fins de semana podem ter mais acidentes pelo simples aumento no número de veículos circulando, e não necessariamente pelo clima.<br>• **Correlação não é causalidade:** O clima adverso é um fator contribuinte, mas não necessariamente a causa isolada do sinistro.<br>• **Recorte geográfico restrito:** A análise cobre apenas rodovias federais delegadas à PRF no município (ex.: BR-369), não refletindo o comportamento do trânsito na malha urbana municipal (gerida pela CMTU) ou nas rodovias estaduais (geridas pelo BPRv/PMPR). |
| **Público Beneficiado** | Inspetoria da PRF em Londrina (planejamento de patrulhamento preventivo em dias com alerta meteorológico), Defesa Civil, equipes de emergência (SIATE/SAMU) e motoristas que trafegam pelo trecho urbano da rodovia. |

---

## 4. Estratégia de Integração e Engenharia dos Dados

Para viabilizar a análise em nível atômico diário, o fluxo de pré-processamento seguirá o seguinte pipeline:

```
[Base PRF (Ocorrências individuais)] ──> Filtrar Município == 'LONDRINA'
                                     ──> Agrupar por data (COUNT de acidentes, SUM de feridos/mortos)
                                                                │
                                                                ├──> MERGE / JOIN (Chave: 'data') ──> [Tabela Consolidada]
                                                                │                                     (1 linha = 1 dia)
[Base INMET (Medições diárias)]      ──> Tratar 'NULL', datas   │
                                     ──> Variáveis: Temp / Chuva
```

1. **Base PRF (1 linha = 1 ocorrência):**
   * Filtrar apenas as linhas onde `municipio == 'LONDRINA'`.
   * Realizar agregação temporal (`groupby('data')`) contabilizando a quantidade total de ocorrências no dia e acumulando o número de feridos e mortos.
2. **Base INMET (1 linha = 1 dia):**
   * Extrair os dados da estação de Londrina (`A835`).
   * Padronizar o formato da data no padrão ISO-8601 (`AAAA-MM-DD`).
   * Tratar caracteres especiais, separadores decimais (vírgula para ponto) e valores ausentes.
3. **Integração:**
   * Junção tabular via `LEFT JOIN` ou `MERGE` utilizando o campo `data` como chave primária. Dias sem acidentes registrados na PRF serão preenchidos com contagem zero (evitando o viés de descartar dias seguros).

---

## 5. Checklist de Verificação Metodológica

- [x] **A pergunta está delimitada (o quê, onde, quando, quem)?**  
  *Sim:* O quê (frequência e gravidade dos acidentes segundo temperatura e chuva), Onde (rodovias federais em Londrina), Quando (2022 a 2024), Quem (usuários e condutores envolvidos em ocorrências na rodovia).
- [x] **A pergunta é aberta?**  
  *Sim:* Investiga *como* variam a frequência e a severidade, sem prejulgar ou induzir uma resposta categórica prévia.
- [x] **Cada pergunta secundária tem pelo menos um indicador associado?**  
  *Sim:* Todas as quatro perguntas secundárias contam com métricas quantitativas definidas (médias diárias, taxas percentuais de severidade e índice de concordância).
- [x] **Conseguimos imaginar os dados que responderiam a cada pergunta?**  
  *Sim:* Coluna de data, contagem de acidentes, número de feridos/mortos da PRF e colunas numéricas de temperatura (°C) e precipitação (mm) do INMET.
- [x] **Os indicadores comparam cenários de forma justa?**  
  *Sim:* Utiliza indicadores relativos (médias diárias padronizadas e proporções de vítimas sobre o total) em vez de simples contagens brutas isoladas.
- [x] **Indicamos pelo menos duas fontes diferentes?**  
  *Sim:* Polícia Rodoviária Federal (dados abertos federais de segurança viária) e INMET (dados meteorológicos de estação oficial).
- [x] **Sabemos o que representa uma linha em cada base?**  
  *Sim:* Na PRF bruta, 1 linha = 1 ocorrência de sinistro; no INMET, 1 linha = 1 dia de medição climática; na base integrada final, 1 linha = 1 dia civil em Londrina.
- [x] **Registramos as limitações da análise?**  
  *Sim:* Foram explicitadas a ausência do volume total de tráfego (VMD), o risco de inferência causal indevida e o recorte restrito ao perímetro federal rodoviário.