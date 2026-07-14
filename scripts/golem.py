from ursina import Entity, color, time, Vec3, destroy
from direct.actor.Actor import Actor

class GolemBoss(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # --- CARGA DEL MODELO ANIMADO DEL CREATURE PACK ---
        # Usamos Actor de Panda3D mapeando múltiples animaciones
        ruta_base = "assets/modelos/villians/golem/Creature Pack/"
        ruta_animaciones = "assets/modelos/villians/golem/5000_Faces/"
        
        self.modelo_visual = Entity(parent=self)
        
        try:
            self.actor = Actor(
                ruta_base + "cuerpo_base.egg",
                {
                    'idle': ruta_animaciones + 'Walk Backward.egg',
                    'walk': ruta_animaciones + 'Walk Backward.egg',
                    'run': ruta_animaciones + 'Walk Backward.egg',
                    'punch': ruta_animaciones + 'Walk Backward.egg',
                    'die': ruta_animaciones + 'Walk Backward.egg'
                }
            )
            self.actor.reparentTo(self.modelo_visual)
            
            # El modelo .egg de Mixamo está desplazado 100 unidades hacia adelante.
            # Lo centramos manualmente a (0,0,0) antes de escalarlo.
            self.actor.setPos(2.09, -100.24, 9.64)
            
            self.actor.loop('idle')
            self.estado_actual = 'idle'
        except Exception as e:
            print(f"=================================")
            print(f"ERROR CARGANDO EL GLB: {e}")
            print(f"=================================")
            self.actor = None
            self.modelo_visual.model = 'cube'
            self.modelo_visual.color = color.red
            self.estado_actual = 'error'
        
        # Restablecemos la escala normal. Si el golem es invisible porque mide 2 cm,
        # esto lo hará visible. Si el EGG está en centímetros, esto lo hará de 2.2 metros (un poco más grande que el jugador).
        self.modelo_visual.scale = 2.2
        
        # dae2egg ya corrige el eje Z arriba, así que solo rotamos en Y para que nos vea de frente.
        self.modelo_visual.rotation_y = 180
        
        # Lo levantamos un poco para asegurarnos de que no esté bajo el piso
        self.modelo_visual.y = 1
            
        # Hitbox masivo para el jefe. Usamos BoxCollider manual porque Ursina no sabe medir Actors de Panda3D automáticamente (eso causó el crash de LMatrix4)
        from ursina import BoxCollider
        self.collider = BoxCollider(self, center=Vec3(0, 2, 0), size=Vec3(4, 10, 4))
        
        self.vida = 1000
        self.enabled = True
        self.velocidad = 5
        self.tiempo_vivo = 0
        
    def recibir_dano(self, cantidad):
        self.vida -= cantidad
        
        # Efecto visual de daño (se pinta rojo)
        if self.actor:
            self.actor.setColorScale(1, 0, 0, 1) 
            
            from ursina import invoke
            def restaurar_color():
                if self.actor:
                    self.actor.clearColorScale()
            invoke(restaurar_color, delay=0.1)
        
        if self.vida <= 0:
            destroy(self)
            
    def update(self):
        self.tiempo_vivo += time.dt
        
        import main
        if hasattr(main, 'jugador_principal'):
            jugador = main.jugador_principal
            direccion = jugador.position - self.position
            direccion.y = 0 
            
            # Usamos look_at 3D bloqueando el eje Y para que no se incline al piso
            objetivo = Vec3(jugador.x, self.y, jugador.z)
            
            if direccion.length() > 15:
                # Muy lejos: Correr
                if self.estado_actual != 'run' and self.actor:
                    self.actor.loop('run')
                    self.estado_actual = 'run'
                self.position += direccion.normalized() * (self.velocidad * 1.5) * time.dt
                self.look_at(objetivo)
                
            elif direccion.length() > 3:
                # Cerca: Caminar hacia el jugador
                if self.estado_actual != 'walk' and self.actor:
                    self.actor.loop('walk')
                    self.estado_actual = 'walk'
                self.position += direccion.normalized() * self.velocidad * time.dt
                self.look_at(objetivo)
                
            else:
                # Muy cerca: Atacar (Punch)
                if self.estado_actual != 'punch' and self.actor:
                    self.actor.loop('punch')
                    self.estado_actual = 'punch'
                self.look_at(objetivo)
