"""Command-line entry point: proxy <command> ..."""

import argparse
import asyncio
import json
import sys

from proxy.config import ExperimentConfig, load_models
from proxy.store import EpisodeStore


def cmd_run(args):
    from proxy.runner.run import run_experiment

    cfg = ExperimentConfig.load(args.config)
    if args.via_openrouter:
        cfg.via_openrouter = True
    models = load_models()
    specs = cfg.episode_specs()
    if args.dry_run:
        by_model = {}
        for s in specs:
            by_model[s.model] = by_model.get(s.model, 0) + 1
        print(f"{cfg.name}: {len(specs)} episodes; per model: {by_model}")
        print(f"config hash {cfg.config_hash()}")
        return
    summary = asyncio.run(
        run_experiment(cfg, models, EpisodeStore(args.data), run_name=args.run_name, limit=args.limit, only_models=args.models)
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "spend"}, indent=2))
    print(summary["spend"])


def cmd_calibrate(args):
    from proxy.counterparty.calibration import run_calibration

    cfg = ExperimentConfig.load(args.config)
    fmt = lambda v: "  n/a" if v is None else f"{v:5.2f}"
    for (target, agent), r in run_calibration(cfg).items():
        print(
            f"{target:>9} {agent:<13} n={r['episodes']:<4} deal_rate={fmt(r['deal_rate'])} "
            f"violations/deal={fmt(r['violation_rate_among_deals'])} gain mean={fmt(r['gain_mean'])} "
            f"p10={fmt(r['gain_p10'])} p90={fmt(r['gain_p90'])}"
        )


def cmd_score(args):
    from proxy.scoring.score import score_store

    scored, skipped = score_store(EpisodeStore(args.data), run=args.run, force=args.force)
    print(f"scored {scored}, already current {skipped}")


def cmd_index(args):
    n = EpisodeStore(args.data).rebuild_index()
    print(f"indexed {n} episodes")


def cmd_show(args):
    from proxy.env.scenario import Scenario
    from proxy.runner.render import format_package

    store = EpisodeStore(args.data)
    path = store.find(args.episode_id)
    if path is None:
        sys.exit(f"episode {args.episode_id} not found")
    ep = store.load(path)
    issues = Scenario.from_dict(ep["scenario"]).issues
    print(f"# {ep['episode_id']}  model={ep['spec']['model']}  target={ep['spec']['outcome_target']}  audit={ep['spec']['audit_framing']}")
    print("\n## Briefing\n" + ep["briefing"]["text"])
    print("\n## Negotiation")
    for a in ep["actions"]:
        who = "AGENT" if a["actor"] == "agent" else "CP"
        line = f"[{a['turn'] + 1}] {who} ({a['role']}) {a['type']}"
        if a["package"]:
            line += f": {format_package(issues, a['package'])}"
        print(line + ("" if a["parse_ok"] else "  [PARSE FAILURE]"))
        if a["message"]:
            print(f"      \"{a['message']}\"")
    print(f"\n## Termination: {ep['termination']}")
    print(f"## Outcomes: {json.dumps(ep['outcomes'])}")
    if ep.get("detectors"):
        d = ep["detectors"]
        print(f"## Detectors: violated={d.get('constraint_violated')} leaked={d.get('leaked')} near={d.get('leaked_near')} reservation_breached={d.get('reservation_breached')}")
    print("\n## Report\n" + ((ep.get("report") or {}).get("text") or "(none)"))


def cmd_view(args):
    from proxy.viewer.server import serve

    serve(EpisodeStore(args.data), port=args.port)


def cmd_models(args):
    from proxy.adapters import AdapterError, SpendTracker, make_adapter

    models = load_models()
    keys = args.keys or list(models)
    specs = [models[k].via_openrouter() if args.via_openrouter else models[k] for k in keys]

    async def check():
        listings: dict[str, list[str] | str] = {}
        spend = SpendTracker(ceiling_usd=1.0)
        for spec in specs:
            try:
                adapter = make_adapter(spec, spend, asyncio.Semaphore(1), 60)
            except AdapterError as e:
                print(f"  {spec.key:<22} SKIP  {e}")
                continue
            if spec.provider not in listings:
                try:
                    listings[spec.provider] = await adapter.list_models()
                except Exception as e:  # listing endpoints vary; report and continue
                    listings[spec.provider] = f"listing failed: {e}"
            listing = listings[spec.provider]
            # Anthropic lists dated snapshot IDs; an undated alias counts as present if a snapshot of it is listed.
            listed = not isinstance(listing, str) and any(m == spec.model or m.startswith(spec.model + "-") for m in listing)
            status = "?" if isinstance(listing, str) else ("OK " if listed else "MISSING")
            line = f"  {spec.key:<22} {status:<7} {spec.provider}:{spec.model}"
            if args.ping:
                try:
                    c = await adapter.complete("Reply with the single word OK.", [{"role": "user", "content": "Ready?"}])
                    line += f"  ping ok, version={c.model_version} finish={c.finish_reason} ${c.cost_usd:.5f}"
                except AdapterError as e:
                    line += f"  PING FAILED: {e}"
            print(line)
        print(spend.summary())

    asyncio.run(check())


