import json
import os
import subprocess
import sys
import xml.dom.minidom

import pytest

from indickit import bench
from indickit.corpus import PARALLEL
from indickit.llm import Echo, Oracle, make_provider
from indickit.metrics import chrf, digits_match, exact, script_fidelity
from indickit.report import to_markdown, to_svg


def test_chrf_properties():
    assert chrf("ನಮಸ್ಕಾರ", "ನಮಸ್ಕಾರ") == 1.0
    assert chrf("abc", "xyz") == 0.0
    assert 0.0 < chrf("ನಮಸ್ಕಾರ ಸ್ನೇಹಿತರೇ", "ನಮಸ್ಕಾರ ಮಿತ್ರರೇ") < 1.0
    assert chrf("a b c", "abc") == 1.0          # whitespace ignored
    assert chrf("", "") == 1.0 and chrf("", "x") == 0.0
    # closer text scores higher
    ref = PARALLEL["kn"][0]
    assert chrf(ref[:-3], ref) > chrf(ref[:5], ref)


def test_script_fidelity_and_exact():
    assert script_fidelity("ನಮಸ್ಕಾರ", "kannada") == 1.0
    assert script_fidelity("namaskara", "kannada") == 0.0
    assert 0.4 < script_fidelity("ನಮಸ್ಕಾರ hello", "kannada") < 1.0
    assert script_fidelity("123", "kannada") == 0.0
    assert exact("ನಮಸ್ತೇ।", "ನಮಸ್ತೇ") == 1.0
    assert digits_match(" ೨೦೨೪ ", "೨೦೨೪") == 1.0 and digits_match("2024", "೨೦೨೪") == 0.0


def test_task_generation_is_deterministic_and_complete():
    a, b = bench.build_tasks(), bench.build_tasks()
    assert [t.id for t in a] == [t.id for t in b]
    assert len({t.id for t in a}) == len(a)
    assert {t.kind for t in a} == set(bench.KINDS)
    assert not any(t.lang == "ta" and t.kind == "translit" for t in a)   # Tamil excluded by design
    kn = [t for t in a if t.lang == "kn" and t.kind == "numerals"]
    assert kn[1].reference == "೨೦೨೪" and "2024" in kn[1].prompt
    tr = next(t for t in a if t.lang == "hi" and t.kind == "translit" and "namaste" in t.prompt)
    assert tr.reference == "नमस्ते"


def test_filters_and_limit():
    t = bench.build_tasks(["kn", "hi"], ["translate"], limit_per_cell=2)
    assert len(t) == 4 and {x.lang for x in t} == {"kn", "hi"}
    assert bench.build_tasks(["xx"]) == []


def test_oracle_scores_one_and_echo_scores_low():
    tasks = bench.build_tasks()
    ora = bench.run(Oracle(), tasks, workers=2)
    assert all(r["score"] == 1.0 for r in ora["results"] if r["kind"] != "respond")
    table = bench.aggregate(ora)
    assert all(row["overall"] > 0.99 for row in table.values())
    echo = bench.aggregate(bench.run(Echo(), tasks, workers=2))
    assert all(row["overall"] < 0.5 for row in echo.values())


def test_errors_are_scored_zero_and_reported():
    class Boom:
        name = "boom"
        def complete(self, prompt, task=None):
            raise RuntimeError("rate limited")
    data = bench.run(Boom(), bench.build_tasks(["kn"], ["numerals"]))
    assert all(r["score"] == 0.0 and "rate limited" in r["error"] for r in data["results"])
    assert "failed" in to_markdown(data)


def test_response_cleaning_handles_fences_and_quotes():
    t = bench.build_tasks(["kn"], ["numerals"])[1]
    assert bench.score(t, '```\n೨೦೨೪\n```')["score"] == 1.0
    assert bench.score(t, '"೨೦೨೪"')["score"] == 1.0
    assert bench.score(t, "2024")["score"] == 0.0


def test_script_id_accepts_sentence_answers():
    t = next(x for x in bench.build_tasks(["kn"], ["script_id"]))
    assert bench.score(t, "This text is written in the Kannada script.")["score"] == 1.0
    assert bench.score(t, "Devanagari")["score"] == 0.0


def test_report_markdown_and_valid_svg(tmp_path):
    data = bench.run(Oracle(), bench.build_tasks(["kn", "hi"]))
    md = to_markdown(data)
    assert "| Kannada |" in md and "mock-oracle" in md
    svg = to_svg(data)
    xml.dom.minidom.parseString(svg)   # well-formed
    assert "Hindi" in svg and "rgb(" in svg
    path = tmp_path / "r.json"
    bench.save(data, str(path))
    assert bench.load(str(path))["meta"]["model"] == "mock-oracle"


def test_openai_compatible_against_local_server():
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = json.dumps({"choices": [{"message": {"content": "೨೦೨೪"}}]}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        p = make_provider("ollama", "m", f"http://127.0.0.1:{srv.server_port}/v1")
        data = bench.run(p, bench.build_tasks(["kn"], ["numerals"], 3))
        assert data["results"][1]["score"] == 1.0 and data["results"][0]["score"] == 0.0
    finally:
        srv.shutdown()


def test_make_provider_errors():
    with pytest.raises(ValueError, match="--model"):
        make_provider("openai")
    with pytest.raises(ValueError, match="unknown provider"):
        make_provider("nonsense", "m")


def _run(*args, stdin=None, env=None):
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    base_env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if env:
        base_env.update(env)
    existing_pp = base_env.get("PYTHONPATH", "")
    base_env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing_pp}" if existing_pp else src_dir
    return subprocess.run([sys.executable, "-m", "indickit", *args], capture_output=True, text=True, env=base_env, input=stdin)


def test_cli_commands(tmp_path):
    assert "kannada" in _run("detect", "ನಮಸ್ಕಾರ").stdout
    assert _run("translit", "namaste", "--to", "devanagari").stdout.strip() == "नमस्ते"
    assert _run("translit", "ನಮಸ್ತೇ", "--from", "kannada", "--to", "itrans").stdout.strip() == "namaste"
    assert _run("normalize", "೧೨೩", "--digits", "ascii").stdout.strip() == "123"
    assert "graphemes" in _run("stats", "ಕನ್ನಡ").stdout
    tax = _run("tax", "--langs", "kn,hi")
    assert tax.returncode == 0 and "Kannada" in tax.stdout and "1.00x" in tax.stdout
    assert _run("detect", stdin="हिंदी भाषा है").returncode == 0
    r = _run("tax", "--tokenizer", "nope")
    assert r.returncode == 1 and "unknown tokenizer" in r.stderr
    out = tmp_path / "res.json"
    run = _run("bench", "run", "--provider", "mock-oracle", "--langs", "kn", "-o", str(out))
    assert run.returncode == 0 and "Kannada" in run.stdout and out.exists()
    svg = tmp_path / "h.svg"
    rep = _run("bench", "report", str(out), "--svg", str(svg))
    assert rep.returncode == 0 and svg.read_text().startswith("<svg")
