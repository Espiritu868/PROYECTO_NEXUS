import random
from typing import Any, Dict, List, Optional

class PowerUpService:
    def __init__(self, pool_powerups: List[str]):
        """
        Inicializa el gestor de drops.
        :param pool_powerups: Colección de strings/tipos de power-ups disponibles.
        """
        # Reglas de negocio y constantes
        self.UMBRAL_PUNTOS = 2000
        self.LIMITE_POR_RONDA = 4
        self.pool_powerups = pool_powerups
        
        # Estado interno
        self.puntos_acumulados = 0
        self.is_drop_ready = False
        self.drops_en_ronda_actual = 0

    def procesar_muerte_enemigo(self, puntos: int, posicion: Any) -> Optional[Dict[str, Any]]:
        """
        Lógica principal que se ejecuta cada que muere un enemigo.
        Retorna un diccionario con el Drop si las condiciones se cumplen, de lo contrario None.
        """
        # REGLA 4: Hard Limit por Ronda
        if self.drops_en_ronda_actual >= self.LIMITE_POR_RONDA:
            return None

        # REGLA 1: Acumulador de Puntos
        self.puntos_acumulados += puntos

        # REGLA 2: Bandera de Drop (Umbral)
        if self.puntos_acumulados >= self.UMBRAL_PUNTOS:
            self.is_drop_ready = True

        # REGLA 3 y 5: Instanciación y RNG de Selección
        if self.is_drop_ready:
            tipo_powerup = random.choice(self.pool_powerups)
            
            # Desactivar bandera y reiniciar el ciclo conservando los puntos excedentes
            self.is_drop_ready = False
            self.puntos_acumulados -= self.UMBRAL_PUNTOS
            
            # Registrar el drop para el Hard Limit
            self.drops_en_ronda_actual += 1

            return {
                "tipo_powerup": tipo_powerup,
                "posicion": posicion
            }

        return None

    def iniciar_siguiente_ronda(self):
        """
        Debe llamarse externamente cuando inicie una nueva ronda.
        Resetea el Hard Limit de drops permitidos.
        """
        self.drops_en_ronda_actual = 0
