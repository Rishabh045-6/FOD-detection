"""
Stage C confirm-classifier: a tiny CNN that decides FOD-object vs clean-aggregate on
40x40 patches built by make_dataset.py.

Edge-friendly (~0.1M params). Trained with flips/rotations/brightness jitter so it
generalizes across the FOD orientations and lighting we'll see at inference.

Run from C:\\Apps\\Hawkeye:
  py -3.12 tbd/train_classifier.py --data tbd/data/cls --epochs 20
Outputs: tbd/runs/cls/best.pt (state_dict + meta) and metrics.
"""
from __future__ import annotations

import argparse
import glob
import os
import random

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

PATCH = 40


class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = nn.Conv2d(3, 16, 3, padding=1); self.b1 = nn.BatchNorm2d(16)
        self.c2 = nn.Conv2d(16, 32, 3, padding=1); self.b2 = nn.BatchNorm2d(32)
        self.c3 = nn.Conv2d(32, 64, 3, padding=1); self.b3 = nn.BatchNorm2d(64)
        self.fc1 = nn.Linear(64, 32); self.fc2 = nn.Linear(32, 2)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.b1(self.c1(x))), 2)   # 20
        x = F.max_pool2d(F.relu(self.b2(self.c2(x))), 2)   # 10
        x = F.max_pool2d(F.relu(self.b3(self.c3(x))), 2)   # 5
        x = F.adaptive_avg_pool2d(x, 1).flatten(1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class PatchDS(Dataset):
    def __init__(self, files, labels, train):
        self.files = files; self.labels = labels; self.train = train

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        im = cv2.imread(self.files[i])
        if im is None or im.shape[:2] != (PATCH, PATCH):
            im = cv2.resize(im, (PATCH, PATCH)) if im is not None else np.zeros((PATCH, PATCH, 3), np.uint8)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        if self.train:
            if random.random() < 0.5: im = im[:, ::-1]
            if random.random() < 0.5: im = im[::-1, :]
            k = random.randint(0, 3); im = np.rot90(im, k).copy()
            im *= random.uniform(0.8, 1.2)          # brightness
            im = np.clip(im + np.random.normal(0, 0.02, im.shape), 0, 1)
        t = torch.from_numpy(im.transpose(2, 0, 1).astype(np.float32).copy())
        return t, self.labels[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="tbd/data/cls")
    ap.add_argument("--out", default="tbd/runs/cls")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--val-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)

    pos = sorted(glob.glob(os.path.join(args.data, "pos", "*.png")))
    neg = sorted(glob.glob(os.path.join(args.data, "neg", "*.png")))
    files = pos + neg
    labels = [1] * len(pos) + [0] * len(neg)
    idx = list(range(len(files))); random.shuffle(idx)
    nval = int(len(idx) * args.val_frac)
    vi, ti = set(idx[:nval]), idx[nval:]
    tr_f = [files[i] for i in ti]; tr_l = [labels[i] for i in ti]
    va_f = [files[i] for i in idx[:nval]]; va_l = [labels[i] for i in idx[:nval]]
    print(f"pos={len(pos)} neg={len(neg)}  train={len(tr_f)} val={len(va_f)}")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tl = DataLoader(PatchDS(tr_f, tr_l, True), batch_size=args.bs, shuffle=True, num_workers=0)
    vl = DataLoader(PatchDS(va_f, va_l, False), batch_size=args.bs, shuffle=False, num_workers=0)
    net = TinyNet().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)
    crit = nn.CrossEntropyLoss()

    best = {"f1": -1}
    for ep in range(args.epochs):
        net.train()
        for x, y in tl:
            x, y = x.to(dev), torch.as_tensor(y).to(dev)
            opt.zero_grad(); loss = crit(net(x), y); loss.backward(); opt.step()
        sched.step()
        # ---- eval ----
        net.eval(); tp = fp = fn = tn = 0
        with torch.no_grad():
            for x, y in vl:
                x = x.to(dev); pr = net(x).softmax(1)[:, 1].cpu().numpy()
                yh = (pr >= 0.5).astype(int); y = np.asarray(y)
                tp += int(((yh == 1) & (y == 1)).sum()); fp += int(((yh == 1) & (y == 0)).sum())
                fn += int(((yh == 0) & (y == 1)).sum()); tn += int(((yh == 0) & (y == 0)).sum())
        prec = tp / max(1, tp + fp); rec = tp / max(1, tp + fn)
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        print(f"ep{ep:02d}  P={prec:.3f} R={rec:.3f} F1={f1:.3f}  (tp{tp} fp{fp} fn{fn} tn{tn})")
        if f1 > best["f1"]:
            best = {"f1": f1, "P": prec, "R": rec, "ep": ep}
            torch.save({"state_dict": net.state_dict(), "patch": PATCH, "meta": best},
                       os.path.join(args.out, "best.pt"))
    print("BEST:", best, "->", os.path.join(args.out, "best.pt"))


if __name__ == "__main__":
    main()
