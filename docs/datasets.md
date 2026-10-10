# Datasets: NQ, HotpotQA, MS MARCO

**Source tags used below**

- **[P]** the RAGDefender paper, arXiv 2511.01268 (ACSAC 2025)
- **[B]** the BEIR paper, arXiv 2104.08663, and the BEIR README
- **[A]** the authors' artifact, `SecAI-Lab/RAGDefender` at commit `ba2a17e` (code and shipped data files)

---

## 1. At a glance

| | NQ | HotpotQA | MS MARCO |
|---|---|---|---|
| Task type | Open-domain QA, single-hop [P] | Multi-hop QA [P] | Machine reading comprehension / passage retrieval [P] |
| Original source | Kwiatkowski et al. 2019 (Google search queries, Wikipedia answers) [B] | Yang et al. 2018 [B] | Nguyen et al. 2016 (Bing queries) [B] |
| Distribution used | BEIR `nq` [A] | BEIR `hotpotqa` [A] | BEIR `msmarco` [A] |
| Corpus size | 2,681,468 passages [B] | 5,233,329 documents [B] | 8,841,823 passages [B], also stated in [P] |
| BEIR evaluation queries | 3,452 [B] | 7,405 [B] | 6,980 (dev) [B] |
| Split the artifact loads | `test` [A] | `test` [A] | `train` [A] |
| Retrieved set per query | 1 golden + 4 benign-irrelevant, top-k = 5 [P] | 2 golden, top-k = 2 [P] | 1 golden + several tangentially related. Paper: top-k = 5 [P]. Artifact: top-k = 2 [A] |
| Target queries attacked | 100 [A] | 100 [A] | 100 [A] |
| Adversarial passages at 1x / 2x / 4x / 6x | 5 / 10 / 20 / 30 [A] | 2 / 4 / 8 / 12 [A] | 2 / 4 / 8 / 12 [A] |
| Which Stage 1 variant the artifact calls | `find_num_adv_agg` [A] | `find_num_adv` [A] | `find_num_adv_agg` [A] |

The perturbation ratio is the number of adversarial passages divided by the number of golden plus benign-irrelevant passages [P]. For NQ that is 30 / 5 = 6x. The artifact's numbers above reproduce this arithmetic.

The paper does not state how many queries it evaluates per dataset. The artifact uses 100 target queries per dataset (see Section 4).

---

## 2. Per-dataset detail

### 2.1 Natural Questions (NQ)

- **Source.** Kwiatkowski et al. 2019. Queries are real Google search queries and answers are spans in Wikipedia articles [B]. The artifact uses the BEIR version, downloaded from the UKP BEIR server into `datasets/nq` and read with BEIR's `GenericDataLoader` [A].
- **Size.** The corpus has 2,681,468 passages and BEIR evaluates on 3,452 queries [B]. BEIR also notes 132,803 training pairs exist but are unused for zero-shot evaluation [B]. The RAGDefender paper gives no corpus or query count for NQ [P].
- **Splits.** The BEIR README lists `train` and `test` for NQ. The BEIR paper's own text calls the 3,452 queries both "development" and "test" and does not reconcile the two [B]. The artifact loads `test` [A].
- **Preprocessing.**
  - BEIR parsed the original HTML (not the ReQA version). It dropped queries with no answer, queries whose answer is a table, and queries with conflicting Wikipedia pages. Passages are title plus paragraph. Only the first 512 word pieces of each document are used [B].
  - The artifact builds the golden set from every corpus passage that shares the Wikipedia title of the qrels-relevant passage (`pos_ans` in `main.py`) [A]. The paper says one golden passage per query [P]. **Check:** log `len(pos_ans)` to see whether this is always 1.
  - Retrieval over the original corpus is precomputed and shipped as `results/beir_results/nq-contriever.json` [A].
  - In the PoisonedRAG path the attack text is built as `question + '.' + p` before it enters the candidate set [A].
- **Attacks.** PoisonedRAG, GARAG, Tan et al. (see Section 3).

### 2.2 HotpotQA

