from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from scripts.escenario import construir_piso

app = Ursina(vsync=False, fullscreen=False, title="Proyecto Nexo - Alpha")
camera.fov = 90

# --- CONFIGURACIÓN DE ENTORNO ---
window.color = color.black
Sky(color=color.black)
scene.fog_density = 0.015
scene.fog_color = color.black

scene.ambient_light = color.rgb(150/255, 150/255, 150/255) * 0.5
dir_light = DirectionalLight(rotation=(45, 45, 0))
dir_light.color = color.rgb(100/255, 150/255, 255/255) * 0.4

# --- CONSTRUCCIÓN DEL EDIFICIO ---
print("Generando arquitectura interdimensional...")

for i in range(4):
    construir_piso(nivel=i, altura_techo=20)

# --- JUGADOR PERSONALIZADO ---
class JugadorNexo(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.velocidad_caminar = 12
        self.velocidad_correr = 22
        self.velocidad_agachado = 5
        self.speed = self.velocidad_caminar
        
        self.altura_normal = 2.0
        self.altura_agachada = 0.8
        self.jump_height = 2.5
        
    def update(self):
        if held_keys['shift']:
            self.speed = self.velocidad_correr
        elif held_keys['control'] or held_keys['c']:
            self.speed = self.velocidad_agachado
            self.camera_pivot.y = lerp(self.camera_pivot.y, self.altura_agachada, time.dt * 10)
        else:
            self.speed = self.velocidad_caminar
            self.camera_pivot.y = lerp(self.camera_pivot.y, self.altura_normal, time.dt * 10)
            
        super().update()

jugador = JugadorNexo(position=(20, 3, 20), origin_y=-0.5)
jugador.collider = 'capsule'

def update():
    if held_keys['q']:
        application.quit()

print("¡Edificio cargado! Explora los 4 pisos.")
app.run()