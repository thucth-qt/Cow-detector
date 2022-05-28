import os
import json
from tqdm import tqdm
import shutil
import numpy as np
import cv2
def convert_bbox_coco2yolo(img_width, img_height, bbox):
    """
    Convert bounding box from COCO  format to YOLO format

    Parameters
    ----------
    img_width : int
        width of image
    img_height : int
        height of image
    bbox : list[int]
        bounding box annotation in COCO format: 
        [top left x position, top left y position, width, height]

    Returns
    -------
    list[float]
        bounding box annotation in YOLO format: 
        [x_center_rel, y_center_rel, width_rel, height_rel]
    """
    def dsbbox2yolo(cx, cy, w, h, alpha):
        #step1: src for straight rectangle
        tl = (cx-w/2, cy-h/2)
        tr = (cx+w/2, cy-h/2)
        bl = (cx-w/2, cy+h/2)
        br = (cx+w/2, cy+h/2)
        src_points = np.array([tl, tr, br, bl]).T

        #step2: center, angle => rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D((cx, cy), -alpha/np.pi*180, 1)
        R = np.array(rotation_matrix[:2, :2])
        t = np.array(rotation_matrix[:, 2])

        #step3: multiply rotation matrix with src_points
        x = R@src_points + np.expand_dims(t, 1)
        x = x.astype(np.int32).T

        result_tl = np.min(x[:,0]), np.min(x[:,1])
        result_br = np.max(x[:,0]), np.max(x[:,1])
        return result_tl[0], result_tl[1], result_br[0]-result_tl[0], result_br[1]-result_tl[1]
    # YOLO bounding box format: [x_center, y_center, width, height]
    # (float values relative to width and height of image)
    x_tl, y_tl, w, h, alpha = bbox
    x_tl, y_tl, w, h = dsbbox2yolo(x_tl+w/2, y_tl+h/2, w, h, alpha)

    dw = 1.0 / img_width
    dh = 1.0 / img_height

    x_center = x_tl + w / 2.0
    y_center = y_tl + h / 2.0

    x = x_center * dw
    y = y_center * dh
    w = w * dw
    h = h * dh

    return [x, y, w, h]

def make_folders(path="output"):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path


def convert_coco_json_to_yolo_txt(output_path, json_file):

    path = make_folders(output_path)

    with open(json_file) as f:
        json_data = json.load(f)

    # write _darknet.labels, which holds names of all classes (one class per line)
    label_file = os.path.join(output_path, "_darknet.labels")
    with open(label_file, "w") as f:
        for category in tqdm(json_data["categories"], desc="Categories"):
            category_name = category["name"]
            f.write(f"{category_name}\n")

    for image in tqdm(json_data["images"], desc="Annotation txt for each iamge"):
        img_id = image["id"]
        img_name = image["file_name"]
        img_width = image["width"]
        img_height = image["height"]

        anno_in_image = [anno for anno in json_data["annotations"] if anno["image_id"] == img_id]
        anno_txt = os.path.join(output_path, img_name.split(".")[0] + ".txt")
        with open(anno_txt, "w") as f:
            for anno in anno_in_image:
                category = anno["category_id"]-1
                bbox_COCO = anno["bbox"]
                x, y, w, h = convert_bbox_coco2yolo(img_width, img_height, bbox_COCO)
                f.write(f"{category} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")

    print("Converting COCO Json to YOLO txt finished!")

if __name__=="__main__":
    convert_coco_json_to_yolo_txt("/content/Cow-detector/dataset/Sub-levels/Detection_and_localisation/Train/labels/train/","/content/Cow-detector/dataset/Sub-levels/Detection_and_localisation/Train/annotations/instances_train.json")
    convert_coco_json_to_yolo_txt("/content/Cow-detector/dataset/Sub-levels/Detection_and_localisation/Train/labels/val/","/content/Cow-detector/dataset/Sub-levels/Detection_and_localisation/Train/annotations/instances_val.json")
    convert_coco_json_to_yolo_txt("/content/Cow-detector/dataset/Sub-levels/Detection_and_localisation/Test/labels/test/","/content/Cow-detector/dataset/Sub-levels/Detection_and_localisation/Test/annotations/instances_val.json")
