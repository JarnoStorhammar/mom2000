from __future__ import annotations
import logging, time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)
TRACKED = {"cup","bowl","plate","fork","knife","spoon","bottle","wine glass"}

@dataclass
class Obj:
    cls: str
    first: float = field(default_factory=time.monotonic)
    last: float  = field(default_factory=time.monotonic)
    def mins(self): return (time.monotonic()-self.first)/60.0

class DishMonitor:
    def __init__(self, model_path, roi, timeout_m, cooldown_m, q_start, q_end, conf=0.45):
        self.model = YOLO(model_path)
        self.roi = roi; self.timeout_m=timeout_m; self.cooldown_m=cooldown_m
        self.q_start=q_start; self.q_end=q_end; self.conf=conf
        self._tr: dict[str,Obj] = {}; self._last_alert=0.0

    def _quiet(self):
        h = datetime.now().hour
        return h >= self.q_start or h < self.q_end if self.q_start>self.q_end else self.q_start<=h<self.q_end

    def _roi_px(self, fr):
        hh,ww=fr.shape[:2]; x1,y1,x2,y2=self.roi
        return int(x1*ww),int(y1*hh),int(x2*ww),int(y2*hh)

    def process_frame(self, frame) -> Optional[dict]:
        rx1,ry1,rx2,ry2 = self._roi_px(frame)
        results = self.model(frame[ry1:ry2,rx1:rx2], conf=self.conf, verbose=False)
        det = {r.names[int(b.cls)] for r in results for b in r.boxes if r.names[int(b.cls)] in TRACKED}
        now = time.monotonic()
        for cls in det:
            if cls in self._tr: self._tr[cls].last=now
            else: self._tr[cls]=Obj(cls=cls)
        gone=[k for k,v in self._tr.items() if now-v.last>10.0]
        for k in gone: del self._tr[k]
        if not self._tr: return None
        mx = max(v.mins() for v in self._tr.values())
        if mx<self.timeout_m or self._quiet() or now-self._last_alert<self.cooldown_m*60: return None
        self._last_alert=now
        return {"items":list(self._tr.keys()),"minutes":round(mx,1),"timestamp":datetime.now().isoformat()}

    def get_status(self): return {k:round(v.mins(),1) for k,v in self._tr.items()}
