from ursina import *
from direct.actor.Actor import Actor

app = Ursina()
EditorCamera()

golem = Actor("assets/modelos/villians/golem/Creature Pack/cuerpo_base.egg")
golem.reparentTo(scene)

# Dibujar eje de coordenadas en (0,0,0)
Entity(model='cube', color=color.red, scale=0.5, position=(0,0,0))

# Ver donde está realmente el modelo
bounds = golem.getBounds()
center = bounds.getCenter()
print(f"Center is: {center}")
Entity(model='sphere', color=color.green, scale=1, position=(center.x, center.z, center.y)) # Ursina es Y-up, Panda3D Z-up

app.step()
print("Done checking.")
sys.exit()
