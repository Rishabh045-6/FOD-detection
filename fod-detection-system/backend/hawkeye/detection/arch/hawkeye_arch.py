"""
Upgrade 2 — SPD-Conv + NWD Loss for YOLO11 (spatial-blindness fix).

This is the single, idempotent patch point for the whole upgrade. It teaches a
*pip-installed* ultralytics (we run 8.4.9 both locally and on Kaggle) two new
tricks without vendoring or forking it:

  1. SPDConv — a Space-to-Depth + non-strided Conv block that is a drop-in
     replacement for a stride-2 ``Conv``. Stride-2 convolutions throw away half
     the spatial samples at every downsample; on 10-30px FOD that information is
     gone before it reaches the P3/8 head. SPDConv folds each 2x2 spatial block
     into channels instead (lossless 2x downsample), so tiny-object signal
     survives. We register it so a custom backbone yaml (yolo11-spd.yaml) can use
     it by name.

  2. NWD — Normalized Wasserstein Distance, blended into the box-regression
     (CIoU) loss. CIoU is unstable for tiny boxes (a 2-3px error on a 15px box
     collapses IoU -> ~0 gradient on exactly the objects we care about). NWD
     models each box as a 2-D Gaussian and uses a scale-invariant similarity that
     stays smooth at tiny scales.

Two application modes:

  * apply_patches(...)  — IN-MEMORY, non-invasive. Use for local dev, unit tests,
    eval, and single-process (no-DDP) training. Does NOT edit site-packages.
  * patch_on_disk(...)  — edits the installed ultralytics source so that every
    fresh import (incl. DDP child processes) sees SPDConv/NWD. Use on Kaggle.
    See detection/kaggle_synth_train_v5_spd/. (Added in the Kaggle wiring step.)

IMPORTANT: any process that BUILDS, LOADS, EXPORTS or INFERS an SPD model must
call apply_patches() (or patch_on_disk) BEFORE ``YOLO(...)`` — the checkpoint's
module graph references SPDConv by name at unpickle/parse time.
"""
from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------- #
# SPDConv source — single source of truth, shared by the in-memory and on-disk
# paths. Kept as text so the on-disk patcher can splice it into ultralytics
# without importing ultralytics first (Kaggle patches right after pip install,
# before the first `from ultralytics import YOLO`).
# ---------------------------------------------------------------------------- #
SPDCONV_SOURCE = '''
class SPDConv(nn.Module):
    """Space-to-Depth + non-strided Conv: a lossless 2x downsample that is a
    drop-in replacement for a stride-2 Conv. Folds 2x2 spatial blocks into the
    channel dim (C -> 4C, H,W -> H/2,W/2) then a 1-stride Conv mixes them back to
    c2. Preserves tiny-object signal that stride-2 convolutions discard.

    Arg contract matches Conv (c1, c2, k, s) so ultralytics' parse_model channel
    handling works unchanged; `s` is accepted but ignored (SPD always halves)."""

    def __init__(self, c1, c2, k=3, s=1):
        super().__init__()
        self.conv = Conv(c1 * 4, c2, k, 1)

    def forward(self, x):
        x = torch.cat(
            (x[..., ::2, ::2], x[..., 1::2, ::2], x[..., ::2, 1::2], x[..., 1::2, 1::2]),
            1,
        )
        return self.conv(x)
'''

# NWD config is held in module state so the (single) BboxLoss.forward patch reads
# the live ratio/C and re-calls to apply_patches() can update them.
_NWD_STATE = {"ratio": 0.0, "C": 16.0}


# ---------------------------------------------------------------------------- #
# Public API
# ---------------------------------------------------------------------------- #
def ensure_registered():
    """Best-effort guarded SPDConv registration for inference/eval load sites.

    Call right before ``YOLO(weights)``: if the checkpoint contains SPDConv it can
    then be unpickled/parsed; if not, this is a harmless no-op. Never raises — a
    plain (non-SPD) model in an env without this package must still load. NWD is
    training-only and intentionally left off here."""
    try:
        _register_spdconv_inmemory()
    except Exception:  # pragma: no cover - load site must not be broken by this
        pass


