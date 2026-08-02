from ursina import Entity, color, distance, held_keys, time, invoke, Text, destroy, curve
import random

class CajaMisteriosa(Entity):
    def __init__(self, posiciones_spawn, parent_visual, **kwargs):
        self.posiciones_spawn = posiciones_spawn
        self.posicion_actual_idx = random.randint(0, len(posiciones_spawn) - 1)
        pos = self.posiciones_spawn[self.posicion_actual_idx]
        
        super().__init__(
            parent=parent_visual,
            model='assets/modelos/objetos_con_meshy/objetos/boxclose.glb',
            position=pos,
            scale=1.5,
            collider='box',
            **kwargs
        )
        self.costo = 750
        self.estado = 'cerrada' # cerrada, girando, abierta, moviendose
        self.usos_restantes = 7
        self.arma_mostrada = None
        self.arma_visual = None
        self.texto_info = None
        
        self.armas_disponibles = [
            {'id': 'raygun', 'modelo': 'assets/modelos/objetos_con_meshy/armas/raygun.glb'},
            {'id': 'raygun_mk2', 'modelo': 'assets/modelos/objetos_con_meshy/armas/raygun_markII.glb'},
            {'id': 'scar', 'modelo': 'assets/modelos/objetos_con_meshy/armas/scar.glb'}
        ]
        
        # PRE-CARGA EN RAM (Evita tirones cuando giran las armas por primera vez)
        self.cache_entidades = []
        for arma in self.armas_disponibles:
            self.cache_entidades.append(Entity(model=arma['modelo'], enabled=False))
        self.cache_entidades.append(Entity(model='assets/modelos/objetos_con_meshy/objetos/boxopen.glb', enabled=False))
        
    def update(self):
        if self.estado == 'moviendose': return
        
        from scripts.jugador import Jugador
        jugador = Jugador.instancia
        if not jugador or jugador.esta_muerto: 
            self.ocultar_texto()
            return
            
        dist = distance(self.world_position, jugador.world_position)
        
        if dist < 5:
            if self.estado == 'cerrada':
                self.mostrar_texto(f"Presiona [E] Caja Misteriosa (Costo: {self.costo})")
            elif self.estado == 'abierta':
                self.mostrar_texto("Presiona [E] para tomar el arma")
            else:
                self.ocultar_texto()
        else:
            self.ocultar_texto()

    def input(self, key):
        if key == 'e':
            if self.estado == 'moviendose': return
            
            from scripts.jugador import Jugador
            jugador = Jugador.instancia
            if not jugador or jugador.esta_muerto: return
            
            dist = distance(self.world_position, jugador.world_position)
            if dist < 5:
                if self.estado == 'cerrada':
                    if jugador.monedas >= self.costo:
                        jugador.ganar_monedas(-self.costo)
                        self.usos_restantes -= 1
                        if self.usos_restantes <= 0:
                            self.iniciar_movimiento()
                        else:
                            self.iniciar_giro()
                    else:
                        self.mostrar_texto("<red>No tienes suficientes monedas")
                elif self.estado == 'abierta':
                    self.entregar_arma(jugador)

    def iniciar_giro(self):
        self.estado = 'girando'
        self.model = 'assets/modelos/objetos_con_meshy/objetos/boxopen.glb'
        self.ocultar_texto()
        
        self.tiempo_giro = 5.0
        self.inicio_giro = time.time()
        
        self.arma_visual = Entity(parent=self, position=(0, -0.5, 0), scale=0.3)
        self.arma_visual.animate_position((0, 1.5, 0), duration=1.0)
        
        self.rotar_armas_falsas()
        
    def rotar_armas_falsas(self):
        if self.estado != 'girando': return
        
        if time.time() - self.inicio_giro > self.tiempo_giro:
            self.seleccionar_arma_final()
            return
            
        arma_aleatoria = random.choice(self.armas_disponibles)
        self.arma_visual.model = arma_aleatoria['modelo']
        
        invoke(self.rotar_armas_falsas, delay=0.15)
        
    def seleccionar_arma_final(self):
        self.arma_mostrada = random.choice(self.armas_disponibles)
        self.arma_visual.model = self.arma_mostrada['modelo']
        self.estado = 'abierta'
        
        # El arma se queda 12 segundos, si no la tomas, se guarda
        invoke(self.cerrar_caja, delay=12.0)

    def entregar_arma(self, jugador):
        if not self.arma_mostrada: return
        
        arma_nueva = Entity(model=self.arma_mostrada['modelo'])
        jugador.equipar_arma(modelo_existente=arma_nueva, id_arma=self.arma_mostrada['id'])
        
        self.arma_mostrada = None
        self.cerrar_caja()

    def cerrar_caja(self):
        if self.estado == 'cerrada' or self.estado == 'moviendose': return
        self.estado = 'cerrada'
        self.model = 'assets/modelos/objetos_con_meshy/objetos/boxclose.glb'
        if self.arma_visual:
            destroy(self.arma_visual)
            self.arma_visual = None

    def iniciar_movimiento(self):
        self.estado = 'moviendose'
        self.ocultar_texto()
        
        # Animación de despedida (juguete/arma flotando que luego se va volando o la caja se hunde)
        self.model = 'assets/modelos/objetos_con_meshy/objetos/boxopen.glb'
        
        self.arma_visual = Entity(parent=self, model='assets/modelos/objetos_con_meshy/armas/raygun.glb', position=(0, -0.5, 0), scale=0.3)
        self.arma_visual.animate_position((0, 2.5, 0), duration=2.0)
        self.arma_visual.animate_rotation_y(720, duration=2.0)
        
        invoke(self.reaparecer_nueva_ubicacion, delay=2.0)

    def reaparecer_nueva_ubicacion(self):
        # Seleccionar un punto distinto al actual
        posiciones_posibles = [i for i in range(len(self.posiciones_spawn)) if i != self.posicion_actual_idx]
        self.posicion_actual_idx = random.choice(posiciones_posibles)
        nueva_pos = self.posiciones_spawn[self.posicion_actual_idx]
        
        if self.arma_visual:
            destroy(self.arma_visual)
            self.arma_visual = None
            
        # Resetear estado y usos
        self.position = nueva_pos + (0, 15, 0) # Aparece en el cielo y cae
        self.usos_restantes = 7
        self.model = 'assets/modelos/objetos_con_meshy/objetos/boxclose.glb'
        
        # Cae del cielo
        self.animate_position(nueva_pos, duration=1.5, curve=curve.out_bounce)
        
        invoke(self.finalizar_reaparicion, delay=1.5)
        
    def finalizar_reaparicion(self):
        self.estado = 'cerrada'
        
    def mostrar_texto(self, msj):
        if not self.texto_info:
            self.texto_info = Text(text=msj, position=(-0.3, -0.25), scale=1.2, color=color.yellow)
        else:
            self.texto_info.text = msj
            self.texto_info.enabled = True
            
    def ocultar_texto(self):
        if self.texto_info:
            self.texto_info.enabled = False
