"""Tests for Android hardware detection and mode selection."""

from nanobot.android.hardware import (
    DeviceMode,
    HardwareInfo,
    _has_npu,
    _parse_android_version,
    _parse_cpu_cores,
    _parse_ram_gb,
    detect_hardware,
    select_mode,
)

# ---------------------------------------------------------------------------
# Unit tests for parsing helpers
# ---------------------------------------------------------------------------

MEMINFO_16GB = """\
MemTotal:       16777216 kB
MemFree:         8000000 kB
MemAvailable:   10000000 kB
"""

MEMINFO_8GB = """\
MemTotal:        8388608 kB
MemFree:         3000000 kB
"""

MEMINFO_4GB = """\
MemTotal:        4194304 kB
MemFree:         1000000 kB
"""

MEMINFO_EMPTY = ""


def _cpuinfo(cores: int) -> str:
    """Build a synthetic /proc/cpuinfo with the given number of processors."""
    return "\n".join(
        f"processor\t: {i}\nmodel name\t: ARMv8\n" for i in range(cores)
    )


def test_parse_ram_gb_16gb():
    assert _parse_ram_gb(MEMINFO_16GB) == 16.0


def test_parse_ram_gb_8gb():
    assert abs(_parse_ram_gb(MEMINFO_8GB) - 8.0) < 0.01


def test_parse_ram_gb_4gb():
    assert abs(_parse_ram_gb(MEMINFO_4GB) - 4.0) < 0.01


def test_parse_ram_gb_empty():
    assert _parse_ram_gb(MEMINFO_EMPTY) == 0.0


def test_parse_cpu_cores_8():
    assert _parse_cpu_cores(_cpuinfo(8)) == 8


def test_parse_cpu_cores_4():
    assert _parse_cpu_cores(_cpuinfo(4)) == 4


def test_parse_cpu_cores_zero_on_empty():
    assert _parse_cpu_cores("") == 0


def test_has_npu_snapdragon_elite():
    assert _has_npu("Snapdragon 8 Elite") is True


def test_has_npu_snapdragon_gen3():
    assert _has_npu("Snapdragon 8 Gen 3") is True


def test_has_npu_dimensity():
    assert _has_npu("Dimensity 9300") is True


def test_has_npu_tensor_g4():
    assert _has_npu("Tensor G4") is True


def test_has_npu_exynos():
    assert _has_npu("Exynos 2400") is True


def test_has_npu_mid_range_false():
    assert _has_npu("Snapdragon 695") is False


def test_has_npu_empty_false():
    assert _has_npu("") is False


def test_parse_android_version_14():
    assert _parse_android_version("14") == 14


def test_parse_android_version_with_patch():
    assert _parse_android_version("14.1.2") == 14


def test_parse_android_version_empty():
    assert _parse_android_version("") == 0


# ---------------------------------------------------------------------------
# Unit tests for select_mode
# ---------------------------------------------------------------------------


def _make_info(
    ram_gb: float,
    cpu_cores: int,
    npu_present: bool = False,
    android_version: int = 0,
) -> HardwareInfo:
    return HardwareInfo(
        ram_gb=ram_gb,
        cpu_cores=cpu_cores,
        npu_present=npu_present,
        android_version=android_version,
    )


def test_select_mode_full_flagship():
    info = _make_info(ram_gb=16.0, cpu_cores=8, npu_present=True, android_version=14)
    assert select_mode(info) == DeviceMode.FULL


def test_select_mode_full_minimum_threshold():
    info = _make_info(ram_gb=12.0, cpu_cores=8, npu_present=True, android_version=14)
    assert select_mode(info) == DeviceMode.FULL


def test_select_mode_basic_mid_range():
    info = _make_info(ram_gb=8.0, cpu_cores=6, android_version=12)
    assert select_mode(info) == DeviceMode.BASIC


def test_select_mode_basic_no_npu():
    """Full-mode RAM/cores but no NPU → basic."""
    info = _make_info(ram_gb=12.0, cpu_cores=8, npu_present=False, android_version=14)
    assert select_mode(info) == DeviceMode.BASIC


def test_select_mode_basic_old_android():
    """Full-mode RAM/cores/NPU but Android 13 → basic."""
    info = _make_info(ram_gb=12.0, cpu_cores=8, npu_present=True, android_version=13)
    assert select_mode(info) == DeviceMode.BASIC


def test_select_mode_unsupported_low_ram():
    info = _make_info(ram_gb=4.0, cpu_cores=4)
    assert select_mode(info) == DeviceMode.UNSUPPORTED


def test_select_mode_unsupported_low_cores():
    info = _make_info(ram_gb=8.0, cpu_cores=4)
    assert select_mode(info) == DeviceMode.UNSUPPORTED


def test_select_mode_unsupported_zero_specs():
    info = _make_info(ram_gb=0.0, cpu_cores=0)
    assert select_mode(info) == DeviceMode.UNSUPPORTED


# ---------------------------------------------------------------------------
# Integration-style test for detect_hardware with injected data
# ---------------------------------------------------------------------------


def test_detect_hardware_flagship(tmp_path):
    """detect_hardware returns correct HardwareInfo for a flagship-spec device."""
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(MEMINFO_16GB, encoding="utf-8")

    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(_cpuinfo(8), encoding="utf-8")

    def fake_getprop(args: list[str]) -> str:
        props = {
            "ro.soc.model": "Snapdragon 8 Elite",
            "ro.hardware": "",
            "ro.build.version.release": "14",
        }
        return props.get(args[1], "")

    info = detect_hardware(
        meminfo_path=str(meminfo),
        cpuinfo_path=str(cpuinfo),
        storage_path=str(tmp_path),
        getprop_runner=fake_getprop,
    )

    assert info.ram_gb == 16.0
    assert info.cpu_cores == 8
    assert info.npu_present is True
    assert info.android_version == 14
    assert info.soc_model == "Snapdragon 8 Elite"
    assert select_mode(info) == DeviceMode.FULL


def test_detect_hardware_mid_range(tmp_path):
    """detect_hardware returns correct HardwareInfo for a mid-range device."""
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(MEMINFO_8GB, encoding="utf-8")

    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(_cpuinfo(6), encoding="utf-8")

    def fake_getprop(args: list[str]) -> str:
        props = {
            "ro.soc.model": "Snapdragon 695",
            "ro.hardware": "",
            "ro.build.version.release": "13",
        }
        return props.get(args[1], "")

    info = detect_hardware(
        meminfo_path=str(meminfo),
        cpuinfo_path=str(cpuinfo),
        storage_path=str(tmp_path),
        getprop_runner=fake_getprop,
    )

    assert info.cpu_cores == 6
    assert info.npu_present is False
    assert select_mode(info) == DeviceMode.BASIC


def test_detect_hardware_missing_files(tmp_path):
    """detect_hardware degrades gracefully when /proc files are absent."""
    info = detect_hardware(
        meminfo_path=str(tmp_path / "nonexistent_meminfo"),
        cpuinfo_path=str(tmp_path / "nonexistent_cpuinfo"),
        storage_path=str(tmp_path),
        getprop_runner=lambda _args: "",
    )

    assert info.ram_gb == 0.0
    assert info.cpu_cores == 0
    assert info.npu_present is False
    assert select_mode(info) == DeviceMode.UNSUPPORTED
