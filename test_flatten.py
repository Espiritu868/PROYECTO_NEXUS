from ursina import *
app = Ursina()

padre = Entity()
# Cargar un GLB (que tiene hijos)
for i in range(10):
    Entity(parent=padre, model='cube', position=(i,0,0)) # Usar cube simulando

print("Entities before:", len(scene.entities))
hijos = list(padre.children)
padre.flatten_strong()

def remove_recursively(ent):
    if ent in scene.entities:
        scene.entities.remove(ent)
    for c in list(ent.children):
        remove_recursively(c)

for hijo in hijos:
    remove_recursively(hijo)
    destroy(hijo)

def check_entities():
    print("Entities after:", len(scene.entities))
    application.quit()

invoke(check_entities, delay=0.2)
app.run()
