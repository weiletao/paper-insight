import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from paper_insight.converters.base import DocumentConverter
from paper_insight.utils.logger import get_logger

logger = get_logger()

# flash-extract limits input to 20 pages per call.
PAGE_CHUNK_SIZE = 20

# Candidate locations for the mineru-open-api binary.
_TOOL_CANDIDATES = [
    "mineru-open-api",
    Path.home() / ".local" / "bin" / "mineru-open-api",
    Path.home() / ".local" / "nodemodules" / "node_modules" / "mineru-open-api" / "bin" / "mineru-open-api",
    Path.home() / ".local" / "nodemodules" / "node_modules" / "mineru-open-api-linux-x64" / "bin" / "mineru-open-api",
]


def _resolve_mineru_path() -> str:
    """Return the absolute path to the mineru-open-api binary."""
    for candidate in _TOOL_CANDIDATES:
        if isinstance(candidate, Path):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return "mineru-open-api"


class MinerUConverter(DocumentConverter):
    """Convert PDF to markdown via mineru-open-api CLI."""

    def convert(self, input_path: str, output_path: str) -> str:
        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise FileNotFoundError(f"PDF not found: {input_path}")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converting {input_file.name} ...")

        self._run_convert(str(input_file), str(output_file))

        logger.info(f"Saved to: {output_file}")
        return str(output_file)

    def _run_convert(self, input_path: str, output_path: str) -> None:
        try:
            self._call_mineru(input_path, output_path)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or ""
            if "exceeds" not in stderr or "page" not in stderr:
                raise RuntimeError(f"Conversion failed:\n{stderr.strip()}") from exc

            logger.info("PDF exceeds 20-page limit, converting in chunks ...")
            self._convert_in_chunks(input_path, output_path)

    def _convert_in_chunks(self, input_path: str, output_path: str) -> None:
        tmp_dir = tempfile.mkdtemp(prefix="mineru_")
        chunk_paths: list[Path] = []

        page = 1
        chunk_idx = 0
        while True:
            end_page = page + PAGE_CHUNK_SIZE - 1
            chunk_file = Path(tmp_dir) / f"chunk_{chunk_idx}.md"

            try:
                self._call_mineru(
                    input_path,
                    str(chunk_file),
                    extra_args=["--pages", f"{page}-{end_page}"],
                )
            except subprocess.CalledProcessError:
                if chunk_file.exists() and chunk_file.stat().st_size > 0:
                    chunk_paths.append(chunk_file)
                break

            if chunk_file.exists() and chunk_file.stat().st_size > 0:
                chunk_paths.append(chunk_file)
            else:
                break

            page = end_page + 1
            chunk_idx += 1

        # Merge all chunks into the final output.
        with open(output_path, "w") as out:
            for i, chunk in enumerate(chunk_paths):
                if i > 0:
                    out.write("\n\n")
                out.write(chunk.read_text())

        shutil.rmtree(tmp_dir, ignore_errors=True)

    def _call_mineru(
        self, input_path: str, output_path: str, extra_args: list[str] | None = None
    ) -> None:
        tool = _resolve_mineru_path()
        cmd = [
            tool,
            "flash-extract",
            input_path,
            "-o",
            output_path,
        ]
        if extra_args:
            cmd.extend(extra_args)

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except FileNotFoundError:
            raise RuntimeError(
                "mineru-open-api is not installed. "
                "Install it with: uv tool install mineru-open-api"
            ) from None
