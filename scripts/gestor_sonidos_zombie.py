import random
import time
from ursina import Audio, distance, clamp

class ZombiesAudioManager:
    """
    Gestor Global de Audio para los Zombies (Estilo Black Ops 2).
    Evita que múltiples zombies reproduzcan sonidos idénticos al mismo tiempo
    y controla la atenuación de volumen espacial.
    """
    # Tiempos de última reproducción
    _ultimo_ataque = 0
    _ultimo_ambiente = 0
    _ultimo_frenesi = 0
    
    # Cooldowns globales en segundos para evitar el caos de audio
    COOLDOWN_ATAQUE = 0.8       # Máximo 1 sonido de ataque cada 0.8s
    COOLDOWN_AMBIENTE = 2.5     # Máximo 1 sonido ambiente cada 2.5s
    COOLDOWN_FRENESI = 4.0      # Máximo 1 sonido de frenesí cada 4s
    
    # Pools de audios
    _audios_ambiente = ['assets/sonidos/zombie/zombie_normal.mp3', 'assets/sonidos/zombie/sound3.mp3']
    _audios_ataque = ['assets/sonidos/zombie/attack.mp3', 'assets/sonidos/zombie/attack2.mp3']
    _audios_frenesi = ['assets/sonidos/zombie/zombie_loco.mp3', 'assets/sonidos/zombie/zombie_loco_extend.mp3', 'assets/sonidos/zombie/zombie_loco_extend2.mp3']

    @classmethod
    def _calcular_volumen(cls, emisor, receptor=None):
        """Calcula el volumen basado en la distancia del zombie al jugador."""
        if not emisor:
            return 0
        if not receptor:
            if hasattr(emisor, 'jugador_objetivo') and emisor.jugador_objetivo:
                receptor = emisor.jugador_objetivo
            else:
                from scripts.jugador import Jugador
                receptor = Jugador.instancia
                
        if not receptor:
            return 1.0 
            
        dist = distance(emisor, receptor)
        
        # Atenuación de volumen: 1.0 a 2 metros, 0.0 a 35 metros
        rango_max = 35.0
        rango_min = 2.0
        
        if dist <= rango_min:
            return 1.0
        elif dist >= rango_max:
            return 0.0
            
        vol = 1.0 - ((dist - rango_min) / (rango_max - rango_min))
        # Curva cuadrática suave para que el sonido decaiga más realista
        return clamp(vol * vol, 0, 1)

    @classmethod
    def solicitar_sonido_ambiente(cls, emisor):
        """Un zombie intenta reproducir su sonido de ambiente/caminata."""
        ahora = time.time()
        if ahora - cls._ultimo_ambiente >= cls.COOLDOWN_AMBIENTE:
            volumen = cls._calcular_volumen(emisor)
            # Solo reproducimos si está lo suficientemente cerca para escucharse
            if volumen > 0.01:
                archivo = random.choice(cls._audios_ambiente)
                Audio(archivo, autoplay=True, loop=False, volume=volumen * 0.75)
                cls._ultimo_ambiente = ahora

    @classmethod
    def solicitar_sonido_ataque(cls, emisor):
        """Un zombie intenta reproducir un sonido al atacar."""
        ahora = time.time()
        if ahora - cls._ultimo_ataque >= cls.COOLDOWN_ATAQUE:
            volumen = cls._calcular_volumen(emisor)
            if volumen > 0.01:
                archivo = random.choice(cls._audios_ataque)
                Audio(archivo, autoplay=True, loop=False, volume=volumen * 1.2)
                cls._ultimo_ataque = ahora

    @classmethod
    def solicitar_sonido_frenesi(cls, emisor):
        """Un zombie se vuelve rápido/loco y pega un grito extendido."""
        ahora = time.time()
        if ahora - cls._ultimo_frenesi >= cls.COOLDOWN_FRENESI:
            volumen = cls._calcular_volumen(emisor)
            if volumen > 0.01:
                archivo = random.choice(cls._audios_frenesi)
                Audio(archivo, autoplay=True, loop=False, volume=volumen)
                cls._ultimo_frenesi = ahora