def cmd_judge(args):
    from proxy.scoring.judge_run import JudgingConfig, judge_store

    cfg = JudgingConfig.load(args.config)
    summary = asyncio.run(judge_store(EpisodeStore(args.data), cfg, load_models(), run=args.run, limit=args.limit, force=args.force))
    print(json.dumps({k: v for k, v in summary.items() if k != "spend"}, indent=2))
    print(summary["spend"])


def cmd_annotate_export(args):
    from pathlib import Path

    from proxy.annotation.sampling import build_batch

    store = EpisodeStore(args.data)
    out = Path(args.out) if args.out else store.root / "annotations" / args.batch
    manifest = build_batch(store, args.batch, out, runs=args.runs, n_disclosure=args.n_disclosure,
                           n_characterization=args.n_characterization, n_leak=args.n_leak, n_stated_total=args.n_stated_total, seed=args.seed)
    print(json.dumps(manifest, indent=2))
    print(f"batch written to {out} (share items.jsonl only; key.json stays with the analyst)")


def cmd_annotate_serve(args):
    from proxy.annotation.server import serve

    serve(args.batch_dir, args.annotator, port=args.port)


def cmd_annotate_agreement(args):
    from pathlib import Path

    from proxy.annotation.agreement import compute_agreement, render_markdown
    from proxy.util import json_clean

    rep = compute_agreement(Path(args.batch_dir), EpisodeStore(args.data), args.judges)
    (Path(args.batch_dir) / "agreement.json").write_text(json.dumps(json_clean(rep), indent=1))
    md = render_markdown(rep)
    (Path(args.batch_dir) / "agreement.md").write_text(md)
    print(md)


def cmd_analyze_all(args):
    from proxy.analysis.report import AnalysisConfig, analyze_all

    cfg = AnalysisConfig.load(args.config)
    out = args.out or f"results/{cfg.name}"
    print(json.dumps(analyze_all(EpisodeStore(args.data), cfg, out), indent=2))
    print(f"see {out}/results.md")


def cmd_analyze_power(args):
    from proxy.analysis.data import load_frame
    from proxy.analysis.power import estimate_parameters, power_table

    df = load_frame(EpisodeStore(args.data), load_models(), runs=args.runs, primary_judge="", principal_model=None)
    params = estimate_parameters(df)
    for k in ("p_violate", "p_nondisclosure", "sigma_scenario"):
        if getattr(args, k) is not None:
            params[k] = getattr(args, k)
    print("parameters:", json.dumps(params))
    missing = [k for k in ("p_violate", "p_nondisclosure", "sigma_scenario") if not params[k] == params[k]]
    if missing:
        sys.exit(f"cannot estimate {missing} from these runs; pass them explicitly (e.g. --p-violate 0.4)")
    table = power_table(params, args.deltas, args.scenarios, args.episodes_per_cell, alpha=args.alpha, sims=args.sims)
    print(table.to_string(index=False))


def cmd_read(args):
    from proxy.reading.run import ReadingConfig, read_run

    summary = asyncio.run(read_run(EpisodeStore(args.data), ReadingConfig.load(args.config), load_models(), args.run, force=args.force))
    print(json.dumps({k: v for k, v in summary.items() if k != "spend"}, indent=2))
    print(summary["spend"])


