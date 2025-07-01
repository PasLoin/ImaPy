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
RESOLUTION = "1024x1024"

# --- SCRIPT ---

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

try:
    subprocess.run(['ffprobe', '-version'], check=True, capture_output=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print("ERREUR : ffprobe (qui fait partie de FFmpeg) n'a pas été trouvé.")
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
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-shortest', temp_video_a
    ]
    subprocess.run(cmd_base, check=True, capture_output=True)

    for i in range(1, len(files)):
        print(f"Étape {i + 1}/{len(files)} : Ajout de '{files[i]}'...")
        
        output_temp = temp_video_b if (i % 2) != 0 else temp_video_a
        input_temp = temp_video_a if (i % 2) != 0 else temp_video_b

        duree_entree = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_temp
        ]).strip())

        new_total_duration = duree_entree + DUREE_IMAGE - DUREE_FONDU
        fade_offset = duree_entree - DUREE_FONDU

        # ---- DÉBUT DE LA CORRECTION FINALE ----
        # On normalise les deux flux vidéo à la même cadence (FRAME_RATE) AVANT de les passer à xfade.
        # [0:v] -> fps -> [v0]
        # [1:v] -> fps -> [v1]
        # [v0][v1] -> xfade -> [v_out]
        filter_graph = (
            f'[0:v]fps={FRAME_RATE}[v0];'
            f'[1:v]fps={FRAME_RATE}[v1];'
            f'[v0][v1]xfade=transition=fade:duration={DUREE_FONDU}:offset={fade_offset}[v_out];'
            f'[0:a]apad=whole_len={new_total_duration}[a_out]'
        )
        map_video = '[v_out]'
        map_audio = '[a_out]'
        # ---- FIN DE LA CORRECTION FINALE ----

        cmd_merge = [
            'ffmpeg', '-y',
            '-i', input_temp,
            '-loop', '1', '-t', str(DUREE_IMAGE), '-i', files[i],
            '-filter_complex', filter_graph,
            '-map', map_video, '-map', map_audio,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
            '-c:a', 'aac', '-b:a', '192k', # Spécifier l'encodeur audio est une bonne pratique
            output_temp
        ]
        
        subprocess.run(cmd_merge, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    final_temp_file = temp_video_b if (len(files)-1) % 2 != 0 else temp_video_a
    if os.path.exists(final_temp_file):
        if os.path.exists(OUTPUT_FILE):
             os.remove(OUTPUT_FILE)
        shutil.move(final_temp_file, OUTPUT_FILE)

    print(f"\n✅ Terminé ! La vidéo a été sauvegardée sous le nom : {OUTPUT_FILE}")

except subprocess.CalledProcessError as e:
    print("\n❌ ERREUR : FFmpeg a rencontré un problème.")
    print(f"La commande '{' '.join(e.cmd)}' a échoué.")
    # Si stderr a été capturé, l'afficher
    if hasattr(e, 'stderr') and e.stderr:
        print("Sortie d'erreur de FFmpeg :\n---")
        print(e.stderr)
        print("---")

finally:
    # Nettoyage
    if os.path.exists(temp_video_a):
        os.remove(temp_video_a)
    if os.path.exists(temp_video_b):
        os.remove(temp_video_b)
