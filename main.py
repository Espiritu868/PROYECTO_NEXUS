from ursina import Ursina, DirectionalLight, AmbientLight, color, window
from scripts.escenario import CoordinadorEscenario
from scripts.jugador import Jugador # ¡Importamos el nuevo TPS!

app = Ursina(title="Proyecto Nexo - Nivel 0")

DirectionalLight(y=2, z=3, shadows=True)
AmbientLight(color=color.rgba(120, 120, 120, 0.1))

# Generar el escenario
coordinador = CoordinadorEscenario()
coordinador.construir_nivel_0()

# Instanciar al jugador (Lo soltamos un poco arriba en Y=10 para que caiga y toque el suelo)
jugador_principal = Jugador(position=(0, 10, 0))

# Tecla de escape de emergencia (Ya que el ratón estará bloqueado en la ventana)
def input(key):
    if key == 'escape':
        application.quit()

app.run()