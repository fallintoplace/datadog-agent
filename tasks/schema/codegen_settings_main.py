"""
Bazel entry point: replicates `dda inv schema.codegen --keep-orig-order`.

Usage: codegen_settings_main.py <output_dir>

Intended to be called from a Bazel run_binary action. The working directory
must be the Bazel execroot so that workspace-relative paths such as
  pkg/config/schema/yaml/core_schema.yaml
  pkg/config/setup/apm_settings.go          (ordering hints)
resolve to their declared inputs.

Writes generated *_settings.go files into <output_dir>.  The caller
(run_binary) must declare those files as outputs in its `outs` list.
"""

import sys

from tasks.schema.codegen_init_settings import run_codegen
from tasks.schema.merge_schema import resolve_schema
from tasks.schema.settings_source_analyzer import extract_imperative_code_hints


def _filter(expect, filename):
    """Return a predicate that accepts (expect=True) or rejects (expect=False) filename."""
    def comparator(othername):
        return (filename == othername) == expect
    return comparator


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output_dir>", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]

    # Paths are workspace-relative; they resolve correctly when the cwd is the
    # Bazel execroot, where all declared srcs are available as symlinks.
    core_schema = resolve_schema("pkg/config/schema/yaml/core_schema.yaml")
    system_probe_schema = resolve_schema("pkg/config/schema/yaml/system-probe_schema.yaml")

    # Extract ordering hints from the existing *_settings.go files (pkg/config/setup/).
    # These tell run_codegen which function goes in which file (--keep-orig-order).
    hints = extract_imperative_code_hints()

    # Core agent settings: every file except system_probe_settings.go
    run_codegen(core_schema, _filter(False, "system_probe_settings.go"), hints, True, output_dir)
    # System-probe settings: only system_probe_settings.go
    run_codegen(system_probe_schema, _filter(True, "system_probe_settings.go"), hints, True, output_dir)


if __name__ == "__main__":
    main()
