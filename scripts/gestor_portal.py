from ursina import Entity, held_keys, invoke, scene
from scripts.hud_mision import HUDMisionPanel


class GestorPortal(Entity):
    def __init__(self, offset_z=600, tipo_mision="RECOLECTAR", indice_arena=0, **kwargs):
        super().__init__(**kwargs)
        self.piezas_recolectadas = 0
        self.total_piezas = 5

        self.grietas_selladas = 0
        self.total_grietas = 3

        self.arma_lista = False
        self.offset_z = offset_z
        self.tipo_mision = tipo_mision
        self.indice_arena = indice_arena

        self.hud = HUDMisionPanel()
        self.hud.enabled = False

        if self.tipo_mision == "RECOLECTAR":
            self.mision_texto = "Recolecta las piezas del Portal"
            self.hud.actualizar_mision(self.mision_texto, self.piezas_recolectadas, self.total_piezas)

        elif self.tipo_mision == "SELLAR_GRIETAS":
            self.mision_texto = "Localiza y sella las 3 grietas dimensionales"
            self.hud.actualizar_mision(self.mision_texto, self.grietas_selladas, self.total_grietas)

        else:  # ELIMINAR_JEFE
            self.mision_texto = "Elimina al Jefe de la Arena"
            self.hud.actualizar_mision(self.mision_texto)

    def update(self):
        from scripts.jugador import Jugador

        jugador = next((e for e in scene.entities if isinstance(e, Jugador)), None)
        if jugador:
            centro_arena_z = self.indice_arena * self.offset_z
            distancia_z = abs(jugador.z - centro_arena_z)
            self.hud.enabled = distancia_z < (self.offset_z / 2)

        if self.arma_lista and held_keys['f'] and self.hud.enabled:
            self.teletransportar_jugador()

    # ============ MISIÓN: RECOLECTAR PIEZAS ============
    def recolectar_pieza(self, nombre):
        self.piezas_recolectadas += 1
        if self.piezas_recolectadas < self.total_piezas:
            self.hud.actualizar_mision(self.mision_texto, self.piezas_recolectadas, self.total_piezas)
        else:
            self.arma_lista = True
            self.hud.mision_completada(" PISTOLA LISTA! Presiona [F]")

    # ============ MISIÓN: ELIMINAR JEFE ============
    def completar_mision_jefe(self):
        self.arma_lista = True
        self.hud.mision_completada("JEFE CAÍDO! Presiona [F]")

    # ============ MISIÓN: SELLAR GRIETAS (NUEVA) ============
    def sellar_grieta(self):
        self.grietas_selladas += 1
        if self.grietas_selladas < self.total_grietas:
            self.hud.actualizar_mision(self.mision_texto, self.grietas_selladas, self.total_grietas)
        else:
            self.arma_lista = True
            self.hud.mision_completada("SECTOR ESTABILIZADO! Presiona [F]")

    def teletransportar_jugador(self):
        from scripts.jugador import Jugador
        jugador = next((e for e in scene.entities if isinstance(e, Jugador)), None)
        if jugador:
            jugador.z += self.offset_z
            self.hud.actualizar_mision("TELETRANSPORTANDO...")
            self.arma_lista = False
            invoke(self.hud.destruir, delay=3)
