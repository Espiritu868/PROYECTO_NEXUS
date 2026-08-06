def fijar_texturas_pbr(entity):
    """
    Filtra las texturas PBR (Normal, Metal, Roughness) de los nodos geom de Panda3D
    para evitar que Ursina Engine las renderice como colores base.
    """
    try:
        from panda3d.core import TextureAttrib, TextureStage
        for np in entity.findAllMatches('**/+GeomNode'):
            geom_node = np.node()
            for i in range(geom_node.getNumGeoms()):
                geom_state = geom_node.getGeomState(i)
                if geom_state.hasAttrib(TextureAttrib.getClassType()):
                    tex_attrib = geom_state.getAttrib(TextureAttrib.getClassType())
                    new_attrib = TextureAttrib.make()
                    
                    for ts_i in range(tex_attrib.getNumOnStages()):
                        ts = tex_attrib.getOnStage(ts_i)
                        tex = tex_attrib.getOnTexture(ts)
                        ts_name = ts.getName().lower()
                        
                        # Conservar solo la textura base (Albedo/Diffuse)
                        if 'normal' not in ts_name and 'metal' not in ts_name and 'rough' not in ts_name:
                            new_attrib = new_attrib.addOnStage(ts, tex)
                            
                    new_state = geom_state.setAttrib(new_attrib)
                    geom_node.setGeomState(i, new_state)
    except Exception as e:
        print("Error fijando texturas PBR:", e)
