from direct.showbase.ShowBase import ShowBase
import sys

app = ShowBase()
model = app.loader.loadModel("assets/modelos/villians/golem/Creature Pack/mutant idle.glb")
print(f"Bounds idle: {model.getBounds()}")
sys.exit()
