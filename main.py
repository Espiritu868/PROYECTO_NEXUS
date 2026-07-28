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
from scripts.editor_nivel import EditorNivel
from scripts.menu_pausa import MenuPausa

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

# --- MENÚ DE PAUSA ---
menu_pausa = MenuPausa()

# Sistema de Oscuridad de Ursina (Usando la niebla pero negra)
# Inicia a 15m y se vuelve 100% oscuridad impenetrable a los 100m
scene.fog_density = (15, 100)
scene.fog_color = color_bruma

# --- PANTALLA DE CARGA (LOADING SCREEN) ---
carga_terminada = False
jugador_principal = None
coordinador = None
gestores_arena = []

from ursina import load_texture, Entity, Text, color
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
import random

from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
import time

lista_imagenes = [
    f'scripts/backgrounds/back{i}.png' for i in range(1, 6)
]
imagen_actual = random.choice(lista_imagenes)

# Usamos OnscreenImage nativo de Panda3D para el fondo, anclado a render2d (-1 a 1)
# para que cubra la pantalla perfecta y exactamente, sin ningún zoom.
pantalla_carga = OnscreenImage(image=imagen_actual, parent=application.base.render2d)
pantalla_carga.setTransparency(TransparencyAttrib.MAlpha)

# Las coordenadas de render2d van de -1 a 1. Escala (1,1,1) cubre toda la pantalla.
pantalla_carga.setScale(1, 1, 1)

# Para que renderice detrás de la UI de Ursina (como la barra de carga)
pantalla_carga.setBin("background", 10)

# Mantenemos solo el fondo de pantalla (sin barra de progreso extra)

def actualizar_loading(porcentaje, mensaje="Cargando..."):
    # Cambiar imagen aleatoria para el slideshow
    nueva_img = random.choice(lista_imagenes)
    pantalla_carga.setImage(nueva_img)
    pantalla_carga.setTransparency(TransparencyAttrib.MAlpha)
    
    # Forzar al motor a dibujar este frame inmediatamente en la pantalla
    application.base.graphicsEngine.renderFrame()
    application.base.graphicsEngine.renderFrame()
    time.sleep(0.8) # Pausa artificial para que se alcance a ver la imagen y el progreso

def self_destruct():
    if carga_terminada:
        from ursina import destroy
        if pantalla_carga:
            pantalla_carga.destroy()
        
        # Activar la interfaz del jugador ahora que terminó la carga
        if jugador_principal:
            jugador_principal.mira.enabled = True
            jugador_principal.barra_vida_bg.enabled = True
            jugador_principal.texto_vida.enabled = True
            jugador_principal.radar_bg.enabled = True

# Usar el sistema de tareas de Panda3D para verificar la destrucción
def check_destruct(task):
    if carga_terminada:
        self_destruct()
        return task.done
    return task.cont
application.base.taskMgr.add(check_destruct, 'destruct_loading_screen')

