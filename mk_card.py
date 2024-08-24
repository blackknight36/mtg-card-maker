#!/usr/bin/env python3
import os
import openai
import random
import cairosvg
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import json
import textwrap

# Read API key from a file
with open("openai_api_key.txt", "r") as file:
    openai.api_key = file.read().strip()

# Define dimensions
CARD_WIDTH = 1500
CARD_HEIGHT = 2100
MARGIN = 100  # Increased margin for better spacing

# Font settings
FONT_PATH = "/Users/michael.watters/Library/Fonts/Beleren2016-Bold.ttf"
FONT_SIZE_TITLE = 90  # Adjusted to move the title down
FONT_SIZE_TEXT = 50
FONT_SIZE_PT = 80
FONT_SIZE_TYPE = 80

# Define available card types
#CARD_TYPES = ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Planeswalker', 'Land']
CARD_TYPES = ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Land']

# Directory to save cards
OUTPUT_DIR = "cards"

# Path to your frames
FRAME_DIR = "art/frames"
CREATURE_FRAME_DIR = os.path.join(FRAME_DIR, "creature")

from PIL import Image
from io import BytesIO

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

def replace_mana_symbols(text, symbol_size=(60, 60)):
    elements = []
    temp = ""  # Initialize temp as an empty string

    inside_braces = False

    for char in text:
        if char == "{":
            inside_braces = True
            temp = ""  # Reset temp when opening brace is found
        elif char == "}":
            inside_braces = False
            if temp in mana_symbols:
                # Resize the symbol to the desired size using Image.LANCZOS for high-quality downscaling
                symbol = mana_symbols[temp].resize(symbol_size, Image.LANCZOS)
                elements.append(symbol)  # Append the resized image
            else:
                elements.append(f"{{{temp}}}")  # Append the text if no match found
            temp = ""  # Reset temp for the next symbol
        elif inside_braces:
            temp += char
        else:
            elements.append(char)  # Directly add non-symbol text
    return elements

def draw_card_abilities(card, draw, abilities, x=120, y=1323, box_width=1266, box_height=620, top_padding=20):
    # Combine all abilities into a single string
    abilities_text = '\n'.join(abilities)

    # Set initial font size and load the font
    font_size = FONT_SIZE_TEXT
    font = ImageFont.truetype(FONT_PATH, font_size)

    # Calculate the maximum pixel width available for text
    max_width = box_width

    # Split the text into words and wrap it based on the actual pixel width
    wrapped_lines = []
    current_line = ""

    for word in abilities_text.split():
        # Test if the word can be added to the current line
        test_line = current_line + " " + word if current_line else word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            # Add the current line to wrapped_lines and start a new one
            wrapped_lines.append(current_line)
            current_line = word

    # Add the last line
    if current_line:
        wrapped_lines.append(current_line)

    # Calculate the height of the text block
    text_height = len(wrapped_lines) * (font_size + 10)

    # Adjust font size if text is too tall to fit in the box
    while text_height > box_height and font_size > 10:
        font_size -= 2
        font = ImageFont.truetype(FONT_PATH, font_size)
        wrapped_lines = []
        current_line = ""
        for word in abilities_text.split():
            test_line = current_line + " " + word if current_line else word
            if draw.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word
        if current_line:
            wrapped_lines.append(current_line)
        text_height = len(wrapped_lines) * (font_size + 10)

    # Calculate the starting Y position for vertical centering
    current_y = y + top_padding

    # Draw each line of wrapped text
    for line in wrapped_lines:
        draw.text((x, current_y), line, font=font, fill="black")
        current_y += font_size + 10

def draw_card_title(card, draw, card_name, mana_cost, x_offset=120, y_offset=111, box_width=1272, box_height=96):
    # Set initial font size and load the font
    font_size = FONT_SIZE_TITLE
    font = ImageFont.truetype(FONT_PATH, font_size)

    # Calculate the maximum pixel width available for the title text
    max_width = box_width - 10  # Adjust for a small margin

    # Draw the card name
    draw.text((x_offset, y_offset), card_name, font=font, fill="black")

    # Calculate the width of the mana cost string
    mana_cost_width = sum([draw.textlength(symbol, font=font) for symbol in mana_cost])

    # Calculate the vertical position to center the mana cost
    mana_cost_height = draw.textbbox((0, 0), mana_cost[0], font=font)[3] - draw.textbbox((0, 0), mana_cost[0], font=font)[1]
    mana_y = y_offset + (box_height - mana_cost_height) // 2

    # Right-align the mana cost within the title box
    mana_x = x_offset + max_width - mana_cost_width  # Align to the right edge
    draw_mana_cost(card, draw, mana_cost, mana_x, mana_y)