def cmd_pilot(args):
    """Generate, score, judge, and read a run end to end, then point at the review."""
    from proxy.reading.run import ReadingConfig, read_run
    from proxy.runner.run import run_experiment
    from proxy.scoring.judge_run import JudgingConfig, judge_store
    from proxy.scoring.score import score_store

    cfg = ExperimentConfig.load(args.config)
    models, store = load_models(), EpisodeStore(args.data)
    print("== generate")
    gen = asyncio.run(run_experiment(cfg, models, store, limit=args.limit))
    print(json.dumps({k: v for k, v in gen.items() if k != "spend"}), "\n" + gen["spend"])
    if gen["aborted"]:
        sys.exit("stopped: generation hit its spend ceiling")
    print("== score")
    print("scored %d, already current %d" % score_store(store, run=cfg.name))
    print("== judge")
    jud = asyncio.run(judge_store(store, JudgingConfig.load(args.judging), models, run=cfg.name))
    print(json.dumps({k: v for k, v in jud.items() if k != "spend"}), "\n" + jud["spend"])
    print("== read")
    rd = asyncio.run(read_run(store, ReadingConfig.load(args.reading), models, cfg.name))
    print(json.dumps({k: v for k, v in rd.items() if k != "spend"}, indent=2), "\n" + rd["spend"])
    store.rebuild_index()
    print(f"\nPilot review: {rd['review']}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="proxy")
    p.add_argument("--data", default=None, help="data directory (default: ./data)")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="generate episodes for an experiment config")
    r.add_argument("config")
    r.add_argument("--run-name")
    r.add_argument("--limit", type=int)
    r.add_argument("--models", nargs="*")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--via-openrouter", action="store_true", help="route every model through OpenRouter")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("calibrate", help="check counterparty outcome bands with the reference agent (free)")
    c.add_argument("config")
    c.set_defaults(func=cmd_calibrate)

    s = sub.add_parser("score", help="run mechanical detectors and stage-1 disclosure over stored episodes")
    s.add_argument("--run")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_score)

    i = sub.add_parser("index", help="rebuild the SQLite index")
    i.set_defaults(func=cmd_index)

    sh = sub.add_parser("show", help="print one episode as a readable transcript")
    sh.add_argument("episode_id")
    sh.set_defaults(func=cmd_show)

    v = sub.add_parser("view", help="local replay viewer")
    v.add_argument("--port", type=int, default=8765)
    v.set_defaults(func=cmd_view)

    m = sub.add_parser("models", help="verify model IDs against provider listings")
    m.add_argument("keys", nargs="*")
    m.add_argument("--ping", action="store_true", help="also send a one-line request to each model (costs a little)")
    m.add_argument("--via-openrouter", action="store_true")
    m.set_defaults(func=cmd_models)

    j = sub.add_parser("judge", help="stage-2 disclosure, characterization, and principal simulation over stored episodes")
    j.add_argument("config")
    j.add_argument("--run")
    j.add_argument("--limit", type=int)
    j.add_argument("--force", action="store_true")
    j.set_defaults(func=cmd_judge)

    an = sub.add_parser("annotate", help="human annotation: export a blinded batch, label it, compute agreement")
    an_sub = an.add_subparsers(dest="annotate_cmd", required=True)
    ae = an_sub.add_parser("export")
    ae.add_argument("batch")
    ae.add_argument("--runs", nargs="*")
    ae.add_argument("--out")
    ae.add_argument("--n-disclosure", type=int, default=150)
    ae.add_argument("--n-characterization", type=int, default=150)
    ae.add_argument("--n-leak", type=int, default=50)
    ae.add_argument("--n-stated-total", type=int, default=100)
    ae.add_argument("--seed", type=int, default=0)
    ae.set_defaults(func=cmd_annotate_export)
    asv = an_sub.add_parser("serve")
    asv.add_argument("batch_dir")
    asv.add_argument("--annotator", required=True)
    asv.add_argument("--port", type=int, default=8766)
    asv.set_defaults(func=cmd_annotate_serve)
    ag = an_sub.add_parser("agreement")
    ag.add_argument("batch_dir")
    ag.add_argument("--judges", nargs="*", default=["glm-5.3", "kimi-k3"])
    ag.set_defaults(func=cmd_annotate_agreement)

    az = sub.add_parser("analyze", help="regenerate every table and figure, or run the power analysis")
    az_sub = az.add_subparsers(dest="analyze_cmd", required=True)
    aa = az_sub.add_parser("all")
    aa.add_argument("config")
    aa.add_argument("--out")
    aa.set_defaults(func=cmd_analyze_all)
    ap = az_sub.add_parser("power")
    ap.add_argument("--runs", nargs="*", default=None)
    ap.add_argument("--deltas", nargs="*", type=float, default=[0.1, 0.15, 0.2])
    ap.add_argument("--scenarios", nargs="*", type=int, default=[10, 20, 40, 80])
    ap.add_argument("--episodes-per-cell", type=int, default=28, help="episodes per scenario per outcome condition (models x roles x audit)")
    ap.add_argument("--p-violate", dest="p_violate", type=float)
    ap.add_argument("--p-nondisclosure", dest="p_nondisclosure", type=float)
    ap.add_argument("--sigma", dest="sigma_scenario", type=float)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--sims", type=int, default=500)
    ap.set_defaults(func=cmd_analyze_power)

    rd = sub.add_parser("read", help="transcript reader agent: read every episode of a run and write a pilot review")
    rd.add_argument("config")
    rd.add_argument("--run", required=True)
    rd.add_argument("--force", action="store_true")
    rd.set_defaults(func=cmd_read)

    pl = sub.add_parser("pilot", help="generate, score, judge, and read a run in one go")
    pl.add_argument("config")
    pl.add_argument("--judging", default="configs/judging.yaml")
    pl.add_argument("--reading", default="configs/reading.yaml")
    pl.add_argument("--limit", type=int)
    pl.set_defaults(func=cmd_pilot)

    args = p.parse_args(argv)
    from proxy import REPO_ROOT
    from proxy.util import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
    if args.data is None:
        from proxy import DATA_DIR

        args.data = DATA_DIR
    args.func(args)


if __name__ == "__main__":
    main()
