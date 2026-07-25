from ursina import *
from direct.actor.Actor import Actor

app = Ursina()
EditorCamera()

ruta_base = "assets/modelos/villians/golem/Creature Pack/"
ruta_anim = "assets/modelos/villians/golem/5000_Faces/"

actor = Actor(
    ruta_base + "cuerpo_base.egg",
    {'idle': ruta_anim + 'Walk Backward.fbx'}
)
actor.reparentTo(scene)
actor.loop('idle')

def check_bounds():
    print(f"Bounds after anim: {actor.getBounds()}")
    center = actor.getBounds().getCenter()
    print(f"Center after anim: {center}")
    sys.exit()

invoke(check_bounds, delay=1)
app.run()