# def replace_mana_symbols(text):
#     # Replace mana symbols with their respective Unicode or emoji equivalents
#     replacements = {
#         "{1}": "1",  # Numeric mana (1 colorless)
#         "{2}": "2",  # Numeric mana (2 colorless)
#         "{3}": "3",  # Numeric mana (3 colorless)
#         "{4}": "4",  # Numeric mana (4 colorless)
#         "{5}": "5",  # Numeric mana (5 colorless)
#         "{T}": "↻",  # Tap symbol
#         "{W}": "⚪️",  # White mana
#         "{U}": "🔵",  # Blue mana
#         "{B}": "⚫️",  # Black mana
#         "{R}": "🔴",  # Red mana
#         "{G}": "🟢",  # Green mana
#         "{C}": "⚪️",  # Colorless mana
#         # "{T}": "T",  # Tap symbol
#         # "{W}": "W",  # White mana
#         # "{U}": "U",  # Blue mana
#         # "{B}": "B",  # Black mana
#         # "{R}": "R",  # Red mana
#         # "{G}": "G",  # Green mana
#         # "{C}": "1",  # Colorless mana
#     }
#
#     for key, value in replacements.items():
#         text = text.replace(key, value)
#
#     return text

def load_frame_for_card_type(card_type, color):
    # Determine the path to the appropriate frame image based on the card type and color
    if card_type == 'Creature':
        frame_path = os.path.join(CREATURE_FRAME_DIR, f"{color.lower()}.png")
    else:
        frame_path = os.path.join(FRAME_DIR, f"{color.lower()}.png")
    return frame_path

def generate_card_text(card_type):
    prompt = (
        f"Generate a Magic: The Gathering {card_type} card with the following attributes: "
        f"Name, Mana Cost, Type, Abilities, Power/Toughness (if applicable), Flavor Text, Rarity, and Color. "
        f"Return the response as a JSON object with the following keys: "
        f"'name', 'mana_cost', 'type', 'abilities', 'power_toughness', 'flavor_text', 'rarity', and 'color'. "
        f"Ensure that the JSON keys are in lowercase.  Colorless, non-artifact cards must return color as 'void'.  Artifact cards need to return color as 'artifact'.  Mana costs must have symbols enclosed in curly braces."
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

    card_text = response['choices'][0]['message']['content']

    # Clean up the response by removing backticks and json formatting
    card_text = card_text.strip()
    if card_text.startswith("```json"):
        card_text = card_text[7:]  # Remove ```json prefix
    if card_text.endswith("```"):
        card_text = card_text[:-3]  # Remove ``` suffix

    try:
        # Parse the cleaned JSON response
        card_data = json.loads(card_text)
        # Normalize keys to lowercase
        card_data = {k.lower(): v for k, v in card_data.items()}
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        raise ValueError("Failed to parse card text as JSON. Please check the format of the AI output.")

    return card_data

def generate_card_art(description):
    dalle_response = openai.Image.create(
        prompt=description,
        n=1,
        size="1024x1024"
    )
    return dalle_response['data'][0]['url']

def draw_card_type(draw, card_type, x_offset=147, y_offset=1197):
    # Type line Area (below the art)
    type_area = [x_offset, y_offset, CARD_WIDTH - x_offset, 1330]  # Moved down slightly to start at (160, 1180)
    draw.text((type_area[0], type_area[1]), card_type, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TYPE), fill="black")

def draw_mana_cost(card, draw, mana_cost, x, y):
    elements = replace_mana_symbols(mana_cost, symbol_size=(70, 70))  # Adjust size as needed

    for element in elements:
        if isinstance(element, Image.Image):
            card.paste(element, (int(x), int(y)), element)
            x += element.width + 5
        else:
            draw.text((int(x), int(y)), element, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE), fill="black")
            x += draw.textbbox((0, 0), element, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE))[2] + 5

def create_template(card, draw, card_data, card_art):
    # Load and paste the appropriate frame
    frame_path = load_frame_for_card_type(card_data['type'], card_data['color'])
    frame = Image.open(frame_path)
    card.paste(frame, (0, 0))

    # Art Area (large black rectangle in the frame)
    art_area = [117, 237, 1383, 1164]
    art_width = art_area[2] - art_area[0]
    art_height = art_area[3] - art_area[1]

    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        # Resize and crop the art image to fit
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

def generate_card():
    card_type = random.choice(CARD_TYPES)
    print(f"Generating a {card_type} card...")

    # Generate card text as JSON using OpenAI
    card_data = generate_card_text(card_type)
    print("Generated Card Data:")
    print(json.dumps(card_data, indent=2))

    # Generate card art using OpenAI DALL-E
    image_description = f"Artwork for a {card_type} Magic: The Gathering card based on the generated text"
    card_art_url = generate_card_art(image_description)
    print("Generated Card Art URL:")
    print(card_art_url)

    # Create a blank card template and render the card
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(card)
    create_template(card, draw, card_data, card_art_url)

    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Save the generated card as a PNG file in the "cards" directory
    output_filename = os.path.join(OUTPUT_DIR, f"{card_data['name'].replace(' ', '_')}_{card_type}.png")
    card.save(output_filename, "PNG")
    print(f"Card saved as {output_filename}")

if __name__ == "__main__":
    generate_card()

