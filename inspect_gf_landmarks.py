from PIL import Image

img = Image.open("/Users/hemantmalik/Desktop/ambience-mall-integrated/ambience-mall-app-ui/public/maps/ground-floor.png")
print("GF size:", img.size)

# Let us verify the positions of:
# Gate 1: bottom center around x=580, y=1380
# Atrium Fountain: around x=580, y=880
# LEGO: around x=480, y=690
# Dyson: around x=480, y=630
# Isharya: around x=570, y=280
# Hackett London: around x=600, y=340
# North Exit / NH-8: around x=400, y=80

landmarks = {
    "Gate 1 Entry": (585, 1375),
    "Walkway above Gate 1 (MAC/Estee/Bath)": (585, 1260),
    "Walkway (Polo / Victoria)": (580, 1100),
    "The Atrium Fountain": (580, 880),
    "Walkway (Marks & Spencer / Uniqlo / Atrium)": (550, 780),
    "Walkway (LEGO / Dyson / Laduree)": (560, 680),
    "Walkway (West Elm / Shantnu / TUMI)": (560, 560),
    "Walkway (Armani / Dior / Ethos)": (570, 450),
    "Walkway (Isharya / Hackett / Under Armour)": (530, 320),
    "Walkway (Zoya / Aldo / Charles & Keith)": (430, 200),
    "North Entry / NH-8": (390, 80)
}

for name, (px, py) in landmarks.items():
    # Crop a 100x100 box around it
    crop_box = (max(0, px - 50), max(0, py - 50), min(1024, px + 50), min(1536, py + 50))
    patch = img.crop(crop_box)
    # Patch center color
    r, g, b = patch.getpixel((50, 50))[:3]
    print(f"{name:<45}: image (x={px}, y={py}), center RGB=({r},{g},{b})")