- **Source.** Yang et al. 2018, multi-hop questions that need reasoning over several paragraphs [B]. The artifact uses BEIR `hotpotqa` [A].
- **Size.** The corpus has 5,233,329 documents and BEIR evaluates on 7,405 queries [B]. The RAGDefender paper gives neither number [P].
- **Splits.** BEIR's `test` is the original HotpotQA dev set. BEIR created its own dev split by holding out 5,447 random training queries [B]. The BEIR README lists `train`, `dev`, `test`. The artifact loads `test` [A].
- **Preprocessing.** BEIR uses the full-Wikipedia setting with processed Wikipedia passages. The processing steps are not described [B]. The artifact takes the golden passages directly from the qrels (two per query, matching the paper) [A][P]. Precomputed retrieval is `results/beir_results/hotpotqa-contriever.json` [A].
- **Stage 1 for this dataset.** The paper uses a concentration-based grouping for multi-hop QA because clustering may fail there [P]. The artifact branches to `find_num_adv` for HotpotQA [A].
- **Attacks.** PoisonedRAG, GARAG, Tan et al.

### 2.3 MS MARCO

- **Source.** Nguyen et al. 2016, a human-generated reading comprehension dataset built from Bing queries with web passages [B]. The artifact uses BEIR `msmarco` [A].
- **Size.** The corpus has 8,841,823 passages [B][P]. BEIR's evaluation set is the official dev set with 6,980 queries [B]. The paper states the corpus size but no query count [P].
- **Splits.** The BEIR README lists `train`, `dev`, `test`. BEIR evaluates on dev [B]. **The artifact loads `train`** for all MS MARCO runs [A]. The reason is not documented. Treat this as a deviation to log.
- **Preprocessing.** BEIR gives only the passage count and the 512-word-piece rule. How the corpus was built or cleaned is not described [B]. The artifact's golden passages come from the qrels [A]. Precomputed retrieval is `results/beir_results/msmarco-contriever.json` [A].
- **Top-k.** The paper says top-k = 5 for MS MARCO [P]. The artifact sets `top_k = 2` and `adv_per_query = 2` for MS MARCO in all three run scripts [A]. This changes the meaning of the 1x / 2x / 4x / 6x ratios, so log it as a deviation.
- **Attacks.** PoisonedRAG, GARAG, Tan et al.

---

## 3. Which attacks run on which dataset

| Attack | What it does [P] | NQ | HotpotQA | MS MARCO | Ratios in the artifact [A] | Artifact entry point [A] |
|---|---|:-:|:-:|:-:|---|---|
| PoisonedRAG (Zou et al., USENIX Security 2025) | Injects LLM-generated misleading passages | yes | yes | yes | 1x, 2x, 4x, 6x | `claims/claim1_poisonedrag`, `run_poisonedrag.py` |
| GARAG (Cho et al., Findings of EMNLP 2024) | Typo-style low-level perturbations of documents | yes | yes | yes | 1x only | `claims/claim3_garag`, `run_garag.py` |
| Tan et al. (ACL 2024) | LLM-generated misleading text | yes | yes | yes | 1x only | `claims/claim2_tan`, `run_tan.py` |

