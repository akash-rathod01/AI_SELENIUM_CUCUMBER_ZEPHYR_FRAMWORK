# utils/visual_regression_utils.py
from PIL import Image, ImageChops
import os

class VisualRegressionUtils:
    @staticmethod
    def compare_images(img1_path, img2_path, diff_path=None):
        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)
        diff = ImageChops.difference(img1, img2)
        if diff_path:
            diff.save(diff_path)
        return diff.getbbox() is None  # True if images are identical

    @staticmethod
    def save_screenshot(driver, file_path):
        driver.save_screenshot(file_path)
