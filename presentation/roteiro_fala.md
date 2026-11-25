# Roteiro de Fala — Apresentação Final (6 a 8 minutos)

**Tema:** *Chuva Reduz a Letalidade, mas Eleva o Risco para Caminhões na BR-369*  
**Duração Alvo:** ~7 min (`07:00`) · **Dupla:** Caio Gabriel Duque Cotting & Victor Gomes Cardoso

> **Dica de entrega:** Use os tópicos abaixo como guia natural de conversa — não leia literalmente. Os **títulos dos slides já trazem a conclusão**; seu papel na fala é explicar o *porquê* e apontar o olho da banca para o número-chave na tela.

---

## Divisão Sugerida & Tempos

| Slide | Tema / Foco | Falante Sugerido | Tempo | Acumulado |
| :---: | :--- | :---: | :---: | :---: |
| **1** | Capa e gancho do problema | Caio | `0:30` | `0:30` |
| **2** | Fontes, descoberta crítica (`83766` vs `A835`) e qualidade | Caio | `1:10` | `1:40` |
| **3** | Paradoxo da chuva, janela horária e caminhões (`+17,7%`) | Caio | `1:15` | `2:55` |
| **4** | Severidade e confirmação da hipótese na letalidade (`0,00%`) | Victor | `1:00` | `3:55` |
| **5** | Corredor `km 145–159,3`, sábado chuvoso, horários e gênero | Victor | `1:15` | `5:10` |
| **6** | Machine Learning (`LogReg L2` + `K-Means k=3`) | Victor | `1:05` | `6:15` |
| **7** | Recomendações operacionais e limitações honestas | Caio + Victor | `0:45` | **`7:00`** |

---

## Guia por Slide (Tópicos Naturais)

### Slide 1 — Capa (`0:30` · Caio)
* **Abertura:** Cumprimentar o professor e a turma; apresentar o eixo do **Observatório de Londrina (Mobilidade)**.
* **Gancho:** *"Todo mundo acha que dia de chuva tem mais acidente e mais morte na BR-369. Cruzando 4 anos de dados reais da PRF com estações meteorológicas em Londrina, descobrimos um quadro bem diferente — e uma exceção crítica nos caminhões."*

### Slide 2 — Estação Local (`83766`) vs `A835` (`1:10` · Caio)
* **Escopo:** Explicar a unidade atômica (**1 linha = 1 dia civil**): `1.096` dias no triênio oficial `2022–2024` (`509` sinistros, `99,4%` na BR-369, `1.265` envolvidos), estendido para `1.461` dias (`692` sinistros) até `2025` para teste cego de ML.
* **Descoberta de engenharia:** Ao abrir os `.zip` do INMET, vimos que a `A835` ficava em **Maringá** (`80 km` a oeste) e parava em fev/2025. Buscamos a estação oficial de Londrina (**Convencional `83766`** + `SBLO 83768` + `ERA5`), fazendo a concordância com a PRF saltar de **`82,9%` para `95,1%`** (`100%` com chuva `> 0 mm`).
* **Qualidade:** Destacar que preservamos os **`676` dias sem acidentes** (*"quem não aparece também conta"*) e limpamos sentinelas (`-9999`, `idade = 0`, fuso `UTC → GMT-3`).

### Slide 3 — Dias Secos/Frios vs Caminhões na Chuva (`1:15` · Caio)
* **O paradoxo aparente:** Na média de 24h, dias chuvosos têm *menos* acidentes (`0,430` vs `0,485/dia`, `p = 0,1675`).
* **Explicação real:** Primeiro, **só chove em `6,93%` das horas** (`1.786` de `25.767 h`); segundo, motos (`-19,5%`), pedestres (`-25,1%`) e ônibus (`-40,6%`) reduzem exposição na chuva.
* **Exceção crítica:** **Caminhões não param** — único modal que sobe na chuva (**`+17,7%`** em 2022–24; **`+26,9%`** até 2025).
* **Temperatura:** Dias frios (`≤ 19°C`) lideram com **`0,527 acid/dia`**. *(Passa a palavra para o Victor).*

