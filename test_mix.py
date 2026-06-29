import subprocess

def test_mix():
    cmd = [
        "ffmpeg", "-y",
        "-i", "output/test_grave.mp3",
        "-i", "data/bg_music.mp3",
        "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.08[bg];[v][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[a]",
        "-t", "10",
        "output/test_mixed.mp3"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(r.stdout)
    print("STDERR:")
    print(r.stderr)

if __name__ == "__main__":
    test_mix()
