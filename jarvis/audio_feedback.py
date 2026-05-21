import os
import pygame
import array
import math

def generate_ping(filename="ping.wav"):
    """Genera un semplice suono 'ping' sinusoidale e lo salva come file WAV."""
    sample_rate = 44100
    duration = 0.2  # secondi
    frequency = 880  # Hz (A5)
    
    # Calcola il numero di campioni
    num_samples = int(sample_rate * duration)
    
    # Genera i campioni della sinusoide con una dissolvenza (fade out)
    samples = []
    for i in range(num_samples):
        # Fade out lineare
        amplitude = 0.5 * (1.0 - i / num_samples)
        # Sinusoide
        val = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
        # Converti in intero a 16 bit
        samples.append(int(val * 32767))
    
    # Crea il file WAV manualmente (header semplice)
    with open(filename, "wb") as f:
        # RIFF header
        f.write(b'RIFF')
        f.write((36 + len(samples) * 2).to_bytes(4, 'little'))
        f.write(b'WAVE')
        
        # fmt chunk
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little')) # chunk size
        f.write((1).to_bytes(2, 'little'))  # PCM
        f.write((1).to_bytes(2, 'little'))  # Mono
        f.write((sample_rate).to_bytes(4, 'little'))
        f.write((sample_rate * 2).to_bytes(4, 'little')) # byte rate
        f.write((2).to_bytes(2, 'little'))  # block align
        f.write((16).to_bytes(2, 'little')) # bits per sample
        
        # data chunk
        f.write(b'data')
        f.write((len(samples) * 2).to_bytes(4, 'little'))
        for s in samples:
            f.write(s.to_bytes(2, 'little', signed=True))

def play_ping():
    """Riproduce il suono ping."""
    ping_file = os.path.join(os.path.dirname(__file__), "ping.wav")
    if not os.path.exists(ping_file):
        generate_ping(ping_file)
    
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    sound = pygame.mixer.Sound(ping_file)
    sound.play()

if __name__ == "__main__":
    pygame.mixer.init()
    play_ping()
    while pygame.mixer.get_busy():
        pygame.time.delay(10)
