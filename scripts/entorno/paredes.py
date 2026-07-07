from ursina import Entity
from scripts.entorno.puerta import Puerta

def generar_paredes(centro_x, centro_z, tamano, indice_arena, total_arenas):
    tamano_pared = 10 
    mitad = tamano // 2
    
    inicio_x = centro_x - mitad
    fin_x = centro_x + mitad
    inicio_z = centro_z - mitad
    fin_z = centro_z + mitad

    padre_paredes = Entity()
    puertas_frente = []
    puertas_atras = []
    
    # Escogemos el modelo de pared según el bioma
    modelo_pared = 'assets/texturas/medieval/wall-fortified.glb' if indice_arena == 1 else 'assets/texturas/structure-wall.glb'

    # Paredes Norte y Sur
    for x in range(inicio_x, fin_x, tamano_pared):
        pos_x = x + tamano_pared/2
        
        # Detectamos el centro para poner UNA SOLA puerta gigante
        if pos_x == -5:
            # --- PUERTA SUR (Atrás) ---
            if indice_arena > 0:
                p_sur = Puerta(position=(0, 0, inicio_z), rotation_y=0)
                puertas_atras.append(p_sur)
                # Llenamos el hueco SOBRE la puerta
                Entity(parent=padre_paredes, model=modelo_pared, position=(0, 16.5, inicio_z + 1), collider=None, scale=(25, 27, 2), double_sided=True)
            else:
                Entity(parent=padre_paredes, model=modelo_pared, position=(0, 0, inicio_z + 1), collider=None, scale=(25, 30, 2), double_sided=True)
            
            # --- PUERTA NORTE (Frente) ---
            if indice_arena < total_arenas - 1:
                p_norte = Puerta(position=(0, 0, fin_z), rotation_y=180)
                puertas_frente.append(p_norte)
                Entity(parent=padre_paredes, model=modelo_pared, position=(0, 16.5, fin_z - 1), collider=None, rotation_y=180, scale=(25, 27, 2), double_sided=True)
            else:
                Entity(parent=padre_paredes, model=modelo_pared, position=(0, 0, fin_z - 1), collider=None, rotation_y=180, scale=(25, 30, 2), double_sided=True)
                
        elif pos_x == 5:
            # Omitimos esta posición, ya que la puerta gigante abarca ambos lados.
            pass
        else:
            # Muros estáticos normales (SIEMPRE se construyen tanto Norte como Sur)
            # Para evitar que la textura se estire, apilamos 3 muros de altura 10 en vez de 1 muro de 30
            for y in range(0, 30, 10):
                # Muro Sur
                Entity(parent=padre_paredes, model=modelo_pared, 
                       position=(pos_x, y, inicio_z + 1), collider=None, scale=(10, 10, 2), double_sided=True)
                
                # Muro Norte
                Entity(parent=padre_paredes, model=modelo_pared, 
                       position=(pos_x, y, fin_z - 1), collider=None, rotation_y=180, scale=(10, 10, 2), double_sided=True)

    # Paredes Este y Oeste (Laterales completamente cerrados)
    for z in range(inicio_z, fin_z, tamano_pared):
        pos_z = z + tamano_pared/2
        
        # Apilamos los laterales también
        for y in range(0, 30, 10):
            Entity(parent=padre_paredes, model=modelo_pared, 
                   position=(inicio_x + 0.1, y, pos_z), collider=None, rotation_y=90, scale=(10, 10, 10), double_sided=True)
                   
            Entity(parent=padre_paredes, model=modelo_pared, 
                   position=(fin_x - 0.1, y, pos_z), collider=None, rotation_y=-90, scale=(10, 10, 10), double_sided=True)

    # MAGIA DE OPTIMIZACIÓN: Fusionamos los 480 bloques de ladrillo en 1 sola malla 3D.
    hijos = list(padre_paredes.children)
    padre_paredes.flatten_strong()
    
    # Removemos los 480 objetos de Python para que no consuman CPU
    from ursina import scene
    for hijo in hijos:
        if hijo in scene.entities:
            scene.entities.remove(hijo)

    # --- COLISIONADORES MASIVOS ---
    # En lugar de 480 colisionadores pequeños, creamos 6 cajas gigantes invisibles
    # Laterales (Este y Oeste)
    Entity(parent=padre_paredes, model='cube', position=(inicio_x, 15, centro_z), scale=(2, 30, tamano), collider='box', visible=False)
    Entity(parent=padre_paredes, model='cube', position=(fin_x, 15, centro_z), scale=(2, 30, tamano), collider='box', visible=False)
    
    # Frontales (Norte y Sur divididos en Izquierda y Derecha por la puerta)
    # Puerta abarca de -20 a 20. Así que el muro izquierdo va de -200 a -20 (centro = -110, ancho = 180)
    Entity(parent=padre_paredes, model='cube', position=(-110, 15, inicio_z), scale=(180, 30, 2), collider='box', visible=False)
    Entity(parent=padre_paredes, model='cube', position=(110, 15, inicio_z), scale=(180, 30, 2), collider='box', visible=False)
    
    Entity(parent=padre_paredes, model='cube', position=(-110, 15, fin_z), scale=(180, 30, 2), collider='box', visible=False)
    Entity(parent=padre_paredes, model='cube', position=(110, 15, fin_z), scale=(180, 30, 2), collider='box', visible=False)

    return puertas_frente, puertas_atras, padre_paredes