#!/usr/bin/env python3
import os
import openai
import random
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import json

# Read API key from a file
with open("openai_api_key.txt", "r") as file:
    openai.api_key = file.read().strip()

# Define dimensions
CARD_WIDTH = 750
CARD_HEIGHT = 1050
MARGIN = 50

# Font settings
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_SIZE_TITLE = 40
FONT_SIZE_TEXT = 24
FONT_SIZE_PT = 36

# Define available card types
CARD_TYPES = ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Planeswalker', 'Land']

# Directory to save cards
OUTPUT_DIR = "cards"

# Directory containing your background images
ART_FRAMES_DIR = "art/frames"

def generate_card_text(card_type):
    prompt = (
        f"Generate a Magic: The Gathering {card_type} card with the following attributes: "
        f"Name, Mana Cost, Type, Abilities, Power/Toughness (if applicable), Flavor Text, and Rarity. "
        f"Return the response as a JSON object with the following keys: "
        f"'name', 'mana_cost', 'type', 'abilities', 'power_toughness', 'flavor_text', and 'rarity'. "
        f"Ensure that the JSON keys are in lowercase."
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

def draw_title_and_type(draw, card_name, mana_cost, card_type):
    draw.text((MARGIN, MARGIN), card_name, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE), fill="black")
    draw_mana_cost(draw, mana_cost, CARD_WIDTH - MARGIN - 200, MARGIN)
    draw.text((MARGIN, MARGIN + FONT_SIZE_TITLE + 30), card_type, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")

def draw_abilities(draw, abilities, abilities_area):
    lines = abilities.split('\n')
    y_text = abilities_area[1]
    for line in lines:
        draw.text((abilities_area[0], y_text), line, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")
        y_text += FONT_SIZE_TEXT + 5

def draw_mana_cost(draw, mana_cost, x, y):
    symbols = {
        'W': 'W.png',  # White mana
        'U': 'U.png',  # Blue mana
        'B': 'B.png',  # Black mana
        'R': 'R.png',  # Red mana
        'G': 'G.png',  # Green mana
        'C': 'C.png',  # Colorless mana
        # Add paths for numbers as well, e.g., '1': '1.png', '2': '2.png', etc.
    }
    for symbol in mana_cost:
        if symbol in symbols:
            symbol_img = Image.open(os.path.join(ART_FRAMES_DIR, symbols[symbol]))
            symbol_img = symbol_img.resize((40, 40))  # Adjust size as necessary
            card.paste(symbol_img, (x, y), symbol_img)  # Paste symbol with transparency
            x += 45  # Move x position for the next symbol

def create_template(card, draw, card_type, card_art, abilities, power_toughness="", flavor_text="", mana_cost=""):
    # Load and paste the appropriate background image
    background = load_background_image(card_type, mana_cost)
    card.paste(background, (0, 0))

    # Default areas for common attributes
    art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
    abilities_area = [MARGIN, CARD_HEIGHT - MARGIN - 200, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN - 50]
    power_toughness_area = None
    flavor_text_area = [MARGIN, CARD_HEIGHT - MARGIN - 100, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN - 50]

    if card_type == 'Creature':
        power_toughness_area = [CARD_WIDTH - MARGIN - 100, CARD_HEIGHT - MARGIN - 150]
    elif card_type in ['Instant', 'Sorcery']:
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 400]
        abilities_area = art_area
        flavor_text_area = None  # Usually no flavor text for these cards
    elif card_type == 'Enchantment':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 400]
    elif card_type == 'Artifact':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 450]
    elif card_type == 'Planeswalker':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
    elif card_type == 'Land':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]

    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw_abilities(draw, abilities, abilities_area)

    if power_toughness and power_toughness_area:
        draw.text(power_toughness_area, power_toughness, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_PT), fill="black")
    if flavor_text and flavor_text_area:
        draw.text(flavor_text_area, flavor_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black", align="center")

def load_background_image(card_type, mana_cost):
    if card_type == 'Land':
        return Image.open(os.path.join(ART_FRAMES_DIR, 'land.png'))
    elif card_type == 'Artifact':
        return Image.open(os.path.join(ART_FRAMES_DIR, 'artifact.png'))
    elif card_type == 'Creature':
        # Determine color-specific background for creatures
        color = determine_card_color(mana_cost)
        return Image.open(os.path.join(ART_FRAMES_DIR, 'creature', f'{color}.png'))
    else:
        # Determine color-specific background for other card types
        color = determine_card_color(mana_cost)
        return Image.open(os.path.join(ART_FRAMES_DIR, f'{color}.png'))

def determine_card_color(mana_cost):
    if 'W' in mana_cost:
        return "white"
    elif 'U' in mana_cost:
        return "blue"
    elif 'B' in mana_cost:
        return "black"
    elif 'R' in mana_cost:
        return "red"
    elif 'G' in mana_cost:
        return "green"
    else:
        return "artifact"  # Default for artifacts, lands, etc.

def generate_card():
    card_type = random.choice(CARD_TYPES)
    print(f"Generating a {card_type} card...")

    # Generate card text as JSON using OpenAI
    card_data = generate_card_text(card_type)
    print("Generated Card Data:")
    print(json.dumps(card_data, indent=2))

    # Extract card details from the parsed JSON
    card_name = card_data["name"]
    mana_cost = card_data["mana_cost"]
    type_line = card_data["type"]
    abilities = "\n".join(card_data["abilities"])
    flavor_text = card_data.get("flavor_text", "")
    power_toughness = card_data.get("power_toughness", "")

    # Generate card art using OpenAI DALL-E
    image_description = f"Artwork for a {card_type} Magic: The Gathering card based on the generated text"
    card_art_url = generate_card_art(image_description)
    print("Generated Card Art URL:")
    print(card_art_url)

    # Create a blank card template and render the card
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(card)
    create_template(card, draw, card_type, card_art_url, abilities, power_toughness, flavor_text, mana_cost)

    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Save the generated card as a PNG file in the "cards" directory
    output_filename = os.path.join(OUTPUT_DIR, f"{card_name.replace(' ', '_')}_{card_type}.png")
    card.save(output_filename, "PNG")
    print(f"Card saved as {output_filename}")

if __name__ == "__main__":
    generate_card()