def apply_patches(nwd_ratio: float = 0.0, nwd_C: float = 16.0):
    """In-memory, non-invasive patching. Idempotent; safe to call repeatedly.

    Args:
        nwd_ratio: blend weight r for NWD in the box loss
                   ``loss = (1-r)*CIoU + r*NWD``. 0 = off (baseline, default),
                   0.5 = blend, 1.0 = full swap. Only affects training.
        nwd_C:     NWD normalization constant in pixels (~mean object size).
    """
    _register_spdconv_inmemory()
    _NWD_STATE["ratio"] = float(nwd_ratio)
    _NWD_STATE["C"] = float(nwd_C)
    if nwd_ratio and nwd_ratio > 0:
        _patch_bbox_loss_once()
    return True


# ---------------------------------------------------------------------------- #
# SPDConv registration (in-memory)
# ---------------------------------------------------------------------------- #
def _build_spdconv():
    """Materialize the SPDConv class from SPDCONV_SOURCE with __module__ set to
    the real Conv module so pickled checkpoints can re-import it by name."""
    import torch
    import torch.nn as nn
    from ultralytics.nn.modules.conv import Conv

    ns = {"nn": nn, "torch": torch, "Conv": Conv, "__name__": "ultralytics.nn.modules.conv"}
    exec(compile(SPDCONV_SOURCE, "<hawkeye_spdconv>", "exec"), ns)
    return ns["SPDConv"]


def _register_spdconv_inmemory():
    import ultralytics.nn.tasks as tasks

    if getattr(tasks, "_hawkeye_spd_registered", False):
        return

    SPDConv = _build_spdconv()

    # Expose the class everywhere parse_model / pickle might look it up.
    import ultralytics.nn.modules as M
    import ultralytics.nn.modules.conv as Mc

    for mod in (tasks, M, Mc):
        setattr(mod, "SPDConv", SPDConv)

    # base_modules is a function-local frozenset compiled into parse_model's
    # bytecode, so injecting the global isn't enough — recompile parse_model from
    # its own (installed) source with SPDConv spliced into the frozenset, then
    # rebind it in the live tasks namespace. DetectionModel looks parse_model up
    # from module globals at call time, so it picks up the new function.
    src = inspect.getsource(tasks.parse_model)
    if "SPDConv" not in src:
        patched = src.replace("            Conv,\n", "            Conv,\n            SPDConv,\n", 1)
        if patched == src:  # frozenset layout changed in this version — fail loud
            raise RuntimeError(
                "hawkeye_arch: could not splice SPDConv into parse_model.base_modules; "
                "ultralytics internals changed — inspect nn/tasks.py parse_model."
            )
        exec(compile(patched, tasks.__file__, "exec"), tasks.__dict__)

    tasks._hawkeye_spd_registered = True


# ---------------------------------------------------------------------------- #
# NWD loss (in-memory monkeypatch of BboxLoss.forward)
# ---------------------------------------------------------------------------- #
def _nwd_similarity(pred_xyxy, target_xyxy, C, eps=1e-2):
    """Normalized Wasserstein Distance similarity in [0,1] between two sets of
    axis-aligned boxes (pixel xyxy). Each box -> Gaussian N(center, diag((w/2)^2,
    (h/2)^2)); for diagonal covariances the 2-Wasserstein^2 reduces to a sum of
    squared center and half-extent differences. NWD = exp(-sqrt(W2^2)/C)."""
    pcx = (pred_xyxy[..., 0] + pred_xyxy[..., 2]) * 0.5
    pcy = (pred_xyxy[..., 1] + pred_xyxy[..., 3]) * 0.5
    pw = (pred_xyxy[..., 2] - pred_xyxy[..., 0])
    ph = (pred_xyxy[..., 3] - pred_xyxy[..., 1])

    tcx = (target_xyxy[..., 0] + target_xyxy[..., 2]) * 0.5
    tcy = (target_xyxy[..., 1] + target_xyxy[..., 3]) * 0.5
    tw = (target_xyxy[..., 2] - target_xyxy[..., 0])
    th = (target_xyxy[..., 3] - target_xyxy[..., 1])

    w2 = (pcx - tcx) ** 2 + (pcy - tcy) ** 2 + ((pw - tw) * 0.5) ** 2 + ((ph - th) * 0.5) ** 2
    return (-(w2.clamp_min(0.0) + eps).sqrt() / C).exp()


