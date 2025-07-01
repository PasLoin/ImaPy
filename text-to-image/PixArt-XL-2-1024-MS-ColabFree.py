!pip install diffusers transformers sentencepiece accelerate

import torch
from diffusers import PixArtAlphaPipeline
import gc
from PIL import Image
import zipfile
import io
import os

# Initialisation du pipeline
pipe = PixArtAlphaPipeline.from_pretrained("PixArt-alpha/PixArt-XL-2-1024-MS", torch_dtype=torch.float16)
pipe = pipe.to('cuda')

# Liste de prompts
prompts = [
    "a man in a bowler hat floating above the Atomium, holding a green apple, in the style of René Magritte, surreal atmosphere, photorealistic",
    "a giant floating pipe casting a shadow over the Grand-Place in Brussels, blue cloudy sky, in the style of René Magritte, high detail",
    "a train emerging from a fireplace in the Royal Library of Belgium, mysterious lighting, in the style of René Magritte, photorealistic",
    "a rain of umbrellas over the Manneken Pis statue, each umbrella transparent, in the style of René Magritte, surreal, detailed",
    "a faceless man standing in front of the Palais de Justice, his face replaced by a white dove, in the style of René Magritte, photorealistic",
    "a giant egg resting on the steps of the Brussels Stock Exchange, early morning fog, in the style of René Magritte, surreal, high resolution",
    "a floating castle above Place Sainte-Catherine, reflected perfectly in a puddle, in the style of René Magritte, photorealistic",
    "a window frame standing alone in Parc du Cinquantenaire, showing a sunny sky while it rains outside, in the style of René Magritte, detailed",
    "a bowler hat hovering over a plate of Belgian fries on a café table, cloudy sky background, in the style of René Magritte, surreal, photorealistic",
    "a large apple blocking the entrance of the Brussels Central Station, commuters walking around it, in the style of René Magritte, surreal, high detail"
]


# Liste pour stocker les images
images = []

# Paramètres de génération d'images
height = 1024  # Hauteur de l'image
width = 576    # Largeur de l'image pour un ratio 9:16
num_inference_steps = 30  # Nombre d'étapes de diffusion
guidance_scale = 7.5  # Guidage pour la génération d'images

# Génération des images
for i, prompt in enumerate(prompts):
    image = pipe(
        prompt,
        height=height,
        width=width,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale
    ).images[0]

    # Affichage de l'image
    display(image)

    # Sauvegarde de l'image dans la liste
    images.append(image)

    # Nettoyage de la RAM
    gc.collect()
    torch.cuda.empty_cache()

# Nettoyage final de la RAM
gc.collect()
torch.cuda.empty_cache()

# Sauvegarde des images dans un fichier ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
    for i, image in enumerate(images):
        # Sauvegarde de l'image dans un buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        # Ajout de l'image au fichier ZIP
        zip_file.writestr(f"image_{i}.png", img_buffer.read())

# Sauvegarde du fichier ZIP sur le disque
with open("generated_images.zip", "wb") as f:
    f.write(zip_buffer.getvalue())

print("Les images ont été sauvegardées dans generated_images.zip")
