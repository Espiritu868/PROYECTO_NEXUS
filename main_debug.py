from ursina import Ursina, DirectionalLight, AmbientLight, color, window, application, scene, Entity, Text, camera, invoke, destroy
import random

# --- PARCHE PARA MODELOS GLB EXTERNOS ---
# Al convertir FBX a GLB en internet, a veces dejan rutas absolutas a imágenes que no existen.
# Este parche evita que Panda3D crashee y simplemente ignore esas texturas faltantes.
import gltf._converter
from panda3d.core import Texture
original_load_texture = gltf._converter.Converter.load_texture

def patched_load_texture(self, texid, gltf_tex, gltf_data):
    try:
        original_load_texture(self, texid, gltf_tex, gltf_data)
    except RuntimeError as e:
        print(f"Ignorando textura faltante: {e}")
        self.textures[texid] = Texture()

gltf._converter.Converter.load_texture = patched_load_texture
# ----------------------------------------

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

# --- PANTALLA DE CARGA (LOADING SCREEN) ---
carga_terminada = False
jugador_principal = None
coordinador = None
gestores_arena = []

from ursina import load_texture
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib

imagen_path = f'scripts/backgrounds/back{random.randint(1, 5)}.png'
textura = load_texture(imagen_path)

if textura:
    pantalla_carga = OnscreenImage(image=imagen_path, parent=application.base.aspect2d)
    pantalla_carga.setTransparency(TransparencyAttrib.MAlpha)
    
    img_ratio = textura.width / textura.height
    
    factor_x = window.aspect_ratio / img_ratio
    factor_z = 1.0 / 1.0
    factor = min(factor_x, factor_z)
    
    # Scale X = ancho, Scale Z = alto. En Panda3D la escala Z es la vertical.
    pantalla_carga.setScale(img_ratio * factor, 1, 1 * factor)
else:
    pantalla_carga = None

def self_destruct():
    if carga_terminada and pantalla_carga:
        pantalla_carga.destroy()
        
if pantalla_carga:
    # Usar el sistema de tareas de Panda3D para verificar la destrucción
    def check_destruct(task):
        if carga_terminada:
            pantalla_carga.destroy()
            return task.done
        return task.cont
    application.base.taskMgr.add(check_destruct, 'destruct_loading_screen')

def iniciar_carga_pesada():
    global carga_terminada, jugador_principal, coordinador, gestores_arena
    
    # Generar el escenario
    coordinador = CoordinadorEscenario()
    coordinador.construir_nivel_base()
    
    # Instanciar al jugador (Lo soltamos un poco arriba en Y=10 para que caiga y toque el suelo)
    from scripts.powerups import precargar_modelos_powerups
    precargar_modelos_powerups()
    jugador_principal = Jugador(position=(0, 10, 0))
    
    # --- GENERACIÓN DE VILLANOS Y SISTEMA DE ARENAS ---
    for indice in range(coordinador.num_arenas):
        coordinador.generar_arena_individual(indice)
        
        centro_arena_x = 0
        centro_arena_z = indice * coordinador.offset_z
        
        enemigos_arena = []
        
        if indice == 0:
            # --- SPAWN DEL JEFE (ARENA 0) ---
            from scripts.golem import GolemBoss
            from scripts.knight import KnightBoss
            from scripts.witch import BrujaBoss
            from scripts.dragon import DragonBoss
            
            # Instanciamos al KnightBoss
            jefe_caballero = KnightBoss(position=(centro_arena_x - 10, 0, centro_arena_z + 40))
            enemigos_arena.append(jefe_caballero)
            
            # Instanciamos a la Bruja de Hielo
            jefa_bruja = BrujaBoss(position=(centro_arena_x + 0, 0, centro_arena_z + 40))
            enemigos_arena.append(jefa_bruja)
            
            # Instanciamos al Jefe Final (Dragón) al fondo
            jefe_dragon = DragonBoss(position=(centro_arena_x, 0, centro_arena_z + 60))
            enemigos_arena.append(jefe_dragon)
            
            # Instanciamos al GolemBoss
            jefe_golem = GolemBoss(position=(centro_arena_x + 10, 0, centro_arena_z + 40))
            enemigos_arena.append(jefe_golem)
            
        else:
            # --- SPAWN NORMAL (OTRAS ARENAS) ---
            cantidad_enemigos = min(15 + (indice * 10), 150)
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

    carga_terminada = True

if __name__ == '__main__':
    # Forzamos a Ursina/Panda3D a dibujar la pantalla de carga primero
    application.base.graphicsEngine.renderFrame()
    application.base.graphicsEngine.renderFrame()
    
    # Ejecutamos la carga de modelos sincrónicamente para evitar warnings de 'recursive poll()'
    iniciar_carga_pesada()

# Engine Loop: Evaluamos la generación de arenas y la distancia de renderizado (Culling)
def update():
    if not carga_terminada:
        return
        
    z_jugador = jugador_principal.z
    
    # Render Distance (Estilo Minecraft) para los chunks masivos del patio
    if 'patio_chunks' in globals():
        for chunk in globals()['patio_chunks']:
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
                if not enemigo.enabled and not getattr(enemigo, 'listo_para_reciclar', False):
                    enemigo.enabled = True

# Tecla de escape de emergencia (Ya que el ratón estará bloqueado en la ventana)
def input(key):
    if key == 'escape':
        application.quit()

if __name__ == '__main__':

    def dump_entities():
        counts = {}
        for e in scene.entities:
            name = str(type(e))
            if hasattr(e, 'model') and e.model:
                name += " - " + str(e.model)
            if hasattr(e, 'name') and e.name:
                name += " [" + str(e.name) + "]"
            counts[name] = counts.get(name, 0) + 1
        
        print("\n--- ENTITY DUMP ---")
        for k, v in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"{v:4}x {k}")
        print("-------------------\n")
        application.quit()

    invoke(dump_entities, delay=1.0)

    app.run()