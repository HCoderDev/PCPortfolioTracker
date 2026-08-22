from PIL import Image, ImageDraw

def create_app_icon():
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle container (Apple HIG App Icon shape)
    rect_margin = 32
    corner_radius = 96
    
    # Draw smooth gradient background
    for y in range(rect_margin, size - rect_margin):
        ratio = (y - rect_margin) / float(size - 2 * rect_margin)
        r = int(79 + ratio * (49 - 79))
        g = int(70 + ratio * (46 - 70))
        b = int(229 + ratio * (129 - 229))
        draw.line([(rect_margin, y), (size - rect_margin, y)], fill=(r, g, b, 255))

    # Mask to rounded rectangle
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([rect_margin, rect_margin, size - rect_margin, size - rect_margin], radius=corner_radius, fill=255)
    
    output_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output_img.paste(img, (0, 0), mask=mask)
    out_draw = ImageDraw.Draw(output_img)

    # Draw Financial Growth Chart Bars & Trend Arrow
    bar_width = 44
    gap = 24
    start_x = 136
    base_y = 370

    # Bar 1 (Left - Indigo)
    out_draw.rounded_rectangle([start_x, base_y - 80, start_x + bar_width, base_y], radius=8, fill=(199, 210, 254, 230))
    
    # Bar 2 (Middle - Cyan)
    out_draw.rounded_rectangle([start_x + bar_width + gap, base_y - 140, start_x + 2*bar_width + gap, base_y], radius=8, fill=(147, 197, 253, 240))
    
    # Bar 3 (Right - Emerald Growth)
    out_draw.rounded_rectangle([start_x + 2*(bar_width + gap), base_y - 210, start_x + 3*bar_width + 2*gap, base_y], radius=8, fill=(52, 211, 153, 255))

    # Trending Arrow Line
    points = [
        (130, base_y - 70),
        (start_x + bar_width + 10, base_y - 145),
        (start_x + 2*bar_width + gap + 10, base_y - 200),
        (370, base_y - 260)
    ]
    out_draw.line(points, fill=(255, 255, 255, 255), width=12)

    # Arrowhead
    arrowhead = [(370, base_y - 260), (335, base_y - 260), (370, base_y - 225)]
    out_draw.polygon(arrowhead, fill=(255, 255, 255, 255))

    # Save PNG
    output_img.save("app_icon.png", format="PNG")
    
    # Save Multi-size ICO
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    output_img.save("app_icon.ico", format="ICO", sizes=icon_sizes)
    print("app_icon.ico and app_icon.png created successfully!")

if __name__ == "__main__":
    create_app_icon()
