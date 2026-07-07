from scripts.entorno.piso import generar_piso
from scripts.entorno.paredes import generar_paredes
from scripts.entorno.decoracion import generar_decoracion
from scripts.entorno.techo import generar_techo

class CoordinadorEscenario:
    def __init__(self):
        self.num_arenas = 4
        self.tamano_arena = 400 
        self.offset_z = 800 
        self.puertas_frente_por_arena = {}
        self.puertas_atras_por_arena = {}
        self.chunks_arenas = []

    def construir_nivel_base(self):
        # Generar el masivo patio exterior una sola vez
        from scripts.entorno.patio import generar_patio_global
        generar_patio_global(self.num_arenas, self.offset_z, self.tamano_arena)
        print("Éxito: Patio exterior masivo generado.")

    def generar_arena_individual(self, i):
        from ursina import Entity
        centro_x = 0
        centro_z = i * self.offset_z
        
        chunk_arena = Entity()
        self.chunks_arenas.append(chunk_arena)
        
        padre_piso = generar_piso(centro_x, centro_z, self.tamano_arena, i)
        if padre_piso: padre_piso.parent = chunk_arena
        
        # Guardamos las puertas que genera esta arena
        puertas_frente, puertas_atras, padre_paredes = generar_paredes(centro_x, centro_z, self.tamano_arena, i, self.num_arenas)
        self.puertas_frente_por_arena[i] = puertas_frente
        self.puertas_atras_por_arena[i] = puertas_atras
        if padre_paredes: padre_paredes.parent = chunk_arena
        
        padre_decoracion = generar_decoracion(centro_x, centro_z, self.tamano_arena, i)
        if padre_decoracion: padre_decoracion.parent = chunk_arena
        
        padre_techo = generar_techo(centro_x, centro_z, self.tamano_arena, i)
        if padre_techo: padre_techo.parent = chunk_arena
        
        print(f"Arena {i} generada y empaquetada en Chunk.")