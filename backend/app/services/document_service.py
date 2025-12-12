"""Service for document processing (PDF splitting, image conversion)"""
from typing import List, Tuple
from PIL import Image
from pdf2image import convert_from_bytes
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing documents (PDF splitting, image conversion)"""
    
    def split_pdf_to_pages(self, pdf_bytes: bytes) -> List[bytes]:
        """
        Convert PDF bytes to list of page images (as PNG bytes).
        
        Args:
            pdf_bytes: PDF file content as bytes
        
        Returns:
            List of image bytes (one per page)
        """
        try:
            # Convert PDF to images (one per page)
            images = convert_from_bytes(pdf_bytes, dpi=200, fmt='png')
            
            page_bytes_list = []
            for idx, image in enumerate(images):
                # Convert PIL Image to bytes
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                page_bytes = buffer.getvalue()
                page_bytes_list.append(page_bytes)
                logger.info(f"Converted page {idx + 1} to PNG ({len(page_bytes)} bytes)")
            
            logger.info(f"Successfully split PDF into {len(page_bytes_list)} pages")
            return page_bytes_list
            
        except Exception as e:
            logger.error(f"Failed to split PDF: {str(e)}", exc_info=True)
            raise
    
    def convert_image_to_bytes(self, image_bytes: bytes, target_format: str = 'PNG') -> bytes:
        """
        Convert image bytes to specified format.
        
        Args:
            image_bytes: Original image bytes
            target_format: Target format ('PNG', 'JPEG')
        
        Returns:
            Converted image bytes
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            
            # Convert RGBA to RGB if saving as JPEG
            if target_format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            buffer = BytesIO()
            image.save(buffer, format=target_format)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to convert image: {str(e)}", exc_info=True)
            # Return original bytes if conversion fails
            return image_bytes
    
    def get_image_bytes_for_classification(self, file_bytes: bytes, file_extension: str) -> List[Tuple[int, bytes]]:
        """
        Get image bytes for classification/OCR processing.
        For PDFs, returns list of (page_number, page_bytes).
        For images, returns list with single (1, image_bytes).
        
        Args:
            file_bytes: File content as bytes
            file_extension: File extension (.pdf, .png, .jpg, .jpeg)
        
        Returns:
            List of tuples: (page_number (1-indexed), image_bytes)
        """
        pages = []
        
        if file_extension.lower() == '.pdf':
            # Split PDF into pages
            page_bytes_list = self.split_pdf_to_pages(file_bytes)
            for idx, page_bytes in enumerate(page_bytes_list, start=1):
                pages.append((idx, page_bytes))
        else:
            # Single image file - convert to PNG if needed
            if file_extension.lower() not in ['.png']:
                page_bytes = self.convert_image_to_bytes(file_bytes, 'PNG')
            else:
                page_bytes = file_bytes
            pages.append((1, page_bytes))
        
        return pages


# Singleton instance
document_service = DocumentService()

