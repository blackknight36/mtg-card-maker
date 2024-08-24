#!/usr/bin/env python3
import os
import openai
import random
import cairosvg
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import json

# Read API key from a file
with open("openai_api_key.txt", "r") as file:
    openai.api_key = file.read().strip()

# Define dimensions
CARD_WIDTH = 1500
CARD_HEIGHT = 2100
MARGIN = 100

# Font settings
FONT_PATH = "/Users/michael.watters/Library/Fonts/Beleren2016-Bold.ttf"
FONT_SIZE_TEXT = 50
FONT_SIZE_PT = 80
FONT_SIZE_TYPE = 80

# Define available card types
CARD_TYPES = ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Land']

# Directory to save cards
OUTPUT_DIR = "cards"

# Paths to frames
FRAME_DIR = "art/frames"
CREATURE_FRAME_DIR = os.path.join(FRAME_DIR, "creature")

# Directory where mana symbols are stored
MANA_SYMBOLS_DIR = "cardImages/manaSymbols"

# Load all mana symbols as PNG Image objects from SVGs
def load_mana_symbol(symbol_name):
    svg_path = os.path.join(MANA_SYMBOLS_DIR, f"{symbol_name}.svg")
    png_data = cairosvg.svg2png(url=svg_path)
    return Image.open(BytesIO(png_data))

mana_symbols = {
    'T': load_mana_symbol('t'),
    'W': load_mana_symbol('w'),
    'U': load_mana_symbol('u'),
    'B': load_mana_symbol('b'),
    'R': load_mana_symbol('r'),
    'G': load_mana_symbol('g'),
    'C': load_mana_symbol('c'),
    '1': load_mana_symbol('1'),
    '2': load_mana_symbol('2'),
    '3': load_mana_symbol('3'),
    '4': load_mana_symbol('4'),
    '5': load_mana_symbol('5'),
    '6': load_mana_symbol('6'),
    '7': load_mana_symbol('7'),
    '8': load_mana_symbol('8'),
    '9': load_mana_symbol('9'),
}

# Replace mana symbols in text with images
def replace_mana_symbols(text, font_size):
    elements = []
    temp = ""
    inside_braces = False

    for char in text:
        if char == "{":
            inside_braces = True
            temp = ""
        elif char == "}":
            inside_braces = False
            symbol_image = mana_symbols.get(temp.upper())
            if symbol_image:
                symbol_image = symbol_image.resize((font_size, font_size), Image.LANCZOS)
                elements.append(symbol_image)
            else:
                elements.append(f"{{{temp}}}")  # Fallback to text if symbol not found
        elif inside_braces:
            temp += char
        else:
            elements.append(char)
    return elements

# Draw the card title and mana cost
def draw_card_title(card, draw, card_name, mana_cost, x_offset=120, y_offset=111, box_width=1272, box_height=96):
    # Determine the initial font size based on title length
    font_size = min(90, int(box_width / (len(card_name) + len(mana_cost) / 2)))
    font = ImageFont.truetype(FONT_PATH, font_size)

    # Calculate the width and height of the card name text
    card_name_bbox = draw.textbbox((0, 0), card_name, font=font)
    card_name_width = card_name_bbox[2] - card_name_bbox[0]
    card_name_height = card_name_bbox[3] - card_name_bbox[1]

    # Calculate the vertical position to center the card name
    card_name_y = y_offset + (box_height - card_name_height) // 2

    # Draw the card name
    draw.text((x_offset, card_name_y), card_name, font=font, fill="black")

    # Calculate the width of the mana cost string
    mana_cost_width = sum([draw.textbbox((0, 0), symbol, font=font)[2] - draw.textbbox((0, 0), symbol, font=font)[0] for symbol in mana_cost])

    # Calculate the vertical position to center the mana cost
    mana_cost_height = card_name_height
    mana_y = card_name_y

    # Right-align the mana cost within the title box
    mana_x = x_offset + box_width - mana_cost_width  # Align to the right edge
    draw_mana_cost(card, draw, mana_cost, mana_x, mana_y)

# Draw the mana cost
def draw_mana_cost(card, draw, mana_cost, x, y):
    font_size = FONT_SIZE_TEXT
    elements = replace_mana_symbols(mana_cost, font_size)

    for element in elements:
        if isinstance(element, Image.Image):
            card.paste(element, (int(x), int(y)), element)
            x += element.width
        else:
            draw.text((x, y), element, font=ImageFont.truetype(FONT_PATH, font_size), fill="black")
            x += draw.textlength(element, font=ImageFont.truetype(FONT_PATH, font_size))

# Draw the card type
def draw_card_type(draw, card_type, x_offset=147, y_offset=1197):
    type_area = [x_offset, y_offset, CARD_WIDTH - x_offset, 1330]
    draw.text((type_area[0], type_area[1]), card_type, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TYPE), fill="black")

