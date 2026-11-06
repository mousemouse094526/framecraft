"""The Windows Qwen worker against stand-in `torch` and `transformers` modules: the real
model is checked by hand on a Windows card (windows-launch D5, ticket 03)."""

import queue
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from backend.spoil_maker import llm, llm_windows
from backend.spoil_maker.llm import Generate, Generated, Ready, WorkerError

PROMPT_IDS = np.array([[1, 2, 3]])
NEW_IDS = np.array([[7, 8]])


# Stand-ins for `torch.nn.Linear` and a 4-bit layer: the load report counts modules
# whose type is exactly `torch.nn.Linear`.
class FakeLinear:
    pass


class FakeQuantized:
    pass


class FakeInputs(dict):
    def to(self, device):
        self["device"] = device
        return self


class FakeProcessor:
    def __init__(self):
        self.template_calls = []
        self.decoded = None

    def apply_chat_template(self, messages, **kwargs):
        self.template_calls.append((messages, kwargs))
        return FakeInputs(input_ids=PROMPT_IDS)

    def batch_decode(self, ids, **kwargs):
        self.decoded = (ids, kwargs)
        return ["the new text"]


class FakeModel:
    device = "cuda:0"

    def __init__(self):
        self.generate_kwargs = None

    def named_modules(self):
        return [
            ("", object()),
            ("model.visual.blocks.0.attn.qkv", FakeLinear()),
            ("model.visual.blocks.1.attn.qkv", FakeLinear()),
            ("model.language_model.layers.0.mlp.gate_proj", FakeQuantized()),
            ("lm_head", FakeLinear()),
        ]

    def generate(self, **kwargs):
        self.generate_kwargs = kwargs
        return np.concatenate([PROMPT_IDS, NEW_IDS], axis=1)


@pytest.fixture
def fake_libraries(monkeypatch):
    """`torch` and `transformers` as the worker sees them on a Windows card."""
    loaded = types.SimpleNamespace(processor=FakeProcessor(), model=FakeModel(), calls={})

    torch = types.ModuleType("torch")
    torch.bfloat16 = "bfloat16"
    torch.nn = types.SimpleNamespace(Linear=FakeLinear)
    torch.cuda = types.SimpleNamespace(max_memory_allocated=lambda device: 7 * 2**30)

    transformers = types.ModuleType("transformers")

    def bits_and_bytes_config(**kwargs):
        loaded.calls["quantization"] = kwargs
        return ("quantization", kwargs)

    def processor_from_pretrained(path, **kwargs):
        loaded.calls["processor"] = (path, kwargs)
        return loaded.processor

    def model_from_pretrained(path, **kwargs):
        loaded.calls["model"] = (path, kwargs)
        return loaded.model

    transformers.BitsAndBytesConfig = bits_and_bytes_config
    transformers.AutoProcessor = types.SimpleNamespace(from_pretrained=processor_from_pretrained)
    transformers.AutoModelForImageTextToText = types.SimpleNamespace(from_pretrained=model_from_pretrained)

    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    return loaded


def run_worker(snapshot: Path, *requests) -> list:
    asked, replies = queue.Queue(), queue.Queue()
    for request in (*requests, None):
        asked.put(request)
    llm_windows.worker(snapshot, asked, replies)
    answers = []
    while not replies.empty():
        answers.append(replies.get())
    return answers


def test_windows_starts_the_transformers_worker_and_the_mac_the_mlx_one():
    assert llm.worker_for("win32") is llm_windows.worker
    assert llm.worker_for("darwin") is llm.worker
    assert llm.worker_for("linux") is llm.worker


def test_a_missing_snapshot_raises_before_transformers_is_imported(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "transformers", None)  # importing it would raise ImportError

    with pytest.raises(FileNotFoundError):
        llm_windows.load(tmp_path / "missing")


