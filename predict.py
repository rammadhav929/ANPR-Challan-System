from ultralytics import YOLO
import cv2 as c
import easyocr
from matplotlib import pyplot as plt
import pandas as pd
import os
from PIL import Image


def crop_and_save_photo(photo_path, crop_coordinates, output_folder):
    photo = Image.open(photo_path)
    cropped_photo = photo.crop(crop_coordinates)
    output_path = os.path.join(output_folder, os.path.basename(photo_path))
    cropped_photo.save(output_path)


def plate(path, filename):
    model = YOLO("./runs/detect/train6/weights/best.pt")
    result = model.predict(source=path, show=True)
    img = c.imread(path)
    result = result[0].boxes
    cordinates = result.xyxy
    n = len(cordinates)
    for i in range(0, n):
        min = int(cordinates[i][0]), int(cordinates[i][2])
        max = int(cordinates[i][1]), int(cordinates[i][3])
    print(min, max)
    x, y = min
    u, o = max
    roi = img[u:o, x:y]
    crop_coordinates = (x, u, y, o)
    output_folder = "./static/predict"
    crop_and_save_photo(path, crop_coordinates, output_folder)

    roi_bgr = c.cvtColor(roi, c.COLOR_RGB2BGR)
    gray = c.cvtColor(roi_bgr, c.COLOR_BGR2GRAY)
    magic_color = apply_brightness_contrast(gray, brightness=35, contrast=70)
    reader = easyocr.Reader(["en"], gpu=False)
    result1 = reader.readtext(magic_color)
    c.imwrite("r.jpg", magic_color)
    if len(result1) == 1 or len(result1) > 2:
        model_ocr = YOLO("./runs1/detect/train10/weights/best.pt")
        result = model_ocr.predict(source=roi, conf=0.3)
        ocr = result[0].names
        box = result[0].boxes
        data_ocr = box.data
        n = len(data_ocr)
        xaxis = []
        class_name = []
        for i in range(0, n):
            x = int(data_ocr[i][2])
            xaxis.append(x)
            y = int(data_ocr[i][5])
            class_name.append(y)
        for i in range(0, n - 1):
            for j in range(i + 1, n):
                if xaxis[i] > xaxis[j]:
                    t = xaxis[i]
                    xaxis[i] = xaxis[j]
                    xaxis[j] = t
                    t = class_name[i]
                    class_name[i] = class_name[j]
                    class_name[j] = t
        decode = ""
        for i in range(0, n):
            decode = decode + (ocr.get(class_name[i]))
        if decode[1] == "0":
            t = decode
            decode = decode[0]
            for i in range(2, n):
                decode = decode + (ocr.get(class_name[i]))
        print(decode)
        return decode

    elif len(result1) == 2:
        b = result1[0][1] + result1[1][1]
        if b[0] == "6":
            new_b = b[0].replace("6", "G")
            b = new_b + b[1:10]
            return b
        else:
            return b


def apply_brightness_contrast(input_img, brightness, contrast):
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow) / 255
        gamma_b = shadow

        buf = c.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()

    if contrast != 0:
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)

        buf = c.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf
