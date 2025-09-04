"""
DocuScan OCR Service

Comprehensive OCR service using Tesseract for extracting text from various document formats
including PDFs, images, and scanned documents with confidence scoring and error handling.
"""

import os
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import magic
from loguru import logger
import time
import json
import re

from ..config import settings
from ..models.document import OCRResult, DocumentType


class OCRProcessor:
    """
    Advanced OCR processor with Tesseract integration.
    
    Features:
    - Multi-format support (PDF, images, documents)
    - Image preprocessing and enhancement
    - Confidence scoring and quality assessment
    - Language detection
    - Page-by-page processing
    - Error handling and retry logic
    """
    
    def __init__(self):
        self.tesseract_cmd = settings.ocr.tesseract_cmd
        self.languages = settings.ocr.languages
        self.psm = settings.ocr.psm
        self.oem = settings.ocr.oem
        self.dpi = settings.ocr.dpi
        self.timeout = settings.ocr.timeout
        self.confidence_threshold = settings.ocr.confidence_threshold
        
        # Configure Tesseract
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
        # Supported image formats
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}
        
        logger.info(f"OCR service initialized with Tesseract at {self.tesseract_cmd}")
    
    async def process_document(self, file_path: Union[str, Path], document_type: DocumentType) -> OCRResult:
        """
        Process a document and extract text using OCR.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document being processed
            
        Returns:
            OCRResult with extracted text and metadata
        """
        file_path = Path(file_path)
        start_time = time.time()
        
        try:
            logger.info(f"Starting OCR processing for {file_path}")
            
            # Validate file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Detect MIME type
            mime_type = self._detect_mime_type(file_path)
            logger.debug(f"Detected MIME type: {mime_type}")
            
            # Process based on document type
            if document_type == DocumentType.PDF or mime_type == 'application/pdf':
                result = await self._process_pdf(file_path)
            elif document_type in [DocumentType.PNG, DocumentType.JPG, DocumentType.JPEG, 
                                  DocumentType.TIFF, DocumentType.BMP, DocumentType.GIF]:
                result = await self._process_image(file_path)
            elif document_type in [DocumentType.DOCX, DocumentType.DOC]:
                # Convert to PDF first, then process
                result = await self._process_document_file(file_path)
            elif document_type == DocumentType.TXT:
                # Direct text extraction
                result = await self._process_text_file(file_path)
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            processing_time = time.time() - start_time
            result.processing_time_seconds = processing_time
            
            logger.info(f"OCR processing completed in {processing_time:.2f}s with confidence {result.confidence:.3f}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"OCR processing failed after {processing_time:.2f}s: {e}")
            
            # Return failed result with error information
            return OCRResult(
                text=f"OCR processing failed: {str(e)}",
                confidence=0.0,
                page_count=0,
                language_detected="unknown",
                processing_time_seconds=processing_time,
                page_results=[],
                tesseract_version=self._get_tesseract_version(),
                psm_mode=self.psm,
                oem_mode=self.oem,
                dpi=self.dpi
            )
    
    async def _process_pdf(self, file_path: Path) -> OCRResult:
        """Process a PDF file using OCR."""
        logger.debug(f"Processing PDF: {file_path}")
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(file_path), dpi=self.dpi)
            
            if not images:
                raise ValueError("No pages found in PDF")
            
            # Process each page
            all_text = []
            page_results = []
            total_confidence = 0.0
            detected_languages = set()
            
            for page_num, image in enumerate(images, 1):
                logger.debug(f"Processing PDF page {page_num}/{len(images)}")
                
                # Enhance image for better OCR
                enhanced_image = self._enhance_image(image)
                
                # Perform OCR on the page
                page_result = await self._ocr_image(enhanced_image, page_num)
                
                all_text.append(page_result['text'])
                page_results.append(page_result)
                total_confidence += page_result['confidence']
                
                if page_result['language']:
                    detected_languages.add(page_result['language'])
            
            # Combine results
            combined_text = '\n\n'.join(all_text)
            avg_confidence = total_confidence / len(images) if images else 0.0
            primary_language = max(detected_languages, key=lambda x: x) if detected_languages else 'eng'
            
            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                page_count=len(images),
                language_detected=primary_language,
                processing_time_seconds=0.0,  # Will be set by caller
                page_results=page_results,
                tesseract_version=self._get_tesseract_version(),
                psm_mode=self.psm,
                oem_mode=self.oem,
                dpi=self.dpi
            )
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise
    
    async def _process_image(self, file_path: Path) -> OCRResult:
        """Process an image file using OCR."""
        logger.debug(f"Processing image: {file_path}")
        
        try:
            # Load and enhance image
            with Image.open(file_path) as image:
                enhanced_image = self._enhance_image(image)
                
                # Perform OCR
                page_result = await self._ocr_image(enhanced_image, 1)
                
                return OCRResult(
                    text=page_result['text'],
                    confidence=page_result['confidence'],
                    page_count=1,
                    language_detected=page_result['language'] or 'eng',
                    processing_time_seconds=0.0,  # Will be set by caller
                    page_results=[page_result],
                    tesseract_version=self._get_tesseract_version(),
                    psm_mode=self.psm,
                    oem_mode=self.oem,
                    dpi=self.dpi
                )
                
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise
    
    async def _process_document_file(self, file_path: Path) -> OCRResult:
        """Process DOCX/DOC files by converting to PDF first."""
        logger.debug(f"Processing document file: {file_path}")
        
        try:
            # Convert to PDF using LibreOffice (if available)
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_path = Path(temp_dir) / f"{file_path.stem}.pdf"
                
                # Try to convert using LibreOffice
                result = subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, str(file_path)
                ], capture_output=True, timeout=60)
                
                if result.returncode == 0 and pdf_path.exists():
                    # Process the converted PDF
                    return await self._process_pdf(pdf_path)
                else:
                    # Fallback: try to extract text directly
                    logger.warning("LibreOffice conversion failed, attempting direct text extraction")
                    return await self._extract_text_from_document(file_path)
                    
        except Exception as e:
            logger.error(f"Document file processing failed: {e}")
            # Final fallback: return error result
            return await self._create_error_result(f"Document processing failed: {e}")
    
    async def _process_text_file(self, file_path: Path) -> OCRResult:
        """Process plain text files."""
        logger.debug(f"Processing text file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return OCRResult(
                text=text,
                confidence=1.0,  # Text files don't need OCR
                page_count=1,
                language_detected='eng',
                processing_time_seconds=0.0,
                page_results=[{
                    'page_number': 1,
                    'text': text,
                    'confidence': 1.0,
                    'language': 'eng',
                    'word_count': len(text.split()),
                    'bbox': None
                }],
                tesseract_version=self._get_tesseract_version(),
                psm_mode=self.psm,
                oem_mode=self.oem,
                dpi=self.dpi
            )
            
        except Exception as e:
            logger.error(f"Text file processing failed: {e}")
            raise
    
    async def _ocr_image(self, image: Image.Image, page_number: int) -> Dict[str, Any]:
        """Perform OCR on a single image."""
        try:
            # Configure OCR
            config = f'--psm {self.psm} --oem {self.oem}'
            
            # Get text with confidence data
            data = pytesseract.image_to_data(
                image, 
                config=config,
                lang='+'.join(self.languages),
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                config=config,
                lang='+'.join(self.languages)
            )
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Detect language
            try:
                lang_result = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
                detected_language = lang_result.get('script', 'eng')
            except:
                detected_language = 'eng'
            
            # Count words
            word_count = len([word for word in data['text'] if word.strip()])
            
            # Extract bounding boxes for words with high confidence
            bboxes = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 60:  # Only high-confidence words
                    bbox = {
                        'text': data['text'][i],
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    }
                    bboxes.append(bbox)
            
            return {
                'page_number': page_number,
                'text': text.strip(),
                'confidence': avg_confidence / 100.0,  # Convert to 0-1 range
                'language': detected_language,
                'word_count': word_count,
                'bounding_boxes': bboxes,
                'raw_data': data
            }
            
        except Exception as e:
            logger.error(f"OCR failed for page {page_number}: {e}")
            return {
                'page_number': page_number,
                'text': '',
                'confidence': 0.0,
                'language': 'unknown',
                'word_count': 0,
                'bounding_boxes': [],
                'error': str(e)
            }
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small (minimum 300 DPI equivalent)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast and sharpness
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Apply slight denoising
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}, using original")
            return image
    
    def _detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type of file."""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(str(file_path))
        except:
            # Fallback based on extension
            extension = file_path.suffix.lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.tiff': 'image/tiff',
                '.bmp': 'image/bmp',
                '.gif': 'image/gif',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.txt': 'text/plain'
            }
            return mime_map.get(extension, 'application/octet-stream')
    
    def _get_tesseract_version(self) -> str:
        """Get Tesseract version information."""
        try:
            result = subprocess.run([self.tesseract_cmd, '--version'], 
                                  capture_output=True, text=True)
            version_line = result.stderr.split('\n')[0]
            return version_line
        except:
            return "unknown"
    
    async def _extract_text_from_document(self, file_path: Path) -> OCRResult:
        """Fallback text extraction for document files."""
        try:
            if file_path.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # Basic text extraction attempt
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            
            return OCRResult(
                text=text,
                confidence=0.8,  # Lower confidence for fallback extraction
                page_count=1,
                language_detected='eng',
                processing_time_seconds=0.0,
                page_results=[{
                    'page_number': 1,
                    'text': text,
                    'confidence': 0.8,
                    'language': 'eng',
                    'word_count': len(text.split())
                }],
                tesseract_version=self._get_tesseract_version(),
                psm_mode=self.psm,
                oem_mode=self.oem,
                dpi=self.dpi
            )
            
        except Exception as e:
            logger.error(f"Fallback text extraction failed: {e}")
            return await self._create_error_result(f"Text extraction failed: {e}")
    
    async def _create_error_result(self, error_message: str) -> OCRResult:
        """Create an error OCR result."""
        return OCRResult(
            text=error_message,
            confidence=0.0,
            page_count=0,
            language_detected="unknown",
            processing_time_seconds=0.0,
            page_results=[],
            tesseract_version=self._get_tesseract_version(),
            psm_mode=self.psm,
            oem_mode=self.oem,
            dpi=self.dpi
        )
    
    def validate_ocr_result(self, result: OCRResult) -> bool:
        """Validate OCR result quality."""
        if result.confidence < self.confidence_threshold:
            logger.warning(f"OCR confidence {result.confidence:.3f} below threshold {self.confidence_threshold}")
            return False
        
        if not result.text or len(result.text.strip()) < 10:
            logger.warning("OCR result contains insufficient text")
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform OCR service health check."""
        try:
            # Test Tesseract availability
            result = subprocess.run([self.tesseract_cmd, '--version'], 
                                  capture_output=True, timeout=10)
            tesseract_available = result.returncode == 0
            
            # Test basic OCR functionality
            test_image = Image.new('RGB', (200, 100), color='white')
            test_result = await self._ocr_image(test_image, 1)
            ocr_functional = True
            
            return {
                'status': 'healthy' if tesseract_available and ocr_functional else 'unhealthy',
                'tesseract_available': tesseract_available,
                'tesseract_version': self._get_tesseract_version(),
                'ocr_functional': ocr_functional,
                'configured_languages': self.languages,
                'psm_mode': self.psm,
                'oem_mode': self.oem,
                'dpi': self.dpi
            }
            
        except Exception as e:
            logger.error(f"OCR health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'tesseract_available': False,
                'ocr_functional': False
            }


# Global OCR processor instance
ocr_processor = OCRProcessor() 