from io import BytesIO
import qrcode
import os

def generate_qr_code():
    # Get the input text, which may include Turkish characters
    keyword = input("Enter the text for QR code generation (supports Turkish characters): ")

    # Specify the folder to save the QR code
    folder_path = "qr_codes"
    os.makedirs(folder_path, exist_ok=True)

    # Create a BytesIO object to hold the QR code image in memory
    qr_code_io = BytesIO()

    try:
        # Create a QR Code instance
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR code
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        # Add the user input data to the QR code
        qr.add_data(keyword)
        qr.make(fit=True)

        # Generate the QR code image and write it to BytesIO
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_code_io, format='PNG')

        # Save the QR code as a file
        png_file_path = os.path.join(folder_path, f"{keyword}.png")
        with open(png_file_path, "wb") as f:
            f.write(qr_code_io.getvalue())

        print(f"QR Code generated for '{keyword}' and saved as '{png_file_path}'")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
generate_qr_code()
