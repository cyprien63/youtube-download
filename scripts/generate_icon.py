from PIL import Image, ImageDraw

def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    imgs = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = size // 10

        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=size // 5,
            fill=(255, 0, 0),
        )

        tri_x1 = int(size * 0.38)
        tri_y1 = int(size * 0.28)
        tri_x2 = int(size * 0.38)
        tri_y2 = int(size * 0.72)
        tri_x3 = int(size * 0.75)
        tri_y3 = int(size * 0.50)

        draw.polygon(
            [(tri_x1, tri_y1), (tri_x2, tri_y2), (tri_x3, tri_y3)],
            fill=(255, 255, 255),
        )

        imgs.append(img)

    imgs[0].save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=imgs[1:],
    )

    imgs[0].save("icon.png", format="PNG")
    print("Icon creees : icon.ico + icon.png")

if __name__ == "__main__":
    create_icon()
