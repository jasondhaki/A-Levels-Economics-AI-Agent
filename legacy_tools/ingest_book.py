import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import os
from PIL import Image  

# --- J4SON.DEV OCR CONFIGURATION ---
# Ensure these paths match your local installation exactly
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'D:\poppler-26.02.0\Library\bin' 

# Bypass Pillow's Decompression Bomb protection for high-res textbook pages
Image.MAX_IMAGE_PIXELS = None  

PDF_INPUT = 'Alvl Eco.pdf'
OUTPUT_FILE = 'Economics_Structured_Data.md'

def perform_ocr():
    print("🚀 STARTING THE J4SON.DEV SMART-SLICING OCR ENGINE...")
    
    if not os.path.exists(PDF_INPUT):
        print(f"❌ Error: Could not find '{PDF_INPUT}' in this directory.")
        return

    try:
        print("📊 ANALYZING PDF STRUCTURE...")
        info = pdfinfo_from_path(PDF_INPUT, poppler_path=POPPLER_PATH)
        total_pages = info["Pages"]
        print(f"📚 DETECTED TOTAL PAGES: {total_pages}")
        
        # Initialize/Wipe the output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("# J4SON.DEV A-LEVEL ECONOMICS KNOWLEDGE BASE (OCR)\n\n")
        
        for page_num in range(1, total_pages + 1):
            print(f"📄 Processing Page {page_num}/{total_pages}... ", end="", flush=True)
            
            # Convert single page to image to manage RAM
            page_image_list = convert_from_path(
                PDF_INPUT, 
                dpi=300, 
                first_page=page_num, 
                last_page=page_num, 
                poppler_path=POPPLER_PATH
            )
            
            if page_image_list:
                page_image = page_image_list[0]
                width, height = page_image.size
                
                # Tesseract threshold (~30,000 pixels is the danger zone)
                MAX_TESS_HEIGHT = 25000 
                
                text = ""
                if height > MAX_TESS_HEIGHT:
                    # Slicing logic for oversized textbook diagrams/tables
                    for top in range(0, height, MAX_TESS_HEIGHT):
                        bottom = min(top + MAX_TESS_HEIGHT, height)
                        chunk = page_image.crop((0, top, width, bottom))
                        text += pytesseract.image_to_string(chunk) + "\n"
                        del chunk 
                else:
                    text = pytesseract.image_to_string(page_image)
                
                # Append data immediately so we don't lose progress if it crashes
                with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"## PAGE {page_num}\n\n")
                    f.write(text)
                    f.write("\n\n---\n\n")
                
                print("Done.")
                
                # Explicitly clean up image objects from RAM
                del page_image
                del page_image_list
                
        print(f"\n✅ SUCCESS! Full OCR compilation complete. File: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"\n❌ AN ERROR OCCURRED IN THE J4SON.DEV OCR ENGINE: {str(e)}")

if __name__ == "__main__":
    perform_ocr()