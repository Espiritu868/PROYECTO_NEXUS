from scripts.enemigo_base import EnemigoBase

class VillanoL(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            # Usamos el modelo sano del jugador...
            ruta_modelo='assets/modelos/character-j.fbx',
            # ...pero le pegamos la textura del villano L
            ruta_textura='assets/modelos/textures/texture-l.png',
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
            
            # Pose de ataque (Levanta un solo brazo apuntando)
            if not self.brazo_der.isEmpty(): self.brazo_der.setP(-90)
            
            if not self.jugador_objetivo:
                return
                
            # Disparar láser (Rayo instantáneo visual Hitscan)
            origen = self.position + Vec3(0, 1.5, 0)
            destino = self.jugador_objetivo.position + Vec3(0, 1.5, 0)
            dist = (destino - origen).length()
            
            # Dibujamos el láser
            laser = Entity(
                model='cube',
                color=color.rgba(255, 0, 0, 200),
                scale=(0.1, 0.1, dist),
                position=origen + (destino - origen)/2,
                unlit=True
            )
            laser.look_at(destino)
            
            # Desvanece el láser
            laser.animate_color(color.rgba(255, 0, 0, 0), duration=0.3, curve=curve.linear)
            destroy(laser, delay=0.3)
            
            # Daño
            self.jugador_objetivo.vida -= 15
            self.jugador_objetivo.texto_vida.text = f'SALUD: {self.jugador_objetivo.vida}'
            
            if self.jugador_objetivo.vida < 40:
                self.jugador_objetivo.texto_vida.color = color.red
                
            if self.jugador_objetivo.vida <= 0:
                print("¡HAS MUERTO!")
                from ursina import application
                application.quit()