# Evidências de execução na nuvem

Gerado em 2026-11-03T23:00:04+00:00 por `radar evidence`, a partir das tabelas operacionais do BigQuery (`alfabetizacao_ops`).

## Execuções recentes

| run_id | comando | status | inicio | segundos | erro |
|---|---|---|---|---|---|
| 20261103T222353Z-08c944 | batch | succeeded | 2026-11-03 22:23:53.248614+00:00 | 13 |  |
| 20261103T203512Z-691fee | consume | succeeded | 2026-11-03 20:35:12.420392+00:00 | 24 |  |
| 20261103T203459Z-143f48 | detect | succeeded | 2026-11-03 20:34:59.166490+00:00 | 6 |  |
| 20261103T203437Z-543a62 | batch | succeeded | 2026-11-03 20:34:37.522889+00:00 | 15 |  |
| 20261103T200726Z-0f08bb | batch | failed | 2026-11-03 20:07:26.461102+00:00 | 93 | QualityGateError: Gate de qualidade 'silver' falhou: demo.falha_injetada |
| 20261103T200359Z-b0f7ce | batch | failed | 2026-11-03 20:03:59.396054+00:00 | 102 | QualityGateError: Gate de qualidade 'silver' falhou: demo.falha_injetada |
| 20261103T200115Z-2ae891 | batch | succeeded | 2026-11-03 20:01:15.445351+00:00 | 15 |  |
| 20261103T195525Z-841b9c | consume | succeeded | 2026-11-03 19:55:25.398801+00:00 | 40 |  |
| 20261103T193548Z-7db1fc | consume | succeeded | 2026-11-03 19:35:48.941283+00:00 | 285 |  |
| 20261103T193403Z-40d0d2 | detect | succeeded | 2026-11-03 19:34:03.176113+00:00 | 18 |  |
| 20261103T192403Z-10157e | batch | succeeded | 2026-11-03 19:24:03.831007+00:00 | 122 |  |

## Jobs do BigQuery (job_id, linhas e bytes faturados)

