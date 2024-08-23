#!/usr/bin/env python3
import os
import openai
import random
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Set your OpenAI API key
openai.api_key = 'sk-svcacct-UUQsmir8TI7k0T8MPKBBPYl11E60gdmcj_9sJBa81iVrjtga-yT3BlbkFJT71RIH1AMmaOeQc-2igeE7Hf69tLTAoEEu-r1uLLCJxU05DCEA'

# Define dimensions
CARD_WIDTH = 750
CARD_HEIGHT = 1050
MARGIN = 50

# Font settings - correct path to Arial font
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
        f"Name, Mana Cost, Type, and Abilities."
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

def draw_title_and_type(draw, card_name, mana_cost, card_type):
    draw.text((MARGIN, MARGIN), card_name, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE), fill="black")
    draw.text((CARD_WIDTH - MARGIN - 100, MARGIN), mana_cost, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TITLE), fill="black")
    draw.text((MARGIN, MARGIN + FONT_SIZE_TITLE + 30), card_type, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")

def create_creature_template(card, draw, card_text, card_art):
    art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw.text((MARGIN, CARD_HEIGHT - MARGIN - 150), card_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")  # Abilities

def create_instant_sorcery_template(card, draw, card_text, card_art):
    text_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, CARD_HEIGHT - MARGIN - 150]
    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((text_area[2] - text_area[0], text_area[3] - text_area[1]))
        card.paste(art_image, (text_area[0], text_area[1]))
    draw.rectangle(text_area, outline="black", width=3)  # Text area
    draw.text((MARGIN, MARGIN + 90), card_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")  # Abilities

def create_enchantment_template(card, draw, card_text, card_art):
    art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 400]
    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw.text((MARGIN, CARD_HEIGHT - MARGIN - 150), card_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")  # Abilities

def create_artifact_template(card, draw, card_text, card_art):
    art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 450]
    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw.text((MARGIN, CARD_HEIGHT - MARGIN - 150), card_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")  # Abilities

def create_planeswalker_template(card, draw, card_text, card_art):
    art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw.text((MARGIN, CARD_HEIGHT - MARGIN - 150), card_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")  # Abilities

def create_land_template(card, draw, card_text, card_art):
    art_area = [MARGIN, MARGIN + 80, CARD_WIDTH - MARGIN, MARGIN + 80 + 512]
    if card_art:
        art_image = Image.open(BytesIO(requests.get(card_art).content))
        art_image = art_image.resize((art_area[2] - art_area[0], art_area[3] - art_area[1]))
        card.paste(art_image, (art_area[0], art_area[1]))
    draw.rectangle(art_area, outline="black", width=3)  # Art area
    draw.text((MARGIN, CARD_HEIGHT - MARGIN - 150), card_text, font=ImageFont.truetype(FONT_PATH, FONT_SIZE_TEXT), fill="black")  # Abilities

def generate_card():
    card_type = random.choice(CARD_TYPES)
    print(f"Generating a {card_type} card...")

    # Generate card text using OpenAI
    card_text = generate_card_text(card_type)
    print("Generated Card Text:")
    print(card_text)

    # Generate card art using OpenAI DALL-E
    image_description = f"Artwork for a {card_type} Magic: The Gathering card based on the generated text"
    card_art_url = generate_card_art(image_description)
    print("Generated Card Art URL:")
    print(card_art_url)

    # Create a blank card template
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(card)

    # Extract the name and mana cost from the generated text for better control (assumes proper formatting)
    card_name = "Generated Name"  # Placeholder, extract from `card_text` appropriately
    mana_cost = "3RR"  # Placeholder, extract from `card_text` appropriately
    card_abilities = "Card abilities text"  # Placeholder, extract from `card_text` appropriately

    # Draw the title and type box
    draw_title_and_type(draw, card_name, mana_cost, card_type)

    # Use the appropriate template based on card type, passing the card art URL
    if card_type == 'Creature':
        create_creature_template(card, draw, card_abilities, card_art_url)
    elif card_type in ['Instant', 'Sorcery']:
        create_instant_sorcery_template(card, draw, card_abilities, card_art_url)
    elif card_type == 'Enchantment':
        create_enchantment_template(card, draw, card_abilities, card_art_url)
    elif card_type == 'Artifact':
        create_artifact_template(card, draw, card_abilities, card_art_url)
    elif card_type == 'Planeswalker':
        create_planeswalker_template(card, draw, card_abilities, card_art_url)
    elif card_type == 'Land':
        create_land_template(card, draw, card_abilities, card_art_url)

    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Save the generated card as a PNG file in the "cards" directory
    output_filename = os.path.join(OUTPUT_DIR, f"{card_name.replace(' ', '_')}_{card_type}.png")
    card.save(output_filename, "PNG")
    print(f"Card saved as {output_filename}")

if __name__ == "__main__":
    generate_card()
