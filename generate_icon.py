from PIL import Image, ImageDraw, ImageFont

def create_icon():
    size = (256, 256)
    image = Image.new('RGBA', size, (0, 0, 0, 0)) # Transparent background
    draw = ImageDraw.Draw(image)

    # Rounded square background
    draw.rounded_rectangle((10, 10, 246, 246), radius=60, fill="#1f6aa5", outline="#144a75", width=10)

    # Text "B"
    try:
        # Try to use a nice font if available, else default
        font = ImageFont.truetype("arial.ttf", 160)
    except:
        font = ImageFont.load_default()

    # Center text
    text = "B"
    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2 - 20 # Slight adjustment up

    draw.text((x, y), text, font=font, fill="white")

    image.save("app.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Icon created: app.ico")

if __name__ == "__main__":
    create_icon()
