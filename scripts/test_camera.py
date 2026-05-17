import cv2, os
src=os.getenv("RTSP_URL","") or int(os.getenv("WEBCAM_DEVICE","0"))
cap=cv2.VideoCapture(src)
ret,frame=cap.read()
print(f"{'OK' if ret else 'FAIL'}  source={src}  shape={frame.shape if ret else 'n/a'}")
cap.release()
