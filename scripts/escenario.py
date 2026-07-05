from scripts.entorno.piso import generar_piso
from scripts.entorno.paredes import generar_paredes

class CoordinadorEscenario:
    def __init__(self):
        self.num_arenas = 4
        self.tamano_arena = 400 
        self.offset_z = 400 

    def construir_nivel_0(self):
        for i in range(self.num_arenas):
            centro_x = 0
            centro_z = i * self.offset_z
            
            generar_piso(centro_x, centro_z, self.tamano_arena)
            
            # NUEVO: Pasamos el índice actual (i) y el total de arenas
            generar_paredes(centro_x, centro_z, self.tamano_arena, i, self.num_arenas)
            
        print(f"Éxito: Se han generado {self.num_arenas} arenas masivas.")