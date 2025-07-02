import os
import subprocess
import glob
import re
import shutil

# --- PARAMÈTRES ---
OUTPUT_FILE = "ma_video_finale.mp4"
DUREE_IMAGE = 1
DUREE_FONDU = 0.5
FRAME_RATE = 25

# --- OPTIONS D'ENCODAGE POUR COMPATIBILITÉ MAXIMALE ---
VIDEO_ENCODING_OPTIONS = [
    '-c:v', 'libx264',
    '-profile:v', 'main',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
]

# --- SCRIPT ---

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

try:
    # LA CORRECTION EST ICI : on a retiré le ", stderr=subprocess.PIPE" redondant
    subprocess.run(['ffprobe', '-version'], check=True, capture_output=True, text=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print("ERREUR : ffprobe (qui fait partie de FFmpeg) n'a pas été trouvé.")
    print("Veuillez installer FFmpeg et vous assurer qu'il est dans le PATH de votre système.")
    exit()

print("Recherche des images...")
files = sorted(glob.glob('image_*.png'), key=natural_sort_key)

if len(files) < 2:
    print("ERREUR : Il faut au moins deux images pour créer une vidéo.")
    exit()

print(f"{len(files)} images trouvées. Lancement du processus séquentiel...")

temp_video_a = "temp_a.mp4"
temp_video_b = "temp_b.mp4"

try:
    print("Étape 1 : Création de la vidéo de base avec la première image.")
    duree_initiale = DUREE_IMAGE - DUREE_FONDU
    
    cmd_base = [
        'ffmpeg', '-y',
        '-loop', '1', '-t', str(duree_initiale), '-i', files[0],
        '-f', 'lavfi', '-t', str(duree_initiale), '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
        *VIDEO_ENCODING_OPTIONS,
        '-shortest', temp_video_a
    ]
    subprocess.run(cmd_base, check=True, capture_output=True, text=True)

    for i in range(1, len(files)):
        print(f"Étape {i + 1}/{len(files)} : Ajout de '{files[i]}'...")
        
        output_temp = temp_video_b if (i % 2) != 0 else temp_video_a
        input_temp = temp_video_a if (i % 2) != 0 else temp_video_b

        duree_entree_bytes = subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_temp
        ])
        duree_entree = float(duree_entree_bytes.strip())

        new_total_duration = duree_entree + DUREE_IMAGE - DUREE_FONDU
        fade_offset = duree_entree - DUREE_FONDU

        filter_graph = (
            f'[0:v]fps={FRAME_RATE}[v0];'
            f'[1:v]fps={FRAME_RATE}[v1];'
            f'[v0][v1]xfade=transition=fade:duration={DUREE_FONDU}:offset={fade_offset}[v_out];'
            f'anullsrc=channel_layout=stereo:sample_rate=44100,atrim=duration={new_total_duration}[a_out]'
        )
        
        cmd_merge = [
            'ffmpeg', '-y',
            '-i', input_temp,
            '-loop', '1', '-t', str(DUREE_IMAGE), '-i', files[i],
            '-filter_complex', filter_graph,
            '-map', '[v_out]', '-map', '[a_out]',
            *VIDEO_ENCODING_OPTIONS,
            '-c:a', 'aac', '-b:a', '192k',
            output_temp
        ]
        
        subprocess.run(cmd_merge, check=True, capture_output=True, text=True)

    final_temp_file = temp_video_b if (len(files)-1) % 2 != 0 else temp_video_a
    if os.path.exists(final_temp_file):
        if os.path.exists(OUTPUT_FILE):
             os.remove(OUTPUT_FILE)
        shutil.move(final_temp_file, OUTPUT_FILE)

    print(f"\n✅ Terminé ! La vidéo a été sauvegardée sous le nom : {OUTPUT_FILE}")

except subprocess.CalledProcessError as e:
    print("\n❌ ERREUR : FFmpeg a rencontré un problème.")
    print(f"La commande qui a échoué était : \n{' '.join(e.cmd)}")
    print("\n--- Sortie d'erreur de FFmpeg ---")
    print(e.stderr)
    print("---------------------------------")


finally:
    # Nettoyage
    print("Nettoyage des fichiers temporaires...")
    if os.path.exists(temp_video_a):
        os.remove(temp_video_a)
    if os.path.exists(temp_video_b):
        os.remove(temp_video_b)
