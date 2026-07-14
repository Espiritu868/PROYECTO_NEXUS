from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
import sys

app = ShowBase()
try:
    actor = Actor("assets/modelos/villians/golem/5000_Faces/Walk Backward.fbx")
    print("SUCCESS FBX LOAD")
except Exception as e:
    print("FAILED FBX LOAD:", repr(e))
sys.exit()
