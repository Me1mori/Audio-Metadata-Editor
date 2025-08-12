import os

AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}

def is_audio_file(filepath: str) -> bool:
    _, ext = os.path.splitext(filepath)
    return ext.lower() in AUDIO_EXTENSIONS

def get_audio_files_in_folder(folder: str) -> list[str]:
    audios = []
    for root, _, files in os.walk(folder):
        for file in files:
            if is_audio_file(file):
                audios.append(os.path.join(root, file))
    return audios

