"""Build the clean, default-off Colab entry point from reviewed cells."""

import hashlib
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
cells = []


def cell(kind, source):
    source = textwrap.dedent(source).strip() + "\n"
    result = {"cell_type": kind, "id": hashlib.sha256(source.encode()).hexdigest()[:12],
              "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    cells.append(result)


cell("markdown", """
    # M5 — Riyadh Travel Planner: Gemini and Evaluation

    This notebook connects the preserved baseline prompt and search tools to Gemini,
    saves the response and available trace, then evaluates the itinerary.

    **Default execution makes no Gemini calls.** First upload the current GitHub branch
    ZIP, install the pinned dependencies, and run the offline checks. A live pilot and
    a new 60-run experiment have separate approval switches. No old V1/V2 file is replaced.

    Download the repository branch ZIP from GitHub's **Code → Download ZIP** menu and
    open this notebook in Colab. Use the branch containing this notebook and its code.
    The teammate's original archive is preserved evidence, not the runnable repository ZIP.
""")
cell("code", """
    UPLOAD_REPOSITORY_ZIP = False
    INSTALL_DEPENDENCIES = False
    RUN_OFFLINE_CHECKS = True
    RUN_OFFLINE_DEMO = True
    APPROVE_LIVE_PILOT = False
    APPROVE_FULL_EXPERIMENT = False
    DOWNLOAD_RUNS = False
""")
cell("markdown", """
    ## 1. Load the repository

    In a fresh Colab session, set `UPLOAD_REPOSITORY_ZIP = True`, run the controls cell
    and this cell, then choose the downloaded GitHub repository ZIP. The extraction
    rejects unsafe paths and symlinks. Locally, opening from the repository also works.
""")
cell("code", """
    import os
    from pathlib import Path, PurePosixPath
    import stat
    import sys
    import tempfile
    import zipfile

    if UPLOAD_REPOSITORY_ZIP:
        from google.colab import files
        uploaded = files.upload()
        if len(uploaded) != 1:
            raise ValueError("Upload exactly one repository ZIP")
        name, content = next(iter(uploaded.items()))
        if not name.endswith('.zip') or len(content) > 100_000_000:
            raise ValueError("Expected a repository ZIP under 100 MB")
        destination = Path(tempfile.mkdtemp(prefix='riyadh-m5-'))
        archive_path = destination / 'repository.zip'
        archive_path.write_bytes(content)
        with zipfile.ZipFile(archive_path) as archive:
            if sum(info.file_size for info in archive.infolist()) > 200_000_000:
                raise ValueError("Expanded repository is too large")
            for info in archive.infolist():
                path = PurePosixPath(info.filename)
                if path.is_absolute() or '..' in path.parts or '\\\\' in info.filename:
                    raise ValueError("Unsafe archive member")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError("Symlink archive member")
            archive.extractall(destination)
        candidates = [p.parent for p in destination.rglob('requirements-gemini.txt')
                      if (p.parent / 'm5eval/experiment.py').is_file()]
    else:
        candidates = [Path.cwd(), Path.cwd().parent]
    matches = [p.resolve() for p in candidates if (p / 'm5eval/experiment.py').is_file()]
    if len(set(matches)) != 1:
        raise RuntimeError("Load the repository ZIP first, or open from its root directory")
    PROJECT_ROOT = matches[0]
    os.chdir(PROJECT_ROOT)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    print('Repository:', PROJECT_ROOT)
""")
cell("markdown", """
    ## 2. Install and check

    Set `INSTALL_DEPENDENCIES = True` for the first Colab setup. Installation downloads
    Python packages but does not call Gemini. If the runtime has already imported a
    different SDK/NumPy/pandas version, restart the session after installation and reload
    the repository before proceeding. Never paste an API key into a code cell or this chat.
""")
cell("code", """
    import subprocess

    if INSTALL_DEPENDENCIES:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-gemini.txt'], check=True)
    if RUN_OFFLINE_CHECKS:
        subprocess.run([sys.executable, 'scripts/run_checks.py'], check=True)
    print('No live Gemini call was requested by this cell.')
""")
cell("markdown", """
    ## 3. Offline full-path demonstration

    The fixture uses the real local search tools, record writer and scorer. Its answer
    is deliberately constructed test data, not an LLM response. Its files are labelled
    `fixture` and must never be reported as experimental model results.
""")
cell("code", """
    from m5eval.demo import run_demo
    from m5eval.experiment import Experiment, RunSettings, golden_cases
    from m5eval.generation import DEFAULT_MODEL, GeminiBackend

    RUNS_ROOT = PROJECT_ROOT / 'runs'
    if RUN_OFFLINE_DEMO:
        demo = run_demo(RUNS_ROOT)
        print(demo['status'])
        print(demo['scores'])
        print('Fixture record:', demo['record_directory'])
""")
cell("markdown", """
    ## 4. One live pilot — requires approval

    Add `GEMINI_API_KEY` using Colab's Secrets panel and grant this notebook access.
    On a local computer, the same environment-variable name is supported.

    Only after the project lead approves the pilot, set `APPROVE_LIVE_PILOT = True`.
    Scope: G01, seed 11, one generation attempt, at most four HTTP requests and a
    30-second timeout per request. Tool use can require more than one HTTP request.
    These are request limits, not a guaranteed monetary spending cap. The model is
    the historical model ID; a 404 stops without switching models.

    Re-running a completed pilot reads its saved record. It does not spend again.
    An incomplete run requires inspection and a separately authorized recovery version.
""")
cell("code", """
    def read_api_key():
        try:
            from google.colab import userdata
        except ImportError:
            value = os.environ.get('GEMINI_API_KEY')
        else:
            value = userdata.get('GEMINI_API_KEY')
        if not value:
            raise RuntimeError('Add GEMINI_API_KEY to Colab Secrets or the local environment')
        return value

    PILOT_VERSION = 'pilot-v3-20261107'
    if APPROVE_LIVE_PILOT:
        backend = GeminiBackend(read_api_key(), allow_live=True, max_http_requests=4, timeout_ms=30000)
        try:
            pilot = Experiment(RUNS_ROOT, PILOT_VERSION, [golden_cases()[0]], [11], backend,
                               settings=RunSettings(model=DEFAULT_MODEL, max_attempts=1))
            record = pilot.run_case('G01', 11)
            print('Generation parsed:', record['generation_success'])
            print('Evaluation:', record['evaluation'])
            print('Record:', pilot.root / 'G01_seed11/record.json')
            if not record['generation_success']:
                print('Stopped. Inspect the saved error; do not change the model or repeat failures silently.')
        finally:
            backend.close()
    else:
        print('Live pilot is OFF. No API key was read and no Gemini request was sent.')
""")
cell("markdown", """
    ## 5. New baseline experiment — separate approval

    This is a new V3 experiment, not recovery or replacement of V2. It uses all twenty
    unchanged golden cases and seeds 11, 22 and 33. Do not start it until the model,
    cost and comparison protocol have been approved.

    With approval, set `APPROVE_FULL_EXPERIMENT = True`. Each execution starts at most
    `MAX_NEW_RUNS` new records. The default chunk is three runs, each with up to three
    outer attempts and ten SDK remote calls per attempt. The HTTP cap applies to this
    client/chunk. Twelve-second pauses between new records reduce request bursts;
    they do not guarantee quota availability. Rate/auth/model/service failures stop the chunk; failed records remain
    in the cohort. Re-running resumes unstarted pairs without replacing saved failures.
""")
cell("code", """
    FULL_VERSION = 'baseline-v3-20261107'
    MAX_NEW_RUNS = 3
    CHUNK_HTTP_CAP = 90
    full_experiment = None
    if APPROVE_FULL_EXPERIMENT:
        import time
        backend = GeminiBackend(read_api_key(), allow_live=True,
                                max_http_requests=CHUNK_HTTP_CAP, timeout_ms=30000)
        try:
            full_experiment = Experiment(RUNS_ROOT, FULL_VERSION, golden_cases(), [11, 22, 33], backend,
                                         settings=RunSettings(model=DEFAULT_MODEL))
            new_records = []
            for run_index in range(MAX_NEW_RUNS):
                if run_index:
                    time.sleep(12)
                batch = full_experiment.run_batch(max_new_runs=1)
                new_records.extend(batch)
                if not batch:
                    break
                error = batch[-1]['generation_result'].get('generation_error') or {}
                if not batch[-1]['generation_success'] and error.get('type') in ('ProviderFailure', 'RequestBudgetExceeded'):
                    break
            print('New records this chunk:', len(new_records))
            print('All saved failures are retained. Inspect error records before proceeding.')
            completed = list(full_experiment.root.glob('G*_seed*/record.json'))
            print('Saved records:', len(completed), '/ 60')
            if len(completed) == 60:
                import json
                summary = full_experiment.summary()
                summary_path = full_experiment.root / 'summary.json'
                if not summary_path.exists():
                    from m5eval.records import save_record
                    save_record(summary_path, summary)
                print('Complete-cohort summary:', summary_path)
        finally:
            backend.close()
    else:
        print('Full experiment is OFF. No Gemini requests were sent.')
""")
cell("markdown", """
    ## 6. Download evidence

    Colab's local storage is temporary. Download completed and incomplete run evidence
    before ending the runtime. The ZIP includes manifests, raw/sanitized responses,
    journals, full records, checksums and any cohort summary. Inspect it for sensitive
    information before sharing. Do not upload new results over historical V1/V2 files.
""")
cell("code", """
    if DOWNLOAD_RUNS:
        import shutil
        from google.colab import files
        if not RUNS_ROOT.is_dir():
            raise RuntimeError('There are no saved runs to download')
        archive = shutil.make_archive(str(PROJECT_ROOT / 'm5_run_evidence'), 'zip', RUNS_ROOT)
        files.download(archive)
    else:
        print('Download is OFF. Enable it after inspecting the saved run directory.')
""")

notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
             "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
destination = ROOT / "notebooks/M5_Colab_Run.ipynb"
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(destination)
