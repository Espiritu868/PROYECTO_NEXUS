import wave
import struct
import math
import random
import os

def generate_bo2_m1911_sound(filename, sample_rate=44100):
    duration = 0.8 # seconds
    num_samples = int(duration * sample_rate)
    audio_data = []
    
    # We will generate a sound that resembles the BO2 starter pistol:
    # It has a "tinny", punchy "crack" with a slight metallic ring,
    # rather than a realistic deep booming .45 ACP sound.
    
    # 1. Generate noise base
    noise = [random.uniform(-1.0, 1.0) for _ in range(num_samples)]
    
    # Simple band-pass filter to give it that "tinny" mid-range BO2 sound
    # We'll use a combination of low-pass and high-pass
    def filter_noise(samples):
        lp = []
        hp = []
        val_lp = 0
        val_hp = 0
        
        for s in samples:
            # Low pass (cut harsh highs)
            val_lp += 0.3 * (s - val_lp)
            lp.append(val_lp)
            
        for s in lp:
            # High pass (cut booming lows to make it tinny)
            val_hp += 0.1 * (s - val_hp)
            hp.append(s - val_hp)
            
        return hp

    noise_filtered = filter_noise(noise)
    
    # 2. Generate the metallic "crack" sweep
    crack_sweep = []
    phase = 0
    start_freq = 2500.0
    end_freq = 600.0
    for i in range(num_samples):
        t = i / sample_rate
        # Fast sweep for the initial pop
        freq = end_freq + (start_freq - end_freq) * math.exp(-t * 60)
        phase += 2 * math.pi * freq / sample_rate
        crack_sweep.append(math.sin(phase))
        
    # 3. Generate a tiny metallic "ring" (like the slide clacking)
    ring = []
    phase_ring = 0
    for i in range(num_samples):
        phase_ring += 2 * math.pi * 1200 / sample_rate
        # Add some slight frequency modulation to make it sound mechanical
        ring.append(math.sin(phase_ring + 0.5 * math.sin(phase_ring * 0.1)))

    for i in range(num_samples):
        t = i / sample_rate
        
        # Envelopes
        # Crack envelope (the sharp pop)
        crack_env = math.exp(-t * 120) if t < 0.05 else 0
        
        # Noise envelope (the main body of the gunshot, short and punchy)
        if t < 0.002:
            noise_env = (t / 0.002)
        else:
            noise_env = math.exp(-(t - 0.002) * 25)
            
        # Ring envelope (the metallic slide sound, delayed very slightly)
        if t < 0.02:
            ring_env = 0
        else:
            ring_env = math.exp(-(t - 0.02) * 15) * 0.15
            
        # Mix
        sample = (
            (crack_sweep[i] * crack_env * 0.7) + 
            (noise_filtered[i] * noise_env * 1.5) +
            (ring[i] * ring_env * 0.8)
        )
        
        # Add a metallic, tight room reverb (characteristic of BO2)
        delay_1 = int(0.015 * sample_rate)
        delay_2 = int(0.035 * sample_rate)
        
        if i > delay_1:
            sample += audio_data[i - delay_1] * 0.3
        if i > delay_2:
            sample += audio_data[i - delay_2] * 0.15
            
        # Hard clipping to give it that compressed, retro game feel
        sample = max(-1.0, min(1.0, sample * 1.8))
        
        audio_data.append(sample)

    # Normalize volume
    max_amp = max(max(audio_data), abs(min(audio_data)))
    if max_amp > 0:
        audio_data = [s * (0.8 / max_amp) for s in audio_data]

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
    generate_bo2_m1911_sound('sounds/m1911.wav')
    print("Sonido estilo M1911 BO2 generado exitosamente en sounds/m1911.wav")