Where each attack shows up in the paper (from the authors' `docs/reproducing-paper.md`) [A]:

- **Figure 4** covers all three attacks on all three datasets at 1x, 2x, 4x, 6x with a GPT-4o generator. The GPT-4o cells need an API key and a config the artifact does not ship.
- **Figure 5** covers PoisonedRAG only, across LLaMA-7B/13B, Vicuna-7B/13B, GPT-4o and Gemini-1.5-pro on the three datasets.
- The three artifact claims run the open-source rows only: LLaMA-7B and Vicuna-7B (8-bit) with Contriever.

Setup shared by all three attacks [P]: Contriever, ANCE and DPR retrievers; RAGDefender's own embeddings from Stella via Sentence Transformers in a FAISS `IndexFlatL2` index; GPT-4o and Gemini-1.5-pro used to create the adversarial passages; ten random seeds per experiment.

---

## 4. Attack data shipped in the artifact

All paths are under `artifacts/` [A].

| File or folder | NQ | HotpotQA | MS MARCO | Note |
|---|---:|---:|---:|---|
| `results/target_queries/<ds>.json` | 100 | 100 | 100 | Fields: `id`, `question`, `correct answer`, `incorrect answer` |
| `results/adv_targeted_results/<ds>.json` | 100 | 100 | 100 | One entry per target query |
| `poisoned_corpus/<ds>/gpt4/` | 100 files | 100 files | 100 files | Pre-written adversarial text that `main.py` reads for the PoisonedRAG runs. A parallel `gemini/` folder also has 100 files each |
| `tan/tan_<ds>.json` | 500 | 200 | 200 | Fields: `query`, `ground_truth`, `adversarial_document` |
| `GARAG/garag_<ds>.json` | 590 | 400 | 202 | Same three fields |

How target queries are used [A]: `repeat_times = 10` iterations, each taking `M = 10` consecutive target queries (indices `iter*10` to `iter*10 + 9`). That covers each of the 100 target queries once. The run scripts set `seed = 12`.

---

## 5. Discrepancies to put in your deviations log

Each of these is something I saw in the code or shipped files. None has been run yet, so confirm the ones marked "Check".

| # | Paper or documentation says | Artifact does | Why it matters |
|---|---|---|---|
| D1 | MS MARCO top-k = 5 [P] | `top_k = 2`, `adv_per_query = 2` [A] | Changes what 1x to 6x means for MS MARCO |
| D2 | BEIR evaluates MS MARCO on dev, 6,980 queries [B] | Loads `train` [A] | Different query pool from the standard benchmark |
| D3 | Ten random seeds [P] | `seed = 12` only, with 10 repeats of 10 queries [A] | Check whether "ten seeds" in the paper means these repeats |
| D4 | Figure 4 reports 1x, 2x, 4x, 6x for all attacks [A docs] | Tan and GARAG run at 1x only [A] | You can only reproduce part of Figure 4 for these two attacks |
| D5 | Claims 2 and 3 are different attacks | Their `expected/result.txt` numbers are identical; the files differ only by a trailing newline [A] | Check by running both. It may be a copy error in the expected files |
| D6 | Claim 1 text and expected output cover Contriever, DPR, ANCE [A] | `run_poisonedrag.py` runs Contriever only; DPR and ANCE are commented out [A] | Expected-output blocks for DPR and ANCE cannot be reproduced without editing the script |
| D7 | One golden passage per NQ query [P] | Golden set is all passages sharing the article title [A] | Check `len(pos_ans)` |
| D8 | Tan et al. and GARAG are attacks [P] | `claim.txt` files call them "defense" baselines [A] | Naming only. Do not copy that wording into your report |
| D9 | RAGDefender uses Stella embeddings [P] | `main.py` creates `SentenceTransformer('paraphrase-MiniLM-L6-v2')` as `s_model`, and the package default embedder is `minilm-all` [A] | Check which stage uses `s_model`. The authors also document that `ConcentrationBasedGrouping` differs from the paper's Eq. 3 and that expected results come from the legacy code [A docs] |

---

## 6. Not stated, still to find

- Number of queries per dataset used in the paper's experiments [P]
- Query counts, preprocessing and split for each dataset in the paper itself (the BEIR numbers above are the best available) [P]
- Which generator the paper pairs with which dataset, beyond Figure 4 (GPT-4o) [P]
- Per-dataset results tables and the appendix (not read)
- How `adv_targeted_results/<ds>.json` was produced (not inspected)

---

## 7. Getting the data

The artifact downloads each BEIR dataset automatically on first use: `https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/<name>.zip`, unzipped into `datasets/<name>` in the working directory [A]. These corpora are large (millions of passages), so check free disk space before you run anything. Do not commit `datasets/` to GitHub.

---

## 8. References

Verify full bibliographic details before they go in the Overleaf paper (task 10). The entries below carry only what the sources I read stated.

1. RAGDefender: "Rescuing the Unpoisoned: Efficient Defense against Knowledge Corruption Attacks on RAG Systems", arXiv 2511.01268, ACSAC 2025.
2. Authors' artifact: https://github.com/SecAI-Lab/RAGDefender (MIT licence).
3. Thakur et al., BEIR benchmark, arXiv 2104.08663.
4. Kwiatkowski et al., 2019, Natural Questions.
5. Yang et al., 2018, HotpotQA.
6. Nguyen et al., 2016, MS MARCO.
7. Zou et al., PoisonedRAG, USENIX Security 2025.
8. Cho et al., GARAG, Findings of EMNLP 2024.
9. Tan et al., ACL 2024 (the "Blinded by generated contexts" paper cited by the artifact).
