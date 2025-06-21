from PIL import Image
import os

def convert_to_ico():
    try:
        # Input and output paths
        input_path = 'favicon_elastic.png'
        output_path = 'public/favicon.ico'
        
        # Open the image and convert to ICO
        img = Image.open(input_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Create ICO in multiple sizes (favicon standard sizes)
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        img.save(output_path, format='ICO', sizes=sizes)
        
        print(f"Successfully converted {input_path} to {output_path}")
        return True
    except Exception as e:
        print(f"Error converting favicon: {e}")
        return False

if __name__ == "__main__":
    convert_to_ico()
