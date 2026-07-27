from ursina import Entity, scene, color, load_texture
from scripts.entorno.puerta import Puerta
import random

def generar_paredes(centro_x, centro_z, tamano, indice_arena, total_arenas):
    mitad = tamano // 2
    
    inicio_x = centro_x - mitad
    fin_x = centro_x + mitad
    inicio_z = centro_z - mitad
    fin_z = centro_z + mitad

    padre_paredes = Entity()
    puertas_frente = []
    puertas_atras = []
    
    # --- TEXTURAS GENERADAS CON IA ---
    textura_concreto = load_texture('assets/texturas/pared_concreto.png')
    if textura_concreto: textura_concreto.filtering = 'mipmap'
        
    textura_danada = load_texture('assets/texturas/pared_danada.png')
    if textura_danada: textura_danada.filtering = 'mipmap'

    # --- PAREDES LATERALES (Este y Oeste) ---
    Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(tamano/30, 1), position=(inicio_x, 15, centro_z), scale=(2, 30, tamano), collider='box')
    Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(tamano/30, 1), position=(fin_x, 15, centro_z), scale=(2, 30, tamano), collider='box')
    
    # --- PAREDES FRONTALES (Norte y Sur) ---
    ancho_muro = (mitad - 20)
    centro_muro_izq = inicio_x + (ancho_muro / 2)
    centro_muro_der = fin_x - (ancho_muro / 2)
    
    # --- PUERTAS Y MUROS SUR (Atrás) ---
    if indice_arena > 0:
        p_sur = Puerta(position=(0, 0, inicio_z), rotation_y=0)
        puertas_atras.append(p_sur)
        Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(40/15, 1), position=(0, 22.5, inicio_z), scale=(40, 15, 2), collider='box')
    else:
        Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(40/30, 1), position=(0, 15, inicio_z), scale=(40, 30, 2), collider='box')
        
    Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(ancho_muro/30, 1), position=(centro_muro_izq, 15, inicio_z), scale=(ancho_muro, 30, 2), collider='box')
    Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(ancho_muro/30, 1), position=(centro_muro_der, 15, inicio_z), scale=(ancho_muro, 30, 2), collider='box')
    
    # --- PUERTAS Y MUROS NORTE (Frente) ---
    if indice_arena < total_arenas - 1:
        p_norte = Puerta(position=(0, 0, fin_z), rotation_y=180)
        puertas_frente.append(p_norte)
        Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(40/15, 1), position=(0, 22.5, fin_z), scale=(40, 15, 2), collider='box')
    else:
        Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(40/30, 1), position=(0, 15, fin_z), scale=(40, 30, 2), collider='box')

    Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(ancho_muro/30, 1), position=(centro_muro_izq, 15, fin_z), scale=(ancho_muro, 30, 2), collider='box')
    Entity(parent=padre_paredes, model='cube', texture=textura_concreto, color=color.white, texture_scale=(ancho_muro/30, 1), position=(centro_muro_der, 15, fin_z), scale=(ancho_muro, 30, 2), collider='box')

    textura_grieta_transparente = load_texture('assets/texturas/grieta_transparente.png')
    if textura_grieta_transparente: textura_grieta_transparente.filtering = 'mipmap'

    # --- SISTEMA DE DECALS (Grieta Transparente) ---
    # Usamos una sola imagen PNG con transparencia real (canal alfa) para evitar generar miles de entidades.
    # ¡1 sola entidad por daño en lugar de docenas!
    num_danos = max(1, int(tamano / 40)) # Un daño cada ~40 unidades en promedio
    
    def colocar_decals(pos_constante, eje_constante, rot_y):
        for _ in range(num_danos):
            pos_var = random.uniform(-mitad + 20, mitad - 20)
            y_pos = random.uniform(8, 22)
            escala = random.uniform(15, 25)
            
            if eje_constante == 'z' and -25 < pos_var < 25:
                continue
                
            x_val = pos_var if eje_constante == 'z' else pos_constante
            z_val = pos_constante if eje_constante == 'z' else pos_var
                
            Entity(
                parent=padre_paredes,
                model='cube',
                texture=textura_grieta_transparente,
                color=color.white,
                transparent=True, # IMPORTANTE: Habilita el canal alfa para ocultar el fondo
                position=(x_val + centro_x, y_pos, z_val + centro_z),
                rotation=(0, rot_y, 0),
                scale=(escala, escala, 0.2), # Delgado como una calcomanía
                collider=None
            )

    # Oeste
    colocar_decals(-mitad + 1.1, 'x', -90)
    # Este
    colocar_decals(mitad - 1.1, 'x', 90)
    # Sur
    colocar_decals(-mitad + 1.1, 'z', 180)
    # Norte
    colocar_decals(mitad - 1.1, 'z', 0)

    return puertas_frente, puertas_atras, padre_paredes