| run_id | comando | etapa | job_id | linhas | bytes_processed | bytes_faturados | segundos |
|---|---|---|---|---|---|---|---|
| 20261103T192403Z-10157e | batch | bronze.export.alunos | 2d3ee423-86aa-49ed-ab3b-596b82b40ce3 |  | 322697226 | 322961408 | 1.445 |
| 20261103T192403Z-10157e | batch | silver.alunos | 3f2871c0-62cc-44a7-88ac-6fa0b71c64ae |  | 322698481 | 322961408 | 3.674 |
| 20261103T192403Z-10157e | batch | bronze.alunos | a07a8abb-516c-4bdc-8949-e0aaecadc0f2 |  | 268545240 | 269484032 | 6.587 |
| 20261103T192403Z-10157e | batch | gold.reconciliacao | ea4e777b-2a4d-4821-bb56-f1127e486c73 |  | 151122223 | 152043520 | 1.551 |
| 20261103T192403Z-10157e | batch | gold.termometro | b1140f29-1131-451a-adfa-b026949646a8 | 10788 | 558703 | 52428800 | 1.604 |
| 20261103T192403Z-10157e | batch | silver.municipio | e51e254e-2119-457c-a123-3ff8ed7784fb |  | 2169246 | 31457280 | 1.182 |
| 20261103T192403Z-10157e | batch | gold.ml_features | 44fcf1f5-06ec-4d1d-acf9-47e186b22611 |  | 3166484 | 31457280 | 1.745 |
| 20261103T192403Z-10157e | batch | bronze.municipio | 058930f4-314d-4329-89c2-d3e07ffdc9e1 |  | 1832061 | 20971520 | 4.455 |
| 20261103T192403Z-10157e | batch | bronze.uf | a86d0b23-c9ca-42bb-b244-d2febbf8d01a |  | 10330 | 20971520 | 4.642 |
| 20261103T192403Z-10157e | batch | bronze.meta_alfabetizacao_brasil | af665cfd-748d-4525-bacb-f05180f4213c |  | 270 | 20971520 | 3.929 |
| 20261103T192403Z-10157e | batch | bronze.meta_alfabetizacao_uf | 4412d875-a422-451c-8878-8a9a2f10a2b4 |  | 7374 | 20971520 | 3.446 |
| 20261103T192403Z-10157e | batch | bronze.meta_alfabetizacao_municipio | 6065e1e2-7dca-456c-a08a-036d5fc2f69f |  | 1151232 | 20971520 | 3.933 |
| 20261103T192403Z-10157e | batch | bronze.dicionario | a42cd9ee-7de1-47da-8409-007210bc22d0 |  | 1174 | 20971520 | 3.947 |
| 20261103T192403Z-10157e | batch | silver.uf | d679eb26-2782-48f9-9517-3ed5140e7ca1 |  | 13399 | 20971520 | 1.356 |
| 20261103T192403Z-10157e | batch | silver.meta_municipio | 190e1132-37cd-41c0-a952-a997a8c8aa5e |  | 1301304 | 20971520 | 1.205 |
| 20261103T192403Z-10157e | batch | gold.indicador_municipal | a1899373-d4c8-4602-b7d2-7987fbd239cd |  | 3025366 | 20971520 | 1.819 |
| 20261103T192403Z-10157e | batch | bronze.export.municipio | c4a10ea7-3093-46f2-9fbd-9646ccae0e70 |  | 2167991 | 10485760 | 0.578 |
| 20261103T192403Z-10157e | batch | bronze.export.uf | 597f1e27-ac01-404a-ae69-d6a4e3ad2c46 |  | 12360 | 10485760 | 0.83 |
| 20261103T192403Z-10157e | batch | bronze.export.meta_alfabetizacao_brasil | 30e4b8ce-3e0d-4d1f-984f-bb3657621dfb |  | 312 | 10485760 | 0.917 |
| 20261103T192403Z-10157e | batch | bronze.export.meta_alfabetizacao_uf | 9ae0afe0-9a52-4032-afcb-f4ec38b5b5da |  | 8508 | 10485760 | 0.861 |
| 20261103T192403Z-10157e | batch | bronze.export.meta_alfabetizacao_municipio | 628d108d-bffc-45d3-b7c2-190c6136e98b |  | 1301088 | 10485760 | 0.833 |
| 20261103T192403Z-10157e | batch | bronze.export.dicionario | e8f5acaf-449f-4f60-b1ba-0962598efca3 |  | 1552 | 10485760 | 0.92 |
| 20261103T192403Z-10157e | batch | silver.dicionario | a6ebf4ee-45e0-4f15-975a-cf9a923a4a66 |  | 1417 | 10485760 | 0.977 |
| 20261103T192403Z-10157e | batch | silver.meta_brasil | a7691db9-8814-43bb-96b2-0b46852c1f2c |  | 312 | 10485760 | 0.849 |
| 20261103T192403Z-10157e | batch | silver.meta_uf | 80126f94-c164-433e-9690-9b8be175b7bf |  | 8508 | 10485760 | 1.034 |
| 20261103T192403Z-10157e | batch | gold.ml_labels | b37d7daf-4115-49ae-bb7a-4895e6b63dd5 |  | 558101 | 10485760 | 1.197 |
| 20261103T192403Z-10157e | batch | ddl.schema | 5334bdac-91d7-47e1-9773-95cb09e8ff36 |  | 0 | 0 | 4.49 |
| 20261103T192403Z-10157e | batch | silver.ref_uf | c83ef3c3-53d3-44de-b711-472cff9e6b28 |  | 0 | 0 | 1.082 |
| 20261103T193403Z-40d0d2 | detect | detect.read.meta_alfabetizacao_brasil | 2ac6e29d-1bf9-483f-8107-b8406ce2129f |  | 270 | 10485760 | 0.188 |
| 20261103T193403Z-40d0d2 | detect | detect.read.meta_alfabetizacao_uf | 0cda9c1e-0754-4559-9a41-0a71ba7d2fcd |  | 7374 | 10485760 | 0.163 |
| 20261103T193403Z-40d0d2 | detect | detect.read.meta_alfabetizacao_municipio | 1f186786-8094-436a-b869-ba0921c9cddb |  | 1151232 | 10485760 | 0.234 |
| 20261103T193403Z-40d0d2 | detect | ddl.schema | 72de0f00-e2f7-44ec-914b-7ce56f51d209 |  | 0 | 0 | 3.976 |
| 20261103T193403Z-40d0d2 | detect | detect.known.meta_alfabetizacao_brasil | 8c27c3df-6663-4f8f-9764-b215291aadbf |  | 0 | 0 | 0.176 |
| 20261103T193403Z-40d0d2 | detect | detect.known.meta_alfabetizacao_uf | 9525a1c0-725d-492e-90c7-8dfa45f76e6d |  | 0 | 0 | 0.144 |
| 20261103T193403Z-40d0d2 | detect | detect.known.meta_alfabetizacao_municipio | 95967f11-d631-45d2-8451-ecf4dfd8dc3f |  | 0 | 0 | 0.165 |
| 20261103T193548Z-7db1fc | consume | stream.commit | f456d2c6-445b-4bff-be31-e76f776491fa |  | 799581 | 52428800 | 5.41 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 22fee257-38c9-4175-96c9-97f7fc3b07eb |  | 774546 | 52428800 | 5.872 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 02cc215a-8c4f-426d-b920-243809e30ca3 |  | 951011 | 52428800 | 6.547 |
| 20261103T193548Z-7db1fc | consume | stream.commit | a7e27b8d-cac6-41f7-8b3d-1a11176752cb |  | 1270123 | 52428800 | 4.818 |
| 20261103T193548Z-7db1fc | consume | stream.commit | a3eefe56-0788-45ce-bf2a-49363fdf181e |  | 1523907 | 52428800 | 5.307 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 7382660b-1226-48e2-b501-6ecd76db1669 |  | 1777667 | 52428800 | 4.217 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 01bf0508-7cd5-4142-84bd-51eed894f19c |  | 1656191 | 52428800 | 4.497 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 77505b29-8aed-454c-ae14-d697e3ef9e3c |  | 1735705 | 52428800 | 5.06 |
| 20261103T193548Z-7db1fc | consume | stream.commit | be55dcdc-635a-4e18-9d3c-eaefa895b5ef |  | 2087241 | 52428800 | 4.928 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 3db548f9-7678-4bd6-b919-33abf8a2c44f |  | 2341694 | 52428800 | 4.807 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 30725183-b0b8-4fb9-b9f2-ce81392c51c2 |  | 2263900 | 52428800 | 4.689 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 185d855d-3e2b-4776-b97f-3491ebed656c |  | 2596726 | 52428800 | 4.741 |
| 20261103T193548Z-7db1fc | consume | stream.commit | cebfaef8-41b9-492e-a88e-70b2c7427406 |  | 2859039 | 52428800 | 4.991 |
| 20261103T193548Z-7db1fc | consume | stream.commit | d0d032d0-70f0-4aa7-9faf-1b2653fc8614 |  | 2934763 | 52428800 | 5.23 |
| 20261103T193548Z-7db1fc | consume | stream.commit | eedec58f-a68d-45fc-882e-c502481a4432 |  | 3248659 | 52428800 | 5.382 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 96a9c525-3036-4d5e-bdb7-b686c293637a |  | 3503699 | 52428800 | 4.922 |
| 20261103T193548Z-7db1fc | consume | stream.commit | 48151fdb-e74c-4cf3-93c9-7d2eb3a5ca11 |  | 3502132 | 52428800 | 5.699 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 48e496a6-5222-4ac7-b0f3-d597cbc59c1c |  | 13926 | 20971520 | 0.247 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | adc72efe-7684-42db-bbdc-24f9c312fc13 |  | 14124 | 20971520 | 0.187 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 5b3b608b-0fb3-4f90-ac39-7e349ea43d09 |  | 45144 | 20971520 | 0.163 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 8f44c4e1-6b8d-45a2-96b4-fd677151d5cd |  | 111144 | 20971520 | 0.162 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 0faf0c5d-b8d6-4fb3-b07d-4b4bc437c082 |  | 177144 | 20971520 | 0.168 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 840002e1-32b6-4591-aee4-15f8e812a5df |  | 243144 | 20971520 | 0.175 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | ad2582d4-2c2f-41b7-8f52-f32e474f5bf6 |  | 243540 | 20971520 | 0.248 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 928aa06a-68c5-43cc-a373-5fd343e646e3 |  | 257598 | 20971520 | 0.167 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 752bb87c-3bde-4696-acc3-e4f7522ecca4 |  | 323598 | 20971520 | 0.181 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 2ab04064-2e1e-4541-ab99-0884a813c334 |  | 389532 | 20971520 | 0.173 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | 7e998394-d539-48c6-bfe7-5017a626b630 |  | 397584 | 20971520 | 0.183 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | d9d05299-399c-4664-9147-48f40fb09ba8 |  | 458172 | 20971520 | 0.148 |
| 20261103T193548Z-7db1fc | consume | stream.ledger_check | a3a47394-992a-46db-b0da-741c16c53731 |  | 524172 | 20971520 | 0.166 |

