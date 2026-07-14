from direct.showbase.ShowBase import ShowBase
import sys

app = ShowBase()
model = app.loader.loadModel("assets/modelos/villians/golem/Creature Pack/cuerpo_base.egg")
print(f"Bounds egg: {model.getBounds()}")
sys.exit()
