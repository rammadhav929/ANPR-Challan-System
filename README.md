# ANPR-Challan-System
Automated Number Plate Detection and Challan Issuing System is a web application that uses YOLOv8 to identify vehicle number plates and automatically send challans via email.



# What is YoloV8 ?
YOLOv8 (You Only Look Once version 8) is a state-of-the-art computer vision model architecture by Ultralytics that offers high accuracy and real-time speed for various tasks, including object detection, image classification, instance segmentation, and pose estimation
✔ Easier to customize
✔ Supports GPUs easily
✔ Can export ONNX, Tensor flow
✔ Works well with Deep Learning tools (TensorFlow, OpenCV, Nvidia CUDA)

- 2️⃣ What is mAP?
mAP = Mean Average Precision
It combines:
- Precision
- Recall
- IoU threshold
- It measures:
How accurately your model detects objects AND places bounding boxes correctly.

- 3️⃣ What is mAP@0.5 ?
This means:
A detection is considered correct if IoU ≥ 0.5
,Then precision-recall curve is calculated
,Then averaged across classes
So:
mAP@0.5 = performance when overlap threshold is 50%