# Draw the abilities text box
def draw_card_abilities(card, draw, abilities, x=120, y=1323, box_width=1266, box_height=620, top_padding=20):
    abilities_text = '\n'.join(abilities)

    font_size = FONT_SIZE_TEXT
    font = ImageFont.truetype(FONT_PATH, font_size)

    max_width = box_width

    words = abilities_text.split()
    wrapped_lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word if current_line == "" else current_line + " " + word
        line_width = draw.textlength(test_line, font=font)
        if line_width <= max_width:
            current_line = test_line
        else:
            wrapped_lines.append(current_line)
            current_line = word

    wrapped_lines.append(current_line)

    text_height = len(wrapped_lines) * (font_size + 10)

    while text_height > box_height and font_size > 10:
        font_size -= 2
        font = ImageFont.truetype(FONT_PATH, font_size)
        wrapped_lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word if current_line == "" else current_line + " " + word
            line_width = draw.textlength(test_line, font=font)
            if line_width <= max_width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word

        wrapped_lines.append(current_line)
        text_height = len(wrapped_lines) * (font_size + 10)

    current_y = y + top_padding
    for line in wrapped_lines:
        draw.text((x, current_y), line, font=font, fill="black")
        current_y += font_size + 10

# Load the frame for the card based on type and color
def load_frame_for_card_type(card_type, color):
    if card_type == 'Creature':
        return os.path.join(CREATURE_FRAME_DIR, f"{color.lower()}.png")
    return os.path.join(FRAME_DIR, f"{color.lower()}.png")

# Generate card text using GPT-4
def generate_card_text(card_type):
    prompt = (
        f"Generate a Magic: The Gathering {card_type} card with the following attributes: "
        f"Name, Mana Cost, Type, Abilities, Power/Toughness (if applicable), Flavor Text, Rarity, and Color. "
        f"Return the response as a JSON object with the following keys: "
        f"'name', 'mana_cost', 'type', 'abilities', 'power_toughness', 'flavor_text', 'rarity', and 'color'. "
        f"Ensure that the JSON keys are in lowercase.  Colorless, non-artifact cards must return color as 'void'.  Artifact cards need to return color as 'artifact'.  Land cards should return color as 'land'.  Mana costs must have symbols enclosed in curly braces.  Multicolored cards should return color as 'multicolored'. "
        f"Card names should be randomized with a large entropy pool. "
    )

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates Magic: The Gathering cards."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.5
    )

    card_text = response['choices'][0]['message']['content'].strip()

    if card_text.startswith("```json"):
        card_text = card_text[7:]
    if card_text.endswith("```"):
        card_text = card_text[:-3]

    try:
        card_data = json.loads(card_text)
        card_data = {k.lower(): v for k, v in card_data.items()}
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse card text as JSON: {e}")

    return card_data

# Generate card art using DALL-E
def generate_card_art(description):
    dalle_response = openai.Image.create(
        prompt=description,
        n=1,
        size="1024x1024"
    )
    return dalle_response['data'][0]['url']

# Create the card template
def create_template(card, draw, card_data, card_art):
    frame_path = load_frame_for_card_type(card_data['type'], card_data['color'])
    frame = Image.open(frame_path)
    card.paste(frame, (0, 0))

    art_area = [117, 237, 1383, 1164]
    art_width = art_area[2] - art_area[0]
    art_height = art_area[3] - art_area[1]

    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_ratio = art_image.width / art_image.height
        box_ratio = art_width / art_height

        if art_ratio > box_ratio:
            scale_height = art_height
            scale_width = int(scale_height * art_ratio)
        else:
            scale_width = art_width
            scale_height = int(scale_width / art_ratio)

        art_image = art_image.resize((scale_width, scale_height), Image.LANCZOS)
        x_offset = (art_image.width - art_width) // 2
        y_offset = (art_image.height - art_height) // 2
        art_image = art_image.crop((x_offset, y_offset, x_offset + art_width, y_offset + art_height))
        card.paste(art_image, (art_area[0], art_area[1]))

    draw_card_title(card, draw, card_data["name"], card_data["mana_cost"])
    draw_card_type(draw, card_data["type"])
    draw_card_abilities(card, draw, card_data["abilities"])

# Generate and save the card
def generate_card():
    card_type = random.choice(CARD_TYPES)
    print(f"Generating a {card_type} card...")
    card_data = generate_card_text(card_type)

    print("Generated Card Data:")
    print(json.dumps(card_data, indent=2))

    image_description = f"Artwork for a {card_data['color']} {card_type} Magic: The Gathering card using the following rules text. {card_data['abilities']}"
    card_art_url = generate_card_art(image_description)
    print("Generated Card Art URL:")
    print(card_art_url)

    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(card)
    create_template(card, draw, card_data, card_art_url)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    output_filename = os.path.join(OUTPUT_DIR, f"{card_data['name'].replace(' ', '_')}_{card_type}.png")
    card.save(output_filename, "PNG")
    print(f"Card saved as {output_filename}")

if __name__ == "__main__":
    generate_card()