def _patch_bbox_loss_once():
    from ultralytics.utils import loss as L

    if getattr(L.BboxLoss, "_hawkeye_nwd_patched", False):
        return

    orig_forward = L.BboxLoss.forward

    def forward(self, *args):
        loss_iou, loss_dfl = orig_forward(self, *args)
        r = _NWD_STATE["ratio"]
        if not r or r <= 0:
            return loss_iou, loss_dfl
        # positional contract (v8DetectionLoss call site):
        # pred_dist, pred_bboxes, anchor_points, target_bboxes, target_scores,
        # target_scores_sum, fg_mask, imgsz, stride
        (_, pred_bboxes, _, target_bboxes, target_scores,
         target_scores_sum, fg_mask, _, stride) = args

        weight = target_scores.sum(-1)[fg_mask].unsqueeze(-1)
        # boxes are in grid units here; * stride -> pixels for a meaningful C.
        str_e = stride.unsqueeze(0).expand(fg_mask.shape[0], -1, -1)[fg_mask]
        pb = pred_bboxes[fg_mask] * str_e
        tb = target_bboxes[fg_mask] * str_e
        nwd = _nwd_similarity(pb, tb, _NWD_STATE["C"])
        loss_nwd = ((1.0 - nwd).unsqueeze(-1) * weight).sum() / target_scores_sum
        loss_iou = (1.0 - r) * loss_iou + r * loss_nwd
        return loss_iou, loss_dfl

    L.BboxLoss.forward = forward
    L.BboxLoss._hawkeye_nwd_patched = True
    L.BboxLoss._hawkeye_orig_forward = orig_forward


# ---------------------------------------------------------------------------- #
# On-disk patching (for Kaggle / DDP). Edits the installed ultralytics source so
# EVERY fresh import — including DDP child processes that re-launch the training
# command — sees SPDConv and the NWD-blended loss. NWD reads env vars
# (HAWKEYE_NWD_RATIO / HAWKEYE_NWD_C) which DDP children inherit, so no in-process
# patching is needed in the children. Use ONLY where the install is ephemeral
# (Kaggle reinstalls each run); on a dev box prefer apply_patches() + revert with
# unpatch_on_disk(). The Kaggle train script inlines an equivalent of this.
# ---------------------------------------------------------------------------- #
_SPD_MARKER = "# === HAWKEYE_SPD_PATCH (auto-generated) ==="
_NWD_MARKER = "# === HAWKEYE_NWD_PATCH (auto-generated) ==="

_TASKS_PATCH_BLOCK = '''
from ultralytics.nn.modules import SPDConv as SPDConv  # noqa: F401,E402
import inspect as _hk_inspect  # noqa: E402
_hk_src = _hk_inspect.getsource(parse_model)
if "SPDConv" not in _hk_src:
    _hk_src = _hk_src.replace("            Conv,\\n", "            Conv,\\n            SPDConv,\\n", 1)
    exec(compile(_hk_src, __file__, "exec"), globals())
del _hk_src, _hk_inspect
'''

