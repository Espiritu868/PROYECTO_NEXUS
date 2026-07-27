from ursina import Entity, color
import random

def generar_decoracion(centro_x, centro_z, tamano, indice_arena=0):
    padre_decoracion = Entity()
    
    mitad = tamano // 2
    
    ruta = 'assets/modelos/objetos_con_meshy/'
    
    # 1. Una sola mesa de crafteo en una esquina
    mesa = Entity(parent=padre_decoracion, model=ruta+'mesa_trabajo.glb', 
           position=(centro_x - mitad + 30, 0.75, centro_z - mitad + 30),
           rotation=(0, 45, 0), scale=1.5, collider='box',
           color=color.yellow) 
           
    import __main__ as main
    main.mesa_trabajo = mesa
    
    # 2. Sistema de ductos de aire (ducto_amarillo.glb)
    # Creando vías de conducto en el techo
    altura_ducto = 45 # Altura para que quede suspendido
    espaciado_ducto = 30
    
    # Línea de ductos a lo largo del eje X
    for px in range(int(-mitad + 40), int(mitad - 40), espaciado_ducto):
        Entity(parent=padre_decoracion, model=ruta+'ducto_amarillo.glb',
               position=(centro_x + px, altura_ducto, centro_z + 60),
               rotation=(0, 90, 0), scale=4, collider='box')
        Entity(parent=padre_decoracion, model=ruta+'ducto_amarillo.glb',
               position=(centro_x + px, altura_ducto, centro_z - 60),
               rotation=(0, 90, 0), scale=4, collider='box')

    # Línea de ductos a lo largo del eje Z
    for pz in range(int(-mitad + 40), int(mitad - 40), espaciado_ducto):
        Entity(parent=padre_decoracion, model=ruta+'ducto_amarillo.glb',
               position=(centro_x + 60, altura_ducto, centro_z + pz),
               rotation=(0, 0, 0), scale=4, collider='box')
        Entity(parent=padre_decoracion, model=ruta+'ducto_amarillo.glb',
               position=(centro_x - 60, altura_ducto, centro_z + pz),
               rotation=(0, 0, 0), scale=4, collider='box')

    # 3. Unos cuantos servidores regados (servidor.glb)
    random.seed(indice_arena + 10)
    for _ in range(30):
        rx = random.uniform(-mitad + 40, mitad - 40)
        rz = random.uniform(-mitad + 40, mitad - 40)
        # Evitar tapar puertas (centro z)
        if abs(rx) < 50 and abs(rz) > mitad - 80:
            continue
        rot = random.choice([0, 90, 180, 270])
        Entity(parent=padre_decoracion, model=ruta+'servidor.glb',
               position=(centro_x + rx, 1.8, centro_z + rz),
               rotation=(0, rot, 0), scale=2.5, collider='box')
               
    # 4. Los demás objetos (barriles, cajas, máquinas transportadoras)
    # Cajas
    for _ in range(50):
        rx = random.uniform(-mitad + 30, mitad - 30)
        rz = random.uniform(-mitad + 30, mitad - 30)
        if abs(rx) < 50 and abs(rz) > mitad - 80:
            continue
        Entity(parent=padre_decoracion, model=ruta+'caja.glb',
               position=(centro_x + rx, 0.8, centro_z + rz),
               rotation=(0, random.uniform(0, 360), 0), scale=0.8, collider='box')

    # Barriles
    for _ in range(60):
        rx = random.uniform(-mitad + 30, mitad - 30)
        rz = random.uniform(-mitad + 30, mitad - 30)
        if abs(rx) < 50 and abs(rz) > mitad - 80:
            continue
        Entity(parent=padre_decoracion, model=ruta+'barril_toxico_red.glb',
               position=(centro_x + rx, 0.8, centro_z + rz),
               rotation=(0, random.uniform(0, 360), 0),
               scale=0.8, collider='box')
               
    # Máquinas transportadoras
    for _ in range(15):
        rx = random.uniform(-mitad + 50, mitad - 50)
        rz = random.uniform(-mitad + 50, mitad - 50)
        if abs(rx) < 50 and abs(rz) > mitad - 80:
            continue
        rot = random.choice([0, 90, 180, 270])
        Entity(parent=padre_decoracion, model=ruta+'maquina_transportadora.glb',
               position=(centro_x + rx, 2, centro_z + rz),
               rotation=(0, rot, 0), scale=4, collider='box')

    return padre_decoracion