## Qualidade por execução e camada

| run_id | camada | severidade | aprovadas | reprovadas |
|---|---|---|---|---|
| 20261103T222353Z-08c944 | contract | informative | 8 | 0 |
| 20261103T222353Z-08c944 | contract | blocking | 14 | 0 |
| 20261103T203437Z-543a62 | contract | informative | 8 | 0 |
| 20261103T203437Z-543a62 | contract | blocking | 14 | 0 |
| 20261103T200726Z-0f08bb | silver | informative | 2 | 0 |
| 20261103T200726Z-0f08bb | silver | blocking | 17 | 1 |
| 20261103T200726Z-0f08bb | bronze | blocking | 1 | 0 |
| 20261103T200726Z-0f08bb | contract | informative | 8 | 0 |
| 20261103T200726Z-0f08bb | contract | blocking | 14 | 0 |
| 20261103T200359Z-b0f7ce | silver | informative | 2 | 0 |
| 20261103T200359Z-b0f7ce | silver | blocking | 17 | 1 |
| 20261103T200359Z-b0f7ce | bronze | blocking | 1 | 0 |
| 20261103T200359Z-b0f7ce | contract | informative | 8 | 0 |
| 20261103T200359Z-b0f7ce | contract | blocking | 14 | 0 |
| 20261103T200115Z-2ae891 | contract | informative | 8 | 0 |
| 20261103T200115Z-2ae891 | contract | blocking | 14 | 0 |
| 20261103T192403Z-10157e | gold | informative | 4 | 1 |
| 20261103T192403Z-10157e | gold | blocking | 5 | 0 |
| 20261103T192403Z-10157e | silver | informative | 2 | 0 |
| 20261103T192403Z-10157e | silver | blocking | 17 | 0 |
| 20261103T192403Z-10157e | bronze | blocking | 1 | 0 |
| 20261103T192403Z-10157e | contract | informative | 8 | 0 |
| 20261103T192403Z-10157e | contract | blocking | 14 | 0 |