def iniciar_carga_pesada():
    global carga_terminada, jugador_principal, coordinador, gestores_arena
    
    actualizar_loading(0.1, "Generando masivo patio exterior...")
    coordinador = CoordinadorEscenario()
    coordinador.construir_nivel_base()
         
    actualizar_loading(0.3, "Invocando al Jugador Principal...")
    jugador_principal = Jugador(position=(0, 10, 0))
    menu_pausa.jugador = jugador_principal
    
    # Inicializar el Editor de Niveles (F4 para abrir)
    editor = EditorNivel(jugador_principal)
    
    # Ocultar la interfaz del jugador temporalmente para que no estorbe en la pantalla de carga
    jugador_principal.mira.enabled = False
    jugador_principal.barra_vida_bg.enabled = False
    jugador_principal.texto_vida.enabled = False
    jugador_principal.radar_bg.enabled = False
    
    # --- GENERACIÓN DE VILLANOS Y SISTEMA DE ARENAS ---
    for indice in range(coordinador.num_arenas):
        progreso = 0.3 + (0.7 * (indice / coordinador.num_arenas))
        actualizar_loading(progreso, f"Construyendo y fortificando Arena {indice}...")
        
        coordinador.generar_arena_individual(indice)
        
        centro_arena_x = 0
        centro_arena_z = indice * coordinador.offset_z
        jefe_asignado = None
        
        if indice == 2:
            from scripts.golem import GolemBoss
            jefe_asignado = GolemBoss
        
        # Incrementar drásticamente la cantidad de enemigos
        cantidad_enemigos = 15 + (indice * 10)
            
        puertas_f = coordinador.puertas_frente_por_arena[indice]
        puertas_a = coordinador.puertas_atras_por_arena[indice]
        
        # ============================================================== #  
        # SISTEMA DE MISIONES AGREGADO                                   #
        from scripts.pieza import PiezaPortal
        from scripts.gestor_portal import GestorPortal 
        from scripts.grieta import Grieta

        # El juego elige la misión al azar para esta arena
        misiones_disponibles = ["RECOLECTAR", "SELLAR_GRIETAS"]
        tipo_mision_elegida = random.choice(misiones_disponibles)

        gestor_portal_arena = GestorPortal(
            offset_z=coordinador.offset_z, 
            tipo_mision=tipo_mision_elegida,
            indice_arena=indice
        )

        #  SOLO generamos las piezas si la misión elegida es "RECOLECTAR"
        if tipo_mision_elegida == "RECOLECTAR":
            piezas_info = [
                {"nombre": "Carcasa del Arma",  "modelo": "assets/modelos/carcasa_reducida.glb"},
                {"nombre": "Pinzas Frontales",  "modelo": "assets/modelos/pinzas.glb"},
                {"nombre": "Emisor portal",     "modelo": "assets/modelos/emisor_portal.glb"},  
                {"nombre": "Base trasera",      "modelo": "assets/modelos/base_trasera.glb"}, 
                {"nombre": "Carcasa lateral",   "modelo": "assets/modelos/Carcasa_lateral.glb"} 
            ]

            sectores = [
                (random.randint(-140, -50), random.randint(-120, -20)), 
                (random.randint(50, 140), random.randint(-120, 20)),
                (random.randint(-70, 70), random.randint(60, 150)),  
                (random.randint(50, 140), random.randint(60, 150)), 
                (random.randint(50, 140), random.randint(-50, 20)), 
            ]
            random.shuffle(sectores)

            for i, info in enumerate(piezas_info):
                offset_x, offset_z = sectores[i]
                pos_x = centro_arena_x + offset_x
                pos_z = centro_arena_z + offset_z
                
                PiezaPortal(
                    nombre_pieza=info["nombre"], 
                    modelo_path=info["modelo"],  
                    position=(pos_x, 1, pos_z), 
                    gestor=gestor_portal_arena
                ) 
                
        elif tipo_mision_elegida == "SELLAR_GRIETAS": 
            sectores_grietas = [ 
                (random.randint(-140, -50), random.randint(-120, -20)),
                (random.randint(50, 140), random.randint(-120, 20)),
                (random.randint(-70, 70), random.randint(60, 150)), 
            ] 
            random.shuffle(sectores_grietas) 
            
            for offset_x, offset_z in sectores_grietas:
                pos_x = centro_arena_x + offset_x
                pos_z = centro_arena_z + offset_z 
                
                g = Grieta(position=(pos_x, 1, pos_z), gestor=gestor_portal_arena)
                print(f" Grieta creada en: {g.position}")
        # ============================================================== #
        
        gestor = GestorArena(
            jefe_class=jefe_asignado,
            cantidad_enemigos=cantidad_enemigos,
            centro_x=centro_arena_x,
            centro_z=centro_arena_z,
            puertas_frente=puertas_f,
            puertas_atras=puertas_a,
            limite_z=centro_arena_z - 200, # Entrada a la arena
            indice_arena=indice
        )
        gestores_arena.append(gestor)

    actualizar_loading(1.0, "¡Listos para el combate!")
    
    # Pre-calentamiento del motor (Engine Warmup):
    # Obligamos a Panda3D a procesar los árboles de colisiones (KD-Trees), shaders y físicas de los miles de 
    # muros generados en este preciso momento, MIENTRAS la pantalla de carga aún está puesta para ocultar el lag.
    for _ in range(3):
        application.base.taskMgr.step()
        
    carga_terminada = True

if __name__ == '__main__':
    # Ejecutamos la carga de modelos sincrónicamente, pero usando nuestro renderFrame para el slideshow
    iniciar_carga_pesada()

# Engine Loop: Evaluamos la generación de arenas y la distancia de renderizado (Culling)
def update():
    if not carga_terminada or application.paused:
        return
        
    z_jugador = jugador_principal.z
    
    # Render Distance (Patio removal optimization)
    # The patio chunks have been deleted to focus only on Arena 0.
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

# Tecla de escape de emergencia (Ya que el ratón estará bloqueado en la ventana)
def input(key):
    pass

if __name__ == '__main__':
    app.run()