from ursina import Ursina, DirectionalLight, AmbientLight, color, window, application, scene
import random

from scripts.escenario import CoordinadorEscenario
from scripts.jugador import Jugador
from scripts.villano_l import VillanoL
from scripts.villano_o import VillanoO
from scripts.zombie import Zombie
from scripts.gestor_arena import GestorArena

app = Ursina(title="Proyecto Nexo - Nivel 0")
window.fullscreen = True
window.vsync = False # Desbloquea los FPS por encima de 60

# --- ATMÓSFERA DE TERROR TÁCTICO (DARKNESS) ---
from ursina import application, AmbientLight, DirectionalLight, color, scene
# Iluminación MUY tenue. El jugador dependerá de su linterna.
AmbientLight(color=color.rgba(20, 20, 25, 255)) 
DirectionalLight(y=2, z=3, shadows=False, color=color.rgba(10, 15, 30, 255))

application.base.camLens.setFar(300) # Límite físico lejos
# En lugar de gris feo, usamos un "Negro Abismo" / Azul Medianoche muy oscuro
color_bruma = color.rgba(0.01, 0.01, 0.02, 1.0) 
application.base.setBackgroundColor(color_bruma) # El fondo es oscuridad pura
window.color = color_bruma 

# Sistema de Oscuridad de Ursina (Usando la niebla pero negra)
# Inicia a 15m y se vuelve 100% oscuridad impenetrable a los 100m
scene.fog_density = (15, 100)
scene.fog_color = color_bruma

# Generar el escenario
coordinador = CoordinadorEscenario()
coordinador.construir_nivel_base()

# Instanciar al jugador (Lo soltamos un poco arriba en Y=10 para que caiga y toque el suelo)
jugador_principal = Jugador(position=(0, 10, 0))

# --- GENERACIÓN DE VILLANOS Y SISTEMA DE ARENAS ---
gestores_arena = []

for indice in range(coordinador.num_arenas):
    coordinador.generar_arena_individual(indice)
    
    centro_arena_x = 0
    centro_arena_z = indice * coordinador.offset_z
    
    # Las arenas se vuelven progresivamente más difíciles (4, 7, 10, 13 enemigos)
    cantidad_enemigos = 4 + (indice * 3)
    enemigos_arena = []
    
    for _ in range(cantidad_enemigos):
        offset_x = random.choice([random.randint(-150, -50), random.randint(50, 150)])
        offset_z = random.randint(-150, 150)
        
        posicion_aleatoria = (centro_arena_x + offset_x, 0, centro_arena_z + offset_z)
        rotacion_aleatoria = random.randint(0, 360) 
        
        tipo_enemigo = random.choice(['l', 'o', 'zombie'])
        if tipo_enemigo == 'zombie':
            textura_z = random.choice(['assets/modelos/textures/texture-l.png', 'assets/modelos/textures/texture-o.png'])
            enemigo = Zombie(textura_zombie=textura_z, position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
        elif tipo_enemigo == 'l':
            enemigo = VillanoL(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
        else:
            enemigo = VillanoO(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
            
        enemigos_arena.append(enemigo)
        
    puertas_f = coordinador.puertas_frente_por_arena[indice]
    puertas_a = coordinador.puertas_atras_por_arena[indice]
    
    gestor = GestorArena(
        enemigos=enemigos_arena, 
        puertas_frente=puertas_f,
        puertas_atras=puertas_a,
        limite_z=centro_arena_z - 200, # Entrada a la arena
        indice_arena=indice
    )
    gestores_arena.append(gestor)

# Engine Loop: Evaluamos la generación de arenas y la distancia de renderizado (Culling)
def update():
    z_jugador = jugador_principal.z
    
    # Render Distance (Estilo Minecraft) para los chunks masivos del patio
    import main
    if hasattr(main, 'patio_chunks'):
        for chunk in main.patio_chunks:
            # Rango visual configurado a 1000 metros
            if abs(chunk.z - z_jugador) > 1000:
                chunk.visible = False
            else:
                chunk.visible = True
                
    # --- CULLING DE CHUNKS DE ARENAS (GPU OPTIMIZATION) ---
    # Solo renderizamos la arena actual, la anterior y la siguiente.
    # El resto desaparece completamente del GPU (culling de millones de vértices).
    indice_jugador = int(round(z_jugador / coordinador.offset_z))
    for i, chunk in enumerate(coordinador.chunks_arenas):
        if abs(i - indice_jugador) <= 1:
            if not chunk.enabled: chunk.enabled = True
        else:
            if chunk.enabled: chunk.enabled = False
                
    # --- CPU OPTIMIZACIÓN EXTREMA ---
    # Apagamos por completo la IA, físicas y animaciones de los enemigos lejanos.
    # El GPU ya optimizaba la geometría, pero esto optimizará la RAM y Procesador.
    for i, gestor in enumerate(gestores_arena):
        centro_arena_z = i * coordinador.offset_z
        distancia = abs(centro_arena_z - z_jugador)
        
        # Si la arena está a más de 600 metros, los enemigos entran en hiper-sueño (0 uso de CPU)
        if distancia > 600:
            for enemigo in gestor.enemigos:
                if enemigo.enabled: enemigo.enabled = False
        else:
            for enemigo in gestor.enemigos:
                if not enemigo.enabled: enemigo.enabled = True
                
    # Streaming de seguridad eliminado, ya están generadas.


# Tecla de escape de emergencia (Ya que el ratón estará bloqueado en la ventana)
def input(key):
    if key == 'escape':
        application.quit()

app.run()