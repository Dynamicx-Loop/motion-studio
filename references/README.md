# Retargeting reference library

Eight records exported from your Zotero Desktop personal library on 2026-10-21
using the query `retarget`. This is a search snapshot, not an exhaustive survey.
Bibliographic metadata is reproduced from Zotero and has not been independently
verified. No PDFs were copied. Local attachment paths, abstracts, and annotations
are omitted from the portable [BibTeX bibliography](retargeting.bib).

Zotero item keys identify library records; BibTeX keys identify citations.
[zotero-items.json](zotero-items.json) preserves their mapping and author lists.

| Reference | Authors | Year | BibTeX key | Zotero item |
| --- | --- | --- | --- | --- |
| Unified Motion Retargeting for Humanoids with Learned Point Cloud Correspondence | Hanyang Cao, Yuetong Fang, Taesoo Kwon, Runyi Yu, Ji Ma, Jing Tan, Yangchen Zhou, Baoze Du, Yi Gu, Yukang Gao, Ruoli Dai, Lei Han, Renjing Xu | 2026 | `cao_unified_2026` | [A5BYCLWC](zotero://select/library/items/A5BYCLWC) |
| PriMoRetarget: Humanoid Motion Transfer Through Prioritized Motion Retargeting | Nicholas Ioannidis, Dun Yang, Max Smith, Tue Vu, Ziyu Zhang, Shayegan Omidshafiei, Xue Bin Peng | 2026 | `ioannidis_primoretarget_2026` | [LBHNP2TM](zotero://select/library/items/LBHNP2TM) |
| DMP: Directable Motion Retargeting through Motion Paraphrasing | Sunmin Lee, Davis Rempe, Yifeng Jiang, Haotian Zhang, Tingwu Wang, Jungdam Won, Xue Bin Peng | 2026 | `lee_dmp_2026` | [9LIHZZZP](zotero://select/library/items/9LIHZZZP) |
| ReActor: Reinforcement Learning for Physics-Aware Motion Retargeting | David Müller, Agon Serifi, Sammy Christen, Ruben Grandia, Espen Knoop, Moritz Bächer | 2026 | `muller_reactor_2026` | [3Y9KV28J](zotero://select/library/items/3Y9KV28J) |
| SPARK: Skeleton-Parameter Aligned Retargeting on Humanoid Robots with Kinodynamic Trajectory Optimization | Hanwen Wang, Qiayuan Liao, Bike Zhang, Kunzhao Ren, Koushil Sreenath, Xiaobin Xiong | 2026 | `wang_spark_2026` | [PCKWMJ7W](zotero://select/library/items/PCKWMJ7W) |
| DynaRetarget: Dynamically-Feasible Retargeting using Sampling-Based Trajectory Optimization | Victor Dhedin, Ilyass Taouil, Shafeef Omar, Dian Yu, Kun Tao, Angela Dai, Majid Khadiv | 2026 | `dhedin_dynaretarget_2026` | [T55ET6CK](zotero://select/library/items/T55ET6CK) |
| Retargeting Matters: General Motion Retargeting for Humanoid Motion Tracking | Joao Pedro Araujo, Yanjie Ze, Pei Xu, Jiajun Wu, C. Karen Liu | 2025 | `araujo_retargeting_2025` | [IZBNS7SI](zotero://select/library/items/IZBNS7SI) |
| Skeleton-Aware Networks for Deep Motion Retargeting | Kfir Aberman, Peizhuo Li, Dani Lischinski, Olga Sorkine-Hornung, Daniel Cohen-Or, Baoquan Chen | 2020 | `aberman_skeleton-aware_2020` | [5Z5PU5X3](zotero://select/library/items/5Z5PU5X3) |

## Reading notes

Use each record as a starting point for method notes and experiment links. UMR is
already checked out in `externals/UMR`; the other references do not imply installed
implementations. Add new records deliberately as the project scope expands.

- [UMR paper study v1](umr-paper-study-v1.md) — versioned study of arXiv
  2609.02134v2, pinned implementation evidence, Astro implications, and
  reproducibility and metric definitions for future experiment reports.
- [UMR SMPL-X/SOMA weights, rigs, labels and correspondence](umr-smplx-soma-weights.md)
  — primary-source inspection for the static Astro/G1 source-model comparison.
- [UMR fixed-head constraints and Astro Dex3-1 hands](umr-fixed-head-and-dex3-hands.md)
  — fixed-head ownership versus surface objectives, static Jacobian evidence,
  and the separate articulated-hand correspondence question.

## Refresh

With Zotero Desktop and its local API running, use the Zotero skill's
`export-bibtex` command with the comma-separated item keys in `zotero-items.json`.
Export to a temporary file, remove `file`, `abstract`, and `annote` fields, and
review changes before replacing `retargeting.bib`. Preserve the Zotero/BibTeX key
mapping if citation keys change. Repeat the search to discover newly added items.

- [UMR wrist/hand static correction](umr-wrist-hand-static-correction.md): pinned objective and normalization source, wrist/palm chain, label conventions, and controlled-calibration caveats.
