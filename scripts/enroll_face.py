"""
Face enrollment.
  python scripts/enroll_face.py --name "Jarno" --webcam [--count 10]
  python scripts/enroll_face.py --name "Jarno" --images /path/to/photos/
  python scripts/enroll_face.py --list
"""
from __future__ import annotations
import argparse, logging, pickle
from pathlib import Path
from typing import Optional
import cv2, face_recognition, numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger=logging.getLogger("enroll")
EMB=Path("shared/embeddings/embeddings.pkl")

def load():
    if EMB.exists():
        with open(EMB,"rb") as f: d=pickle.load(f)
        return d.get("encodings",[]),d.get("names",[])
    return [],[]

def save(e,n):
    EMB.parent.mkdir(parents=True,exist_ok=True)
    with open(EMB,"wb") as f: pickle.dump({"encodings":e,"names":n},f)
    logger.info("Saved %d embeddings",len(n))

def from_dir(name,d):
    e,n=load(); c=0
    for p in Path(d).glob("*"):
        if p.suffix.lower() not in{".jpg",".jpeg",".png",".bmp"}: continue
        img=face_recognition.load_image_file(str(p))
        locs=face_recognition.face_locations(img)
        if not locs: logger.warning("No face: %s",p.name); continue
        enc=face_recognition.face_encodings(img,locs[:1])
        if enc: e.append(enc[0]); n.append(name); c+=1; logger.info("Enrolled %s",p.name)
    if c: save(e,n)
    return c

def from_webcam(name,count=10):
    cap=cv2.VideoCapture(0)
    if not cap.isOpened(): logger.error("No webcam"); return 0
    e,n=load(); c=0; logger.info("SPACE=capture  Q=quit  target=%d",count)
    while c<count:
        ret,frame=cap.read()
        if not ret: continue
        d=frame.copy()
        cv2.putText(d,f"{c}/{count} SPACE=capture Q=quit",(10,30),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,255,0),2)
        cv2.imshow("Enroll",d); key=cv2.waitKey(1)&0xFF
        if key==ord("q"): break
        if key==ord(" "):
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            locs=face_recognition.face_locations(rgb)
            if not locs: logger.warning("No face"); continue
            enc=face_recognition.face_encodings(rgb,locs)
            if enc: e.append(enc[0]); n.append(name); c+=1; logger.info("Captured %d/%d",c,count)
    cap.release(); cv2.destroyAllWindows()
    if c: save(e,n)
    return c

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--name"); p.add_argument("--images"); p.add_argument("--webcam",action="store_true")
    p.add_argument("--count",type=int,default=10); p.add_argument("--list",action="store_true")
    a=p.parse_args()
    if a.list:
        _,n=load(); print("Enrolled:",", ".join(sorted(set(n))) or "none"); return
    if not a.name: p.error("--name required")
    if a.images: print(f"Enrolled {from_dir(a.name,a.images)} for '{a.name}'")
    elif a.webcam: print(f"Enrolled {from_webcam(a.name,a.count)} for '{a.name}'")
    else: p.error("--images or --webcam required")

if __name__=="__main__": main()
