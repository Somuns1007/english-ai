"""Run existing tests against disposable SQLite/JSON copies; production data is read-only."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

with tempfile.TemporaryDirectory(prefix="identity-tests-", ignore_cleanup_errors=True) as directory:
    isolated = Path(directory)
    os.environ["LISTENING_DB_PATH"] = str(isolated / "listening.db")
    os.environ["AUTH_DB_PATH"] = str(isolated / "auth.db")
    # Existing repository switch: only disposable test DBs sacrifice fsync durability.
    os.environ["LISTENING_UNSAFE_FAST_DB"] = "1"
    from listening import expression_service as expressions
    target = isolated / "expressions"
    shutil.copytree(expressions.EXPRESSIONS_DIR, target)
    expressions.EXPRESSIONS_DIR = target
    expressions.EXPRESSIONS_PATH = target / "expressions.json"
    expressions.SCENARIOS_PATH = target / "scenarios.json"
    expressions.AUDIO_INDEX_PATH = target / "audio_index.json"
    expressions.expression_repo.reload()
    # Legacy TTS helper uses its own constants; also keep its output off real data.
    try:
        from listening.tools import generate_scenario_audio as tts
        tts.DATA_DIR = isolated
        tts.SCENARIOS_PATH = expressions.SCENARIOS_PATH
        tts.AUDIO_INDEX_PATH = expressions.AUDIO_INDEX_PATH
        tts.AUDIO_DIR = target / "audio"
    except ModuleNotFoundError:
        pass

    def deny_real_data_writes(event, args):
        if event == "open":
            path, mode, flags = args
            writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename"}:
            path, writing = args[0], True
        else:
            return
        if writing and isinstance(path, (str, bytes)):
            resolved = Path(os.fsdecode(path)).resolve()
            if resolved.is_relative_to(ROOT / "backend" / "listening" / "data"):
                raise RuntimeError(f"Test attempted to modify protected real data: {resolved}")
    sys.addaudithook(deny_real_data_writes)
    import pytest
    os.chdir(ROOT / "backend")
    raise SystemExit(pytest.main([*(sys.argv[1:] or ["tests", "-x"]), "-p", "no:cacheprovider",
                                 "--basetemp", str(isolated / "pytest")]))
