import wave
import struct
import math
import random
import os

def generate_glock17_sound(filename, sample_rate=44100):
    duration = 0.6 # seconds (Glock sound is very short and snappy)
    num_samples = int(duration * sample_rate)
    audio_data = []
    
    # 9mm Glock 17 has a very sharp, dry "crack" with a short punchy thump.
    
    # 1. Generate base noise
    noise = [random.uniform(-1.0, 1.0) for _ in range(num_samples)]
    
    # 2. Thump (Slightly higher pitch and faster decay than a .45 ACP)
    thump = []
    phase = 0
    start_freq = 180.0
    end_freq = 50.0
    for i in range(num_samples):
        t = i / sample_rate
        freq = end_freq + (start_freq - end_freq) * math.exp(-t * 50)
        phase += 2 * math.pi * freq / sample_rate
        thump.append(math.sin(phase))

    # 3. High pitched snap (the 9mm crack)
    snap = []
    phase_snap = 0
    start_snap = 3500.0
    end_snap = 800.0
    for i in range(num_samples):
        t = i / sample_rate
        freq = end_snap + (start_snap - end_snap) * math.exp(-t * 100)
        phase_snap += 2 * math.pi * freq / sample_rate
        snap.append(math.sin(phase_snap))

    for i in range(num_samples):
        t = i / sample_rate
        
        # Envelopes
        # Snap envelope (extremely fast, sharp attack)
        snap_env = math.exp(-t * 180) if t < 0.03 else 0
        
        # Noise envelope (punchy and short, no long tail)
        if t < 0.001:
            noise_env = (t / 0.001)
        else:
            noise_env = math.exp(-(t - 0.001) * 35)
            
        # Thump envelope (short bass impact)
        thump_env = math.exp(-t * 30)
        
        # Mix
        sample = (
            (snap[i] * snap_env * 0.9) + 
            (noise[i] * noise_env * 1.2) +
            (thump[i] * thump_env * 0.7)
        )
        
        # Add a very subtle, dry room reflection (Glocks sound 'dry')
        delay = int(0.01 * sample_rate)
        if i > delay:
            sample += audio_data[i - delay] * 0.15
            
        # Hard clipping to compress the gunshot like a real recording
        sample = max(-1.0, min(1.0, sample * 1.5))
        
        audio_data.append(sample)

    # Normalize volume
    max_amp = max(max(audio_data), abs(min(audio_data)))
    if max_amp > 0:
        audio_data = [s * (0.85 / max_amp) for s in audio_data]

    # Write to wav file
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for sample in audio_data:
            int_sample = int(sample * 32767.0)
            int_sample = max(-32768, min(32767, int_sample))
            wav_file.writeframes(struct.pack('<h', int_sample))

if __name__ == '__main__':
    generate_glock17_sound('sounds/glock17.wav')
    print("Sonido estilo Glock 17 generado exitosamente en sounds/glock17.wav")
