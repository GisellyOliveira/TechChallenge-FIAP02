"""FinOps: projeção mensal de custo a partir de quantidades MEDIDAS e preços de lista.

Quantidades vêm do `INFORMATION_SCHEMA` do BigQuery, das tabelas `ops.*` e do tamanho real do
bucket. Os preços ficam em `config/finops_prices.yaml`, com a marca de verificação de cada fonte.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from radar_alfabetizacao.pipeline.context import PipelineContext

TIB = 1024**4
GIB = 1024**3


@dataclass(frozen=True)
class RunCost:
    """Custo médio medido de um tipo de execução."""

    execucoes: int
    bytes_faturados: float
    segundos: float


@dataclass(frozen=True)
class Measurements:
    run_costs: Mapping[tuple[str, str], RunCost]
    bq_ativo_bytes: float
    bq_longo_bytes: float
    gcs_bytes: float
    pubsub_bytes: float
    total_bytes_faturados: float = 0.0


@dataclass(frozen=True)
class FinOpsLine:
    servico: str
    unidade: str
    quantidade: str
    preco: str
    custo_mensal: float
    custo_sem_franquia: float


@dataclass(frozen=True)
class Projection:
    lines: list[FinOpsLine]
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(line.custo_mensal for line in self.lines)

    @property
    def total_sem_franquia(self) -> float:
        return sum(line.custo_sem_franquia for line in self.lines)


def collect_measurements(ctx: PipelineContext, *, gcs_bytes: float, days: int) -> Measurements:
    """Lê do BigQuery as quantidades medidas (custos por execução, armazenamento, Pub/Sub)."""
    s = ctx.settings
    commands = ctx.run_sql("ops/finops_comandos.sql", step="finops.comandos").rows
    run_costs = {
        (r["comando"], r["variante"]): RunCost(
            int(r["execucoes"]),
            float(r["bytes_faturados_medios"] or 0),
            float(r["segundos_medios"] or 0),
        )
        for r in commands
    }
    ativo, longo = ctx.warehouse.dataset_storage([s.bronze, s.silver, s.gold, s.ops])
    pubsub = ctx.run_sql("ops/finops_pubsub.sql", step="finops.pubsub")
    total = ctx.run_sql("ops/finops_bigquery_total.sql", step="finops.total", params={"dias": days})
    return Measurements(
        run_costs=run_costs,
        bq_ativo_bytes=float(ativo),
        bq_longo_bytes=float(longo),
        gcs_bytes=gcs_bytes,
        pubsub_bytes=float(pubsub.rows[0]["bytes"]),
        total_bytes_faturados=float(total.rows[0]["bytes_faturados"]),
    )


def load_prices(path: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded


def _lookup(
    costs: Mapping[tuple[str, str], RunCost], command: str, variant: str
) -> tuple[RunCost | None, str | None]:
    """Custo medido da variante; se ainda não foi medida, usa a mais cara medida (conservador)."""
    exact = costs.get((command, variant))
    if exact is not None:
        return exact, None
    measured = [c for (cmd, _), c in costs.items() if cmd == command]
    if not measured:
        return None, f"Sem execução medida de '{command}'; contribuição considerada zero."
    worst = max(measured, key=lambda c: (c.bytes_faturados, c.segundos))
    note = (
        f"'{command}' na variante '{variant}' ainda não foi medido: usado o caso mais caro medido "
        "(estimativa conservadora). Rode o comando de novo para medir."
    )
    return worst, note


def _monthly_executions(prices: Mapping[str, Any]) -> list[tuple[str, str, float]]:
    """Execuções por mês de cada comando, separando as ociosas das que tiveram trabalho."""
    cron = prices["cronograma"]
    updates = float(cron["atualizacoes_fonte_por_mes"])
    return [
        ("batch", "sem_mudancas", float(cron["batch_por_mes"]) - updates),
        ("batch", "completo", updates),
        ("detect", "sem_mudancas", float(cron["detect_por_mes"]) - updates),
        ("detect", "completo", updates),
        ("consume", "sem_mudancas", float(cron["consume_por_mes"]) - updates),
        ("consume", "completo", updates),
    ]


def project(m: Measurements, prices: Mapping[str, Any]) -> Projection:
    notes: list[str] = []
    bq, run, ps = prices["bigquery"], prices["cloud_run_jobs"], prices["pubsub"]
    gcs, sch = prices["cloud_storage"], prices["cloud_scheduler"]

    bytes_month = vcpu_s = 0.0
    for command, variant, count in _monthly_executions(prices):
        cost, note = _lookup(m.run_costs, command, variant)
        if note and note not in notes:
            notes.append(note)
        if cost is None:
            continue
        bytes_month += count * cost.bytes_faturados
        vcpu_s += count * cost.segundos * float(run["vcpu_por_job"])
    gib_s = vcpu_s * float(run["memoria_gib_por_job"]) / float(run["vcpu_por_job"])

    tib = bytes_month / TIB
    analise_bruto = tib * float(bq["analise_usd_por_tib"])
    analise = max(0.0, tib - float(bq["franquia_analise_tib_mes"])) * float(
        bq["analise_usd_por_tib"]
    )

    ativo, longo = m.bq_ativo_bytes / GIB, m.bq_longo_bytes / GIB
    free = float(bq["franquia_armazenamento_gib"])
    ativo_pago = max(0.0, ativo - free)
    longo_pago = max(0.0, longo - max(0.0, free - ativo))
    armaz = ativo_pago * float(bq["armazenamento_ativo_usd_por_gib_mes"]) + longo_pago * float(
        bq["armazenamento_longo_usd_por_gib_mes"]
    )
    armaz_bruto = ativo * float(bq["armazenamento_ativo_usd_por_gib_mes"]) + longo * float(
        bq["armazenamento_longo_usd_por_gib_mes"]
    )

    gcs_gib = m.gcs_bytes / GIB
    gcs_custo = max(0.0, gcs_gib - float(gcs["franquia_gib_mes"])) * float(
        gcs["standard_usd_por_gib_mes"]
    )
    gcs_bruto = gcs_gib * float(gcs["standard_usd_por_gib_mes"])

    ps_gib = 2 * m.pubsub_bytes / GIB  # publicação + entrega ao assinante
    ps_custo = max(0.0, ps_gib - float(ps["franquia_gib_mes"])) / 1024 * float(ps["usd_por_tib"])
    ps_bruto = ps_gib / 1024 * float(ps["usd_por_tib"])

    run_custo = max(0.0, vcpu_s - float(run["franquia_vcpu_segundos"])) * float(
        run["vcpu_segundo_usd"]
    )
    run_custo += max(0.0, gib_s - float(run["franquia_gib_segundos"])) * float(
        run["gib_segundo_usd"]
    )
    run_bruto = vcpu_s * float(run["vcpu_segundo_usd"]) + gib_s * float(run["gib_segundo_usd"])

    jobs = int(prices["cronograma"]["jobs_agendados"])
    sch_custo = max(0, jobs - int(sch["jobs_gratuitos"])) * float(sch["usd_por_job_mes"])
    sch_bruto = jobs * float(sch["usd_por_job_mes"])

    unverified = [
        k for k, v in prices.items() if isinstance(v, dict) and v.get("verificado") is False
    ]
    if unverified:
        notes.append(f"Preços ainda não conferidos na página oficial: {', '.join(unverified)}.")

    lines = [
        FinOpsLine(
            "BigQuery: análise (on-demand)",
            "TiB processados/mês",
            f"{tib:.6f} TiB ({bytes_month / 1e6:.0f} MB) projetados a partir de execuções medidas",
            f"US$ {bq['analise_usd_por_tib']}/TiB; 1 TiB/mês grátis",
            analise,
            analise_bruto,
        ),
        FinOpsLine(
            "BigQuery: armazenamento",
            "GiB-mês (lógico)",
            f"{ativo:.3f} ativo + {longo:.3f} longo prazo, medidos",
            f"US$ {bq['armazenamento_ativo_usd_por_gib_mes']}/GiB ativo; 10 GiB/mês grátis",
            armaz,
            armaz_bruto,
        ),
        FinOpsLine(
            "Cloud Storage: Bronze Parquet",
            "GiB-mês",
            f"{gcs_gib:.3f} GiB, medidos no bucket",
            f"US$ {gcs['standard_usd_por_gib_mes']}/GiB ({gcs['regiao']}); 5 GiB/mês grátis",
            gcs_custo,
            gcs_bruto,
        ),
        FinOpsLine(
            "Pub/Sub: mensagens",
            "GiB trafegados/mês",
            f"{ps_gib:.4f} GiB (volume medido x2: publicação e entrega)",
            f"US$ {ps['usd_por_tib']}/TiB; 10 GiB/mês grátis",
            ps_custo,
            ps_bruto,
        ),
        FinOpsLine(
            "Cloud Run Jobs",
            "vCPU-s e GiB-s/mês",
            f"{vcpu_s:.0f} vCPU-s e {gib_s:.0f} GiB-s projetados a partir de durações medidas",
            f"US$ {run['vcpu_segundo_usd']}/vCPU-s e US$ {run['gib_segundo_usd']}/GiB-s; "
            "franquia mensal",
            run_custo,
            run_bruto,
        ),
        FinOpsLine(
            "Cloud Scheduler",
            "jobs agendados",
            f"{jobs} jobs",
            f"US$ {sch['usd_por_job_mes']}/job; {sch['jobs_gratuitos']} grátis",
            sch_custo,
            sch_bruto,
        ),
    ]
    return Projection(lines, notes)


def render_markdown(p: Projection, measured_total_bytes: float, window_days: int) -> str:
    out = [
        "# FinOps: projeção mensal de custo",
        "",
        "| Serviço | Unidade | Quantidade medida | Preço unitário | Custo mensal projetado |",
        "|---|---|---|---|---:|",
    ]
    for line in p.lines:
        out.append(
            f"| {line.servico} | {line.unidade} | {line.quantidade} | {line.preco} "
            f"| US$ {line.custo_mensal:.4f} |"
        )
    out.append(f"| **Total** | | | | **US$ {p.total:.4f}** |")
    out += [
        "",
        "Sem nenhuma franquia gratuita (pior caso), a projeção seria "
        f"**US$ {p.total_sem_franquia:.4f}/mês**.",
        f"Nos últimos {window_days} dias, o pipeline faturou {measured_total_bytes / 1e6:.1f} MB "
        "de análise no BigQuery (todos os jobs rotulados `app=radar-alfabetizacao`).",
        "",
        "## Premissas",
        "",
        "- Cronograma e preços em `config/finops_prices.yaml`.",
        "- Execução sem mudança na fonte custa só consultas de metadados e do registro operacional "
        "(mínimo de 10 MiB faturados por consulta).",
        "- Cloud Logging e Cloud Monitoring ficam dentro da franquia gratuita no volume esperado "
        "(logs de poucos KB por execução; não medido).",
    ]
    out += [f"- {note}" for note in p.notes]
    return "\n".join(out) + "\n"
