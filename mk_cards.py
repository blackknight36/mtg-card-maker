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

def generate_card_text(card_type):
    prompt = (
        f"Generate a Magic: The Gathering {card_type} card with the following attributes: "
        f"Name, Mana Cost, Type, Abilities, Power/Toughness (if applicable), Flavor Text, and Rarity. "
        f"Please return the card details in JSON format."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates Magic: The Gathering cards."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response['choices'][0]['message']['content']

def generate_card_art(description):
    dalle_response = openai.Image.create(
        prompt=description,
        n=1,
        size="1024x1024"
    )
    return dalle_response['data'][0]['url']

def parse_card_text(card_text):
    try:
        card_data = json.loads(card_text)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse card text as JSON. Please check the format of the AI output.")
    return card_data

def draw_title_and_type(draw, card_name, mana_cost, card_type):
    draw.text((MARGIN, MARGIN), card_name, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE), fill="black")
    draw.text((CARD_WIDTH - MARGIN - 100, MARGIN), mana_cost, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE), fill="black")
    draw.text((MARGIN, MARGIN + FONT_SIZE_TITLE + 30), card_type, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")

def draw_abilities(draw, abilities, abilities_area):
    lines = abilities.split('\n')
    y_text = abilities_area[1]
    for line in lines:
        draw.text((abilities_area[0], y_text), line, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")
        y_text += FONT_SIZE_TEXT + 5

def create_template(card, draw, card_type, card_art, abilities, power_toughness="", flavor_text=""):
    if card_type == 'Creature':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
        abilities_area = [MARGIN, CARD_HEIGHT - MARGIN - 200, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN - 50]
        power_toughness_area = [CARD_WIDTH - MARGIN - 100, CARD_HEIGHT - MARGIN - 150]
        flavor_text_area = [MARGIN, CARD_HEIGHT - MARGIN - 100, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN - 50]
    elif card_type in ['Instant', 'Sorcery']:
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 400]
        abilities_area = art_area
    elif card_type == 'Enchantment':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 400]
        abilities_area = [MARGIN, CARD_HEIGHT - MARGIN - 150, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN]
    elif card_type == 'Artifact':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 450]
        abilities_area = [MARGIN, CARD_HEIGHT - MARGIN - 150, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN]
    elif card_type == 'Planeswalker':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
        abilities_area = [MARGIN, CARD_HEIGHT - MARGIN - 150, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN]
    elif card_type == 'Land':
        art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
        abilities_area = [MARGIN, CARD_HEIGHT - MARGIN - 150, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN]
    else:
        raise ValueError(f"Unknown card type: {card_type}")

    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw_abilities(draw, abilities, abilities_area)

    if power_toughness and card_type == 'Creature':
        draw.text(power_toughness_area, power_toughness, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_PT), fill="black")
    if flavor_text:
        draw.text(flavor_text_area, flavor_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black", align="center")

def generate_card():
    card_type = random.choice(CARD_TYPES)
    print(f"Generating a {card_type} card...")

    # Generate card text as JSON using OpenAI
    card_text = generate_card_text(card_type)
    print("Generated Card Text:")
    print(card_text)

    # Parse the generated card text as JSON
    card_data = parse_card_text(card_text)

    # Extract card details from the parsed JSON
    card_name = card_data["name"]
    mana_cost = card_data["mana_cost"]
    type_line = card_data["type_line"]
    abilities = card_data["abilities"]
    power_toughness = card_data.get("power_toughness", "")
    flavor_text = card_data.get("flavor_text", "")

    # Generate card art using OpenAI DALL-E
    image_description = f"Artwork for a {card_type} Magic: The Gathering card based on the generated text"
    card_art_url = generate_card_art(image_description)
    print("Generated Card Art URL:")
    print(card_art_url)

    # Create a blank card template and render the card
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(card)
    draw_title_and_type(draw, card_name, mana_cost, type_line)
    create_template(card, draw, card_type, card_art_url, abilities, power_toughness, flavor_text)

    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Save the generated card as a PNG file in the "cards" directory
    output_filename = os.path.join(OUTPUT_DIR, f"{card_name.replace(' ', '_')}_{card_type}.png")
    card.save(output_filename, "PNG")
    print(f"Card saved as {output_filename}")

if __name__ == "__main__":
    generate_card()
