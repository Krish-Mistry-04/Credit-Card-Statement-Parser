import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import tempfile
import os
from typing import List, Tuple
import re

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path for Windows (adjust if needed)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF pages to images"""
        try:
            # Convert PDF to images (300 DPI for better OCR quality)
            images = convert_from_path(pdf_path, dpi=300)
            return images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return []
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy"""
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if not already
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply image processing techniques
        # 1. Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 2. Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_enhanced = clahe.apply(denoised)
        
        # 3. Binarization (Otsu's thresholding)
        _, binary = cv2.threshold(contrast_enhanced, 0, 255, 
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. Deskew (fix rotation)
        deskewed = self.deskew_image(binary)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(deskewed)
        
        # Additional PIL enhancements
        enhancer = ImageEnhance.Sharpness(processed_image)
        processed_image = enhancer.enhance(2.0)
        
        return processed_image
    
    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Fix image rotation/skew"""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
            
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Rotate only if significant skew detected
        if abs(angle) > 0.5:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), 
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
            return rotated
        return image
    
    def extract_text_from_image(self, image: Image.Image, preprocess: bool = True) -> str:
        """Extract text from image using OCR"""
        try:
            # Preprocess image if needed
            if preprocess:
                image = self.preprocess_image(image)
            
            # Configure Tesseract parameters
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
    
    def extract_text_with_regions(self, image: Image.Image) -> dict:
        """Extract text from specific regions for better accuracy"""
        width, height = image.size
        regions = {}
        
        # Define regions of interest (adjust based on typical statement layout)
        roi_definitions = {
            'header': (0, 0, width, height // 4),
            'account_info': (0, height // 4, width // 2, height // 2),
            'balance_info': (width // 2, height // 4, width, height // 2),
            'transactions': (0, height // 2, width, height)
        }
        
        for region_name, bbox in roi_definitions.items():
            # Crop region
            region_img = image.crop(bbox)
            
            # Extract text from region
            region_text = self.extract_text_from_image(region_img)
            regions[region_name] = region_text
        
        return regions
    
    def extract_structured_data(self, image: Image.Image) -> dict:
        """Extract structured data using advanced OCR techniques"""
        # Get OCR data with bounding boxes
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Group text by lines
        lines = {}
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            if data['text'][i].strip():
                line_num = data['line_num'][i]
                if line_num not in lines:
                    lines[line_num] = []
                lines[line_num].append({
                    'text': data['text'][i],
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'conf': data['conf'][i]
                })
        
        return lines
    
    def enhance_for_specific_bank(self, image: Image.Image, bank: str) -> Image.Image:
        """Apply bank-specific image enhancements"""
        if bank.lower() == 'chase':
            # Chase statements often have blue text
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.5)
        elif bank.lower() == 'amex':
            # Amex uses light backgrounds
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
        
        return image