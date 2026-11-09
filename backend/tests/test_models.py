import pytest

from backend.models import QWEN_MAC, qwen_for


def test_windows_runs_qwen_from_qwen_s_own_repo_at_the_pinned_commit():
    spec = qwen_for("win32")

    assert (spec.repo_id, spec.revision) == ("Qwen/Qwen3.5-9B", "c202236235762e1c871ad0ccb60c8ee5ba337b9a")
    assert (spec.check_id, spec.label, spec.platforms) == ("model_qwen", "Qwen3.5 9B model", ("win32",))
    assert spec.allow_patterns == QWEN_MAC.allow_patterns
    assert (spec.license, spec.license_url, spec.author) == (QWEN_MAC.license, QWEN_MAC.license_url, "Qwen")


@pytest.mark.parametrize("sys_platform", ["darwin", "linux"])
def test_every_other_os_runs_the_mlx_model(sys_platform):
    assert qwen_for(sys_platform) is QWEN_MAC