def test_the_model_loads_offline_in_4_bit_on_the_card_keeping_vision_and_lm_head(tmp_path, fake_libraries):
    llm_windows.load(tmp_path)

    assert fake_libraries.calls["processor"] == (tmp_path, {"local_files_only": True})
    path, kwargs = fake_libraries.calls["model"]
    assert path == tmp_path
    assert kwargs["local_files_only"] is True
    assert kwargs["device_map"] == "cuda:0"
    assert kwargs["dtype"] == "bfloat16"
    assert fake_libraries.calls["quantization"] == {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": "bfloat16",
        "llm_int8_skip_modules": ["model.visual", "lm_head"],
    }


def test_after_loading_it_logs_what_stayed_unquantized_and_the_vram_then_says_ready(tmp_path, fake_libraries, capsys):
    answers = run_worker(tmp_path)

    assert answers == [Ready()]
    log = capsys.readouterr().err
    assert "not quantized: model.visual (2), lm_head (1)" in log
    assert "VRAM after load: 7.0 GiB" in log


def test_a_prompt_with_an_image_is_answered_with_the_new_tokens_only(tmp_path, fake_libraries):
    frame = tmp_path / "0.jpg"

    answers = run_worker(tmp_path, Generate("Describe this frame.", frame, 80, 0.0))

    assert answers == [Ready(), Generated("the new text")]
    messages, kwargs = fake_libraries.processor.template_calls[0]
    assert messages == [
        {"role": "user", "content": [{"type": "image", "path": str(frame)}, {"type": "text", "text": "Describe this frame."}]}
    ]
    assert kwargs["enable_thinking"] is False
    assert kwargs["add_generation_prompt"] is True
    generated = fake_libraries.model.generate_kwargs
    assert (generated["max_new_tokens"], generated["do_sample"], generated["input_ids"] is PROMPT_IDS) == (80, False, True)
    assert "temperature" not in generated
    ids, decode_kwargs = fake_libraries.processor.decoded
    assert ids.tolist() == NEW_IDS.tolist()
    assert decode_kwargs == {"skip_special_tokens": True}


def test_a_prompt_with_a_temperature_samples_at_it(tmp_path, fake_libraries):
    run_worker(tmp_path, Generate("Write the script.", None, 4000, 0.3))

    messages, _ = fake_libraries.processor.template_calls[0]
    assert messages[0]["content"] == [{"type": "text", "text": "Write the script."}]
    generated = fake_libraries.model.generate_kwargs
    assert (generated["do_sample"], generated["temperature"]) == (True, 0.3)


def test_any_error_answers_model_failed_and_ends_the_worker(tmp_path, fake_libraries):
    def out_of_memory(**kwargs):
        raise RuntimeError("CUDA out of memory")

    fake_libraries.model.generate = out_of_memory

    answers = run_worker(tmp_path, Generate("a", None, 10, 0.0), Generate("b", None, 10, 0.0))

    assert answers == [Ready(), WorkerError("model_failed", "RuntimeError: CUDA out of memory")]


def test_each_os_reads_its_own_timeouts_and_others_get_the_macs(monkeypatch):
    from backend import checks

    for sys_platform, expected in [
        ("darwin", llm.Timeouts(describe=60, write=600, polish=300, pick=60)),
        ("win32", llm.Timeouts(describe=300, write=3000, polish=1500, pick=300)),
        ("linux", llm.Timeouts(describe=60, write=600, polish=300, pick=60)),
    ]:
        monkeypatch.setattr(checks, "this_platform", lambda: sys_platform)
        assert llm.timeouts() == expected


def test_the_windows_worker_can_be_sent_to_a_spawned_child():
    import pickle

    assert pickle.loads(pickle.dumps(llm.worker_for("win32"))) is llm_windows.worker


def test_a_failed_load_answers_model_failed_without_ready(tmp_path):
    answers = run_worker(tmp_path / "missing")

    assert len(answers) == 1
    assert answers[0].code == "model_failed"
    assert answers[0].detail.startswith("FileNotFoundError: no model snapshot at")
