from ursina import Ursina, DirectionalLight, AmbientLight, color, window, application
import random

from scripts.escenario import CoordinadorEscenario
from scripts.jugador import Jugador
from scripts.villano_l import VillanoL
from scripts.villano_o import VillanoO

app = Ursina(title="Proyecto Nexo - Nivel 0")

DirectionalLight(y=2, z=3, shadows=True)
AmbientLight(color=color.rgba(120, 120, 120, 0.1))

# Generar el escenario
coordinador = CoordinadorEscenario()
coordinador.construir_nivel_0()

# Instanciar al jugador (Lo soltamos un poco arriba en Y=10 para que caiga y toque el suelo)
jugador_principal = Jugador(position=(0, 10, 0))

# --- GENERACIÓN DE VILLANOS EN LAS 4 ARENAS ---
# Asumiendo que tu CoordinadorEscenario construyó las salas separadas por 150 unidades en X
for i in range(4):
    centro_arena_x = i * 150
    centro_arena_z = 0
    
    # Decidimos de forma aleatoria si se crean 4 o 5 villanos para esta habitación
    cantidad_enemigos = random.randint(4, 5)
    
    for _ in range(cantidad_enemigos):
        # Calculamos una posición y rotación aleatoria dentro del rango de la habitación
        offset_x = random.randint(-25, 25)
        offset_z = random.randint(-25, 25)
        
        posicion_aleatoria = (centro_arena_x + offset_x, 0, centro_arena_z + offset_z)
        rotacion_aleatoria = random.randint(0, 360) 
        
        # Elegimos al azar instanciar la clase VillanoL o VillanoO
        if random.choice(['l', 'o']) == 'l':
            VillanoL(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
        else:
            VillanoO(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)

# Tecla de escape de emergencia (Ya que el ratón estará bloqueado en la ventana)
def input(key):
    if key == 'escape':
        application.quit()

app.run()