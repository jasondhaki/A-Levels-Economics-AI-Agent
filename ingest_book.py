import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import os
from PIL import Image  

# --- CONFIGURATION ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Your exact path to Poppler binaries
POPPLER_PATH = r'D:\poppler-26.02.0\Library\bin' 

# Bypass Pillow's Decompression Bomb protection
Image.MAX_IMAGE_PIXELS = None  

PDF_INPUT = 'Alvl Eco.pdf'
OUTPUT_FILE = 'Economics_Structured_Data.md'

def perform_ocr():
    print("🚀 Starting the j4son.dev Smart-Slicing OCR Engine...")
    
    if not os.path.exists(PDF_INPUT):
        print(f"❌ Error: Could not find '{PDF_INPUT}' in this directory.")
        return

    try:
        print("📊 Analyzing PDF structure...")
        info = pdfinfo_from_path(PDF_INPUT, poppler_path=POPPLER_PATH)
        total_pages = info["Pages"]
        print(f"📚 Detected total pages: {total_pages}")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("# A-Levels Economics Knowledge Base\n\n")
        
        for page_num in range(1, total_pages + 1):
            print(f"📄 Processing Page {page_num}/{total_pages}... ", end="", flush=True)
            
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
                
                # Tesseract hard limit threshold (~30,000 pixels)
                MAX_TESS_HEIGHT = 25000 
                
                # Check if the page is a behemoth
                if height > MAX_TESS_HEIGHT:
                    print(f"\n⚠️ Mega-page detected ({width}x{height}px). Slicing into safe chunks...")
                    text = ""
                    
                    # Slice horizontally into pieces of 25,000 pixels max
                    for top in range(0, height, MAX_TESS_HEIGHT):
                        bottom = min(top + MAX_TESS_HEIGHT, height)
                        print(f"   ✂️ Slicing segment: Y-coordinates {top} to {bottom}...")
                        
                        # Crop out the segment
                        chunk = page_image.crop((0, top, width, bottom))
                        
                        # Run OCR on the segment and append text
                        text += pytesseract.image_to_string(chunk) + "\n"
                        del chunk # Free memory immediately
                else:
                    # Normal size page, run OCR standardly
                    text = pytesseract.image_to_string(page_image)
                
                # Append the final accumulated text to the Markdown file
                with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"## Page {page_num}\n\n")
                    f.write(text)
                    f.write("\n\n---\n\n")
                
                print("Done.")
                
                # Explicitly clean up memory
                del page_image
                del page_image_list
                
        print(f"\n✅ Success! Full compilation complete with zero crashes. File saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    perform_ocr()