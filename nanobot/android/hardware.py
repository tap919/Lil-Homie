"""Android hardware detection for Lil Homie adaptive mode selection.

Reads device specs from Android system interfaces:
- /proc/meminfo for RAM
- /proc/cpuinfo for CPU core count
- getprop for SoC model (NPU detection) and Android version
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class DeviceMode(str, Enum):
    """Operating mode selected based on detected hardware capabilities."""

    FULL = "full"
    """Flagship device: full cron/tools, local LLM, FFmpeg/video support."""

    BASIC = "basic"
    """Mid-range device: text-only promos, limited cron, cloud LLM fallback."""

    UNSUPPORTED = "unsupported"
    """Insufficient RAM: chat-only, no cron/tools."""


@dataclass
class HardwareInfo:
    """Detected hardware specification of the current device."""

    ram_gb: float = 0.0
    """Total RAM in gigabytes."""

    cpu_cores: int = 0
    """Number of logical CPU cores (from /proc/cpuinfo)."""

    npu_present: bool = False
    """True when a Neural Processing Unit is detected via SoC model string."""

    android_version: int = 0
    """Major Android version number (e.g. 14 for Android 14)."""

    soc_model: str = ""
    """Raw SoC model string from ``getprop ro.soc.model`` or ``ro.hardware``."""

    storage_gb: float = 0.0
    """Available internal storage in gigabytes (best-effort, 0 if unavailable)."""

    raw: dict[str, str] = field(default_factory=dict)
    """Raw key→value pairs collected during detection (for diagnostics)."""


# ---------------------------------------------------------------------------
# Low-level readers — each accepts an optional override for unit-testing
# ---------------------------------------------------------------------------

def _read_proc_meminfo(path: str = "/proc/meminfo") -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_proc_cpuinfo(path: str = "/proc/cpuinfo") -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _run_getprop(key: str, runner: Callable[[list[str]], str] | None = None) -> str:
    """Run ``getprop <key>`` and return the trimmed output."""
    if runner is not None:
        return runner(["getprop", key])
    try:
        result = subprocess.run(
            ["getprop", key],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_NPU_KEYWORDS = re.compile(
    r"snapdragon\s+8\s+(elite|gen\s*[3-9])|dimensity\s+9[0-9]{3}|kirin\s+9[0-9]{2}|"
    r"exynos\s+2[0-9]{3}|apple\s+m|tensor\s+g[3-9]|nuvia",
    re.IGNORECASE,
)


def _parse_ram_gb(meminfo: str) -> float:
    """Return total RAM in GB from /proc/meminfo content."""
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    kb = float(parts[1])
                    return kb / (1024 * 1024)
                except ValueError:
                    pass
    return 0.0


def _parse_cpu_cores(cpuinfo: str) -> int:
    """Return the number of logical CPU cores from /proc/cpuinfo content."""
    return len(re.findall(r"^processor\s*:", cpuinfo, re.MULTILINE))


def _has_npu(soc_model: str) -> bool:
    """Return True when the SoC model string matches a known NPU-capable chip."""
    return bool(_NPU_KEYWORDS.search(soc_model))


def _parse_android_version(version_str: str) -> int:
    """Return the major Android version as an integer."""
    try:
        return int(version_str.split(".")[0])
    except (ValueError, IndexError):
        return 0


def _parse_storage_gb(path: str = "/storage/emulated/0") -> float:
    """Return available storage in GB using statvfs (best-effort)."""
    try:
        import os
        st = os.statvfs(path)
        return (st.f_bavail * st.f_frsize) / (1024 ** 3)
    except OSError:
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_hardware(
    *,
    meminfo_path: str = "/proc/meminfo",
    cpuinfo_path: str = "/proc/cpuinfo",
    storage_path: str = "/storage/emulated/0",
    getprop_runner: Callable[[list[str]], str] | None = None,
) -> HardwareInfo:
    """Detect device hardware and return a :class:`HardwareInfo` instance.

    All parameters are injectable for testing on non-Android systems.

    Args:
        meminfo_path: Path to the meminfo pseudo-file.
        cpuinfo_path: Path to the cpuinfo pseudo-file.
        storage_path: Path used for statvfs storage measurement.
        getprop_runner: Callable that accepts a ``getprop`` argument list and
            returns the property value as a string.  When *None* the real
            ``getprop`` binary is invoked.

    Returns:
        Populated :class:`HardwareInfo` dataclass.
    """
    meminfo = _read_proc_meminfo(meminfo_path)
    cpuinfo = _read_proc_cpuinfo(cpuinfo_path)

    soc_model = _run_getprop("ro.soc.model", getprop_runner)
    if not soc_model:
        soc_model = _run_getprop("ro.hardware", getprop_runner)

    android_version_str = _run_getprop("ro.build.version.release", getprop_runner)

    ram_gb = _parse_ram_gb(meminfo)
    cpu_cores = _parse_cpu_cores(cpuinfo)
    npu_present = _has_npu(soc_model)
    android_version = _parse_android_version(android_version_str)
    storage_gb = _parse_storage_gb(storage_path)

    return HardwareInfo(
        ram_gb=ram_gb,
        cpu_cores=cpu_cores,
        npu_present=npu_present,
        android_version=android_version,
        soc_model=soc_model,
        storage_gb=storage_gb,
        raw={
            "ro.soc.model": soc_model,
            "ro.build.version.release": android_version_str,
        },
    )


def select_mode(info: HardwareInfo) -> DeviceMode:
    """Select the appropriate operating mode for the given hardware.

    Decision table (evaluated top-to-bottom):

    +--------------+------------+----------+------+----------------+
    | RAM (GB)     | CPU cores  | NPU      | OS   | Mode           |
    +==============+============+==========+======+================+
    | >= 12        | >= 8       | present  | >=14 | **full**       |
    +--------------+------------+----------+------+----------------+
    | >= 6 (< 12)  | >= 6       | —        | —    | **basic**      |
    +--------------+------------+----------+------+----------------+
    | anything     | anything   | —        | —    | **unsupported**|
    +--------------+------------+----------+------+----------------+

    Args:
        info: Detected hardware information.

    Returns:
        The selected :class:`DeviceMode`.
    """
    if (
        info.ram_gb >= 12
        and info.cpu_cores >= 8
        and info.npu_present
        and info.android_version >= 14
    ):
        return DeviceMode.FULL

    if info.ram_gb >= 6 and info.cpu_cores >= 6:
        return DeviceMode.BASIC

    return DeviceMode.UNSUPPORTED