## Regras reprovadas

| run_id | regra | severidade | observado | esperado |
|---|---|---|---|---|
| 20261103T200726Z-0f08bb | demo.falha_injetada | blocking | 1 | == 0 |
| 20261103T200359Z-b0f7ce | demo.falha_injetada | blocking | 1 | == 0 |
| 20261103T192403Z-10157e | gold.indicador_municipal.selo_baixo_raro | informative | 0.1007 | <= 0.1 |

## Lotes de streaming

| batch_id | recebidas | validas | quarentena | dup_no_lote | dup_no_ledger | integradas | latencia_p50_s | latencia_p95_s |
|---|---|---|---|---|---|---|---|---|
| 20261103T195525Z-841b9c-b1 | 8 | 2 | 6 | 1 | 1 | 0 | 8.38 | 8.38 |
| 20261103T193548Z-7db1fc-b17 | 323 | 323 | 0 | 0 | 0 | 323 | 341.3 | 341.3 |
| 20261103T193548Z-7db1fc-b16 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 327.6 | 327.8 |
| 20261103T193548Z-7db1fc-b15 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 311 | 311.3 |
| 20261103T193548Z-7db1fc-b14 | 523 | 523 | 0 | 0 | 0 | 523 | 297.2 | 297.2 |
| 20261103T193548Z-7db1fc-b13 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 282.6 | 287.8 |
| 20261103T193548Z-7db1fc-b12 | 918 | 918 | 0 | 0 | 0 | 918 | 267.4 | 267.4 |
| 20261103T193548Z-7db1fc-b11 | 122 | 122 | 0 | 0 | 0 | 122 | 253.9 | 253.9 |
| 20261103T193548Z-7db1fc-b10 | 999 | 999 | 0 | 0 | 0 | 999 | 238.7 | 238.8 |
| 20261103T193548Z-7db1fc-b9 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 223.2 | 223.3 |
| 20261103T193548Z-7db1fc-b8 | 213 | 213 | 0 | 0 | 0 | 213 | 207.3 | 207.6 |
| 20261103T193548Z-7db1fc-b7 | 6 | 6 | 0 | 0 | 0 | 6 | 193.2 | 193.2 |
| 20261103T193548Z-7db1fc-b6 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 178.9 | 179.1 |
| 20261103T193548Z-7db1fc-b5 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 162.9 | 162.9 |
| 20261103T193548Z-7db1fc-b4 | 1000 | 1000 | 0 | 0 | 0 | 1000 | 149 | 149.3 |
| 20261103T193548Z-7db1fc-b3 | 470 | 470 | 0 | 0 | 0 | 470 | 130.8 | 130.9 |
| 20261103T193548Z-7db1fc-b2 | 3 | 3 | 0 | 0 | 0 | 3 | 121.9 | 121.9 |
| 20261103T193548Z-7db1fc-b1 | 211 | 211 | 0 | 0 | 0 | 211 | 97.26 | 97.26 |

