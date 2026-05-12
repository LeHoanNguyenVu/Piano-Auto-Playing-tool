from PIL import Image, ImageDraw, ImageFont

def create_splash():
    width = 400
    height = 250
    # Nền tối (Dark theme)
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)

    try:
        # Thử load font mặc định của Windows
        title_font = ImageFont.truetype("arialbd.ttf", 32)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # Chữ "RobloxPianoPlayer"
    title_text = "RobloxPiano"
    title_color = "#38bdf8" # Xanh nhạt
    title_box = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_box[2] - title_box[0]
    draw.text(((width - title_w) / 2, 80), title_text, font=title_font, fill=title_color)

    # Chữ "Player"
    subtitle_text = "PLAYER"
    subtitle_color = "#94a3b8"
    sub_box = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    sub_w = sub_box[2] - sub_box[0]
    draw.text(((width - sub_w) / 2, 125), subtitle_text, font=subtitle_font, fill=subtitle_color)

    # Chữ "Loading..."
    loading_text = "Loading components... Please wait"
    loading_box = draw.textbbox((0, 0), loading_text, font=subtitle_font)
    load_w = loading_box[2] - loading_box[0]
    draw.text(((width - load_w) / 2, 210), loading_text, font=subtitle_font, fill="#64748b")

    img.save('splash.png')

if __name__ == "__main__":
    create_splash()
    print("Created splash.png")
