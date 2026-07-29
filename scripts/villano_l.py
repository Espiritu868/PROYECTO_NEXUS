from scripts.enemigo_base import EnemigoBase

class VillanoL(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            ruta_modelo='',
            ruta_textura='',
            base_folder='assets/modelos/villians/mutant2/',
            prefix='Meshy_AI_Knight_Mutant_Optimiz_biped_Animation_',
            **kwargs
        )
        self.vida = 100
        self.velocidad = 10
        self.distancia_ataque = 40 # Francotirador (ataca desde muy lejos)
        self.tiempo_entre_ataques = 2.5 # Dispara cada 2.5 segundos

    def atacar(self):
        from ursina import time, Entity, color, curve, destroy, Vec3
        if time.time() - self.ultimo_ataque > self.tiempo_entre_ataques:
            self.ultimo_ataque = time.time()
            
            
            # Pose de ataque
            if self.actor:
                self.cambiar_animacion('attack', loop=False)
            else:
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(-90)
            
            
            if not self.jugador_objetivo:
                return
                
            # Disparar láser (Rayo instantáneo visual Hitscan)
            origen = self.position + Vec3(0, 1.5, 0)
            destino = self.jugador_objetivo.position + Vec3(0, 1.5, 0)
            direccion = (destino - origen).normalized()
            dist = (destino - origen).length()
            
            # --- COMPROBACIÓN DE LÍNEA DE VISIÓN (Line of Sight) ---
            from ursina import raycast
            hit_vision = raycast(origen, direction=direccion, distance=dist, ignore=(self,))
            
            # Si el rayo choca exactamente con el jugador, hay daño. Si choca con otra cosa (pared) o se pierde, no hay daño.
            if hit_vision.hit and hit_vision.entity == self.jugador_objetivo:
                daño_efectivo = True
            else:
                daño_efectivo = False
                if hit_vision.hit:
                    dist = hit_vision.distance
            
            # Dibujamos el láser
            laser = Entity(
                model='cube',
                color=color.rgba(255, 0, 0, 200),
                scale=(0.1, 0.1, dist),
                position=origen + (direccion * (dist / 2)),
                unlit=True
            )
            laser.look_at(origen + (direccion * dist))
            
            # Desvanece el láser
            laser.animate_color(color.rgba(255, 0, 0, 0), duration=0.3, curve=curve.linear)
            destroy(laser, delay=0.3)
            
            # Aplicar Daño solo si hay visión clara
            if daño_efectivo:
                self.jugador_objetivo.vida -= 15
                self.jugador_objetivo.texto_vida.text = f'SALUD: {self.jugador_objetivo.vida}'
                
                if self.jugador_objetivo.vida < 40:
                    self.jugador_objetivo.texto_vida.color = color.red
                
            if self.jugador_objetivo.vida <= 0:
                print("¡HAS MUERTO!")
                from ursina import application
                application.quit()