from pathlib import Path
import numpy as np
from services.live_detector import LiveDetector

base = Path(__file__).resolve().parent
props = {
    'tbd_weights': str((base / 'hawkeye' / 'tbd' / 'runs' / 'cls_v7' / 'best.pt').resolve()),
    'yolo_weights': str((base / 'hawkeye' / 'detection' / 'runs' / 'fod_train' / 'v5_spd_both' / 'weights' / 'best.pt').resolve()),
}
print('weights', props)
ld = LiveDetector(**props)
frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = ld.process_frame(frame)
print('result type', type(result))
print('result length', len(result))
print('elements', [type(x) for x in result])
print('detection count', len(result[1]))
