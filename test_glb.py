from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
import sys

app = ShowBase()

ruta_base = "assets/modelos/villians/golem/Creature Pack/"
try:
    actor = Actor(
        ruta_base + "mutant idle.glb",
        {
            'idle': ruta_base + 'mutant idle.glb',
            'walk': ruta_base + 'mutant walking.glb',
            'run': ruta_base + 'mutant run.glb',
            'punch': ruta_base + 'mutant punch.glb',
            'die': ruta_base + 'mutant dying.glb'
        }
    )
    print("SUCCESS!")
    print(actor.getAnimNames())
except Exception as e:
    print("FAILED TO LOAD ACTOR:")
    print(repr(e))

sys.exit()
