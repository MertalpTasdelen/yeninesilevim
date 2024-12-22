from io import BytesIO
import barcode
from barcode.writer import SVGWriter
import os

def generate_barcode():
    # Get the barcode content from the user
    keyword = input("Enter the keyword for barcode generation (alphanumeric): ")

    # Specify the folder to save the barcode
    folder_path = "barcodes"
    os.makedirs(folder_path, exist_ok=True)

    # Create a BytesIO object to hold the SVG barcode in memory
    barcode_io = BytesIO()

    try:
        # Create the Code128 barcode with SVGWriter to write to the BytesIO object
        code128 = barcode.get('code128', keyword, writer=SVGWriter())
        code128.write(barcode_io)  # Write the barcode to the BytesIO object

        # Optionally, save the SVG data to a file
        svg_file_path = os.path.join(folder_path, f"{keyword}.svg")
        with open(svg_file_path, "wb") as f:
            f.write(barcode_io.getvalue())

        print(f"Barcode generated for '{keyword}' and saved as '{svg_file_path}'")
        
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
generate_barcode()