_LOSS_PATCH_BLOCK = '''
import os as _hk_os  # noqa: E402


def _hk_nwd_similarity(p, t, C, eps=1e-2):
    pcx = (p[..., 0] + p[..., 2]) * 0.5
    pcy = (p[..., 1] + p[..., 3]) * 0.5
    pw = p[..., 2] - p[..., 0]
    ph = p[..., 3] - p[..., 1]
    tcx = (t[..., 0] + t[..., 2]) * 0.5
    tcy = (t[..., 1] + t[..., 3]) * 0.5
    tw = t[..., 2] - t[..., 0]
    th = t[..., 3] - t[..., 1]
    w2 = (pcx - tcx) ** 2 + (pcy - tcy) ** 2 + ((pw - tw) * 0.5) ** 2 + ((ph - th) * 0.5) ** 2
    return (-(w2.clamp_min(0.0) + eps).sqrt() / C).exp()


if not getattr(BboxLoss, "_hawkeye_nwd_patched", False):
    _hk_orig_forward = BboxLoss.forward

    def _hk_bbox_forward(self, *args):
        loss_iou, loss_dfl = _hk_orig_forward(self, *args)
        r = float(_hk_os.environ.get("HAWKEYE_NWD_RATIO", "0") or 0)
        if r <= 0:
            return loss_iou, loss_dfl
        C = float(_hk_os.environ.get("HAWKEYE_NWD_C", "16") or 16)
        (_, pred_bboxes, _, target_bboxes, target_scores,
         target_scores_sum, fg_mask, _, stride) = args
        weight = target_scores.sum(-1)[fg_mask].unsqueeze(-1)
        str_e = stride.unsqueeze(0).expand(fg_mask.shape[0], -1, -1)[fg_mask]
        pb = pred_bboxes[fg_mask] * str_e
        tb = target_bboxes[fg_mask] * str_e
        nwd = _hk_nwd_similarity(pb, tb, C)
        loss_nwd = ((1.0 - nwd).unsqueeze(-1) * weight).sum() / target_scores_sum
        return (1.0 - r) * loss_iou + r * loss_nwd, loss_dfl

    BboxLoss.forward = _hk_bbox_forward
    BboxLoss._hawkeye_nwd_patched = True
'''


def _modules_export_block():
    return (
        "\nfrom .conv import SPDConv  # noqa: F401,E402\n"
        "if 'SPDConv' not in __all__:\n"
        "    __all__ = (*__all__, 'SPDConv')\n"
    )


def _append_once(path, marker, block):
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return False
    path.write_text(text.rstrip("\n") + f"\n\n\n{marker}\n{block}\n", encoding="utf-8")
    return True


def _ultra_dir(ultra_dir=None):
    import importlib.util
    import pathlib

    if ultra_dir is not None:
        return pathlib.Path(ultra_dir)
    spec = importlib.util.find_spec("ultralytics")  # does not execute the package
    return pathlib.Path(spec.submodule_search_locations[0])


def patch_on_disk(ultra_dir=None):
    """Idempotently splice SPDConv + env-gated NWD into the installed ultralytics
    source. Run BEFORE the first `from ultralytics import YOLO` so the parent (and
    DDP children) pick it up natively. Set HAWKEYE_NWD_RATIO / HAWKEYE_NWD_C in the
    environment to activate NWD (default off = identical to stock)."""
    import pathlib

    d = _ultra_dir(ultra_dir)
    _append_once(d / "nn" / "modules" / "conv.py", _SPD_MARKER, SPDCONV_SOURCE)
    _append_once(d / "nn" / "modules" / "__init__.py", _SPD_MARKER, _modules_export_block())
    _append_once(d / "nn" / "tasks.py", _SPD_MARKER, _TASKS_PATCH_BLOCK)
    _append_once(d / "utils" / "loss.py", _NWD_MARKER, _LOSS_PATCH_BLOCK)
    return pathlib.Path(d)


def unpatch_on_disk(ultra_dir=None):
    """Strip the appended HAWKEYE blocks, restoring the source files."""
    d = _ultra_dir(ultra_dir)
    for rel, marker in [
        ("nn/modules/conv.py", _SPD_MARKER),
        ("nn/modules/__init__.py", _SPD_MARKER),
        ("nn/tasks.py", _SPD_MARKER),
        ("utils/loss.py", _NWD_MARKER),
    ]:
        p = d / rel
        text = p.read_text(encoding="utf-8")
        if marker in text:
            p.write_text(text.split(marker)[0].rstrip("\n") + "\n", encoding="utf-8")