### Slide 4 — Zero Óbitos sob Chuva na PRF (`1:00` · Victor)
* **Teste da hipótese:** Nossa hipótese no Lab 01 previa que pista molhada reduziria velocidade e manteria ou reduziria a letalidade.
* **Evidência:** Nos **`41` sinistros sob chuva/garoa** reportados pela PRF (2022–24), houve **zero óbitos (`0,00%`)** contra **`3,21%`** (`15` óbitos) em tempo seco/nublado — mesmo com lesões graves em `31,7%`.
* **No dia instrumental (`≥ 1 mm`):** A letalidade cai pela metade nos dois recortes (`1,68%` vs `3,64%` em 2022–24; `1,63%` vs `3,14%` em 2022–25).

### Slide 5 — Corredor `km 145–159,3`, Sábados, Horários e Gênero (`1:15` · Victor)
* **Onde:** **`89,1%`** dos sinistros da BR-369 acontecem no trecho urbano entre o **`km 145` e o `km 159,3`** (`34,6%` são colisões traseiras).
* **Quando:** Sexta seca é o pico semanal (`69,1/100d`), mas **sábado** é o único dia em que chover piora a taxa (**`54,9` vs `47,2/100d`**, `+16,4%`; `+31,7%` até 2025). No relógio, moto/carro disparam às **`07h–08h` e `17h–18h`**, enquanto **caminhões têm pico às `08h`**.
* **Quem (Gênero):** Homens são **`84,5%`** dos condutores (`98,9%` em caminhões); mulheres são **`60,1%`** dos passageiros e recuam mais na chuva (`-20,9%` vs `-15,0%`).

### Slide 6 — Machine Learning & Clusterização (`1:05` · Victor)
* **Rigor sem vazamento:** Divisão cronológica estrita (`Treino 2022–23`, `Val 2024`, `Teste cego 2025`) antes do pré-processamento.
* **Supervisionado (`tem_grave_ou_morte`):** **Regressão Logística L2** superou Random Forest e Gradient Boosting e generalizou melhor em 2025 (`ROC-AUC 0,584`, `PR-AUC 0,357`, `F1 0,448`). Honestidade: prever *se* o dia vai ter acidente só com clima/calendário fica perto do acaso (`ROC ≈ 0,49`).
* **Não supervisionado (`K-Means k = 3`):** *Silhouette* `0,4040` (PCA `65,5%`), isolando **`119` dias críticos** (tempo aberto/chuva esparsa com `1,42 acid/d` e `1,02 graves/d`) de `772` dias secos rotineiros e `205` dias muito chuvosos.

### Slide 7 — Conclusões e Limitações (`0:45` · Caio / Ambos)
* **Aplicação prática:** Fiscalização orientada no **`km 145–159,3`** — velocidade e distância de seguimento nos picos secos/frios (`07h–08h`/`17h–18h`) e foco em **caminhões** na chuva (`08h`) e **sábados chuvosos**.
* **Limites científicos:** Sem denominador de VMD horário ou CNH por gênero, medimos *ocorrência observada*, não risco causal por km. Próximo passo: chuva horária local no timestamp + fluxo DNIT. Agradecimentos e abertura para perguntas.

---

## Respostas Rápidas para Perguntas Prováveis da Banca

* **"Por que o `ROC-AUC` deu `0,584`?"** → Porque gravidade viária depende fortemente de velocidade instantânea, distração e dinâmica veicular não observadas no boletim antes do impacto; mesmo assim, a Regressão Logística regularizada superou o acaso (`0,500`) e bateu árvores em generalização no ano cego de `2025`.
* **"Se choveu menos por dia em média, então é mais seguro dirigir na chuva?"** → **Não!** A agregação diária dilui que só chove `6,93%` das horas e que motos somem da rodovia na chuva (`-19,5%`). Sem fluxo de tráfego (VMD), seria falácia causal afirmar proteção.
* **"Qual foi o maior aprendizado do projeto?"** → A validação de campo dos dados: descobrir que `A835` era Maringá e reconstruir a série local (`83766` + `SBLO` + `ERA5`) elevou a acurácia espacial e provou na prática o ciclo iterativo do Slide 9.