## Linhas por tabela

| dataset | tabela | linhas | bytes |
|---|---|---|---|
| alfabetizacao_bronze | alunos | 3867999 | 450341193 |
| alfabetizacao_bronze | dicionario | 27 | 2443 |
| alfabetizacao_bronze | meta_alfabetizacao_brasil | 3 | 411 |
| alfabetizacao_bronze | meta_alfabetizacao_municipio | 10704 | 1654320 |
| alfabetizacao_bronze | meta_alfabetizacao_uf | 81 | 11181 |
| alfabetizacao_bronze | municipio | 23995 | 2959826 |
| alfabetizacao_bronze | stream_events | 10796 | 6585255 |
| alfabetizacao_bronze | stream_quarantine | 0 | 0 |
| alfabetizacao_bronze | uf | 145 | 17145 |
| alfabetizacao_gold | indicador_municipal | 10704 | 1922641 |
| alfabetizacao_gold | ml_features | 10704 | 1231080 |
| alfabetizacao_gold | ml_labels | 5232 | 235440 |
| alfabetizacao_gold | reconciliacao | 24161 | 1987671 |
| alfabetizacao_gold | termometro | 10788 | 1890275 |
| alfabetizacao_ops | quality_results | 204 | 35629 |
| alfabetizacao_ops | runs | 22 | 2384 |
| alfabetizacao_ops | source_versions | 10 | 978 |
| alfabetizacao_ops | steps | 211 | 27085 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b1 | 211 | 40022 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b10 | 999 | 189678 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b11 | 122 | 23036 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b12 | 918 | 174364 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b13 | 1000 | 188261 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b14 | 523 | 99254 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b15 | 1000 | 189816 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b16 | 1000 | 189928 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b17 | 323 | 61342 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b2 | 3 | 529 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b3 | 470 | 88868 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b4 | 1000 | 189480 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b5 | 1000 | 189632 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b6 | 1000 | 189696 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b7 | 6 | 1116 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b8 | 213 | 40330 |
| alfabetizacao_ops | stg_20261103t193548z_7db1fc_b9 | 1000 | 189904 |
| alfabetizacao_ops | stg_20261103t195525z_841b9c_b1 | 1 | 179 |
| alfabetizacao_ops | stream_batches | 18 | 2479 |
| alfabetizacao_silver | alunos | 3867999 | 329997776 |
| alfabetizacao_silver | dicionario | 27 | 1039 |
| alfabetizacao_silver | meta_brasil | 3 | 187 |
| alfabetizacao_silver | meta_municipio | 10704 | 840816 |
| alfabetizacao_silver | meta_uf | 81 | 5229 |
| alfabetizacao_silver | municipio | 23995 | 2434729 |
| alfabetizacao_silver | ref_uf | 27 | 216 |
| alfabetizacao_silver | stream_events | 10788 | 2439509 |
| alfabetizacao_silver | uf | 145 | 12994 |
