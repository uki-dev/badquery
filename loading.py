import bpy
import cadquery
import os

OUTPUT_PATH='cadquery.gltf'

def load(object: bpy.types.Object):

    # clean up existing objects
    delete_objects(object.cadquery.pointers)

    try:
        script = object.cadquery.script
        module = script.as_module()
        # TODO: realise a more flexible approach to exposing result to add-on
        assembly, objects = generate(OUTPUT_PATH, module.result)
        add_objects(object.cadquery.pointers, objects)
        attach_root(objects, object)
        link_materials(assembly, objects)
        
        # clean up filesystem
        os.remove(OUTPUT_PATH)
    except Exception as exception:
        import traceback
        traceback.print_exception(exception)

def add_objects(collection, objects):
    for object in objects:
        pointer = collection.add()
        pointer.object = object

def delete_objects(collection):
    for pointer in collection:
        try: 
            bpy.data.objects.remove(pointer.object)
        except:
            pass
    collection.clear()

# TODO: can we avoid exporting to disk at all, and instead pass a buffer between cadquery and blender?
def generate(path, object):
    assembly = cadquery.Assembly()
    assembly.add(object)
    assembly.save(path, exportType='GLTF')
    objects = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return assembly, set(bpy.context.scene.objects) - objects

def attach_root(objects, parent):
    for object in objects:
        if object.parent is None:
            object.parent = parent

def link_materials(assembly: cadquery.Assembly, objects):
    for child in assembly.objects.values():
        try:
            material = bpy.data.materials[child.metadata['material']]
            # TODO: use `objects`` not `bpy.data.objects`
            object = bpy.data.objects[child.name]
            apply_material(object, material)
        except:
            pass

def apply_material(object: bpy.types.Object, material: bpy.types.Material):
    def walk(object: bpy.types.Object):
        if object.type == 'MESH':
            object.data.materials.append(material)
        for child in object.children:
            walk(child)
    walk(object)
    