import os
import sys

# Parche temporal para inspeccionar entidades después de cargar la base
with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Insertamos nuestro código justo antes de app.run()
custom_code = """
    def dump_entities():
        counts = {}
        for e in scene.entities:
            name = str(type(e))
            if hasattr(e, 'model') and e.model:
                name += " - " + str(e.model)
            if hasattr(e, 'name') and e.name:
                name += " [" + str(e.name) + "]"
            counts[name] = counts.get(name, 0) + 1
        
        print("\\n--- ENTITY DUMP ---")
        for k, v in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"{v:4}x {k}")
        print("-------------------\\n")
        application.quit()

    invoke(dump_entities, delay=1.0)
"""
code = code.replace("    app.run()", custom_code + "\n    app.run()")

with open('main_debug.py', 'w', encoding='utf-8') as f:
    f.write(code)
