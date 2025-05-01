
bl_info = {
    "name": "Import Disto CSV to Mesh (Leica Disto Points)",
    "author": "Vince Horlait",
    "version": (1, 6, 1),
    "blender": (3, 0, 0),
    "location": "File > Import > Import CSV (Disto to Mesh)",
    "description": "Import Leica Disto CSV file with 3D points as vertices, with optional labels and customizable columns",
    "category": "Import-Export",
}

# SPDX-License-Identifier: MIT

import bpy
import csv
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty

def create_text_label(text, location, size, vertical, align, offset_z, collection):
    font_curve = bpy.data.curves.new(type="FONT", name=f"Label_{text}")
    font_obj = bpy.data.objects.new(name=f"Label_{text}", object_data=font_curve)
    font_obj.data.body = text
    
    if align == 'CENTER':
        font_obj.data.align_x = 'CENTER'
    elif align == 'LEFT':
        font_obj.data.align_x = 'LEFT'
    elif align == 'RIGHT':
        font_obj.data.align_x = 'RIGHT'
    
    font_obj.rotation_euler[0] = 1.5708 if vertical else 0.0
    font_obj.location = (location[0], location[1], location[2] + offset_z)
    font_obj.scale = (size, size, size)
    
    collection.objects.link(font_obj)

class ImportCSVAsMesh(Operator, ImportHelper):
    bl_idname = "import_mesh.csv_as_mesh"
    bl_label = "Import CSV (Disto to Mesh)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".csv"
    filter_glob: StringProperty(default="*.csv", options={'HIDDEN'})

    show_labels: BoolProperty(name="Show Labels", description="Add label for each point", default=False)
    label_size: FloatProperty(name="Label Size", description="Size of labels", default=0.1)
    label_orientation: EnumProperty(
        name="Label Orientation",
        description="Orientation of the label",
        items=[('HORIZONTAL', "Horizontal", ""), ('VERTICAL', "Vertical", "")],
        default='VERTICAL'
    )
    label_alignment: EnumProperty(
        name="Label Alignment",
        description="Text alignment",
        items=[('CENTER', "Center", ""), ('LEFT', "Left", ""), ('RIGHT', "Right", "")],
        default='CENTER'
    )
    label_offset_z: FloatProperty(name="Vertical Offset", description="Offset above point", default=0.05)

    x_column_name: StringProperty(name="X Column Name", default="X [m]")
    y_column_name: StringProperty(name="Y Column Name", default="Y [m]")
    z_column_name: StringProperty(name="Z Column Name", default="Z [m]")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "show_labels")
        layout.prop(self, "label_size")
        layout.prop(self, "label_orientation")
        layout.prop(self, "label_alignment")
        layout.prop(self, "label_offset_z")
        layout.prop(self, "x_column_name")
        layout.prop(self, "y_column_name")
        layout.prop(self, "z_column_name")
        layout.separator()
        layout.operator("wm.url_open", text="📄 View Documentation (GitHub)").url = "https://github.com/madebyvince/import_csv_disto_mesh"

    def execute(self, context):
        verts = []
        skipped_lines = []
        try:
            with open(self.filepath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for line_num, row in enumerate(reader, start=2):
                    try:
                        x_val = row.get(self.x_column_name)
                        y_val = row.get(self.y_column_name)
                        z_val = row.get(self.z_column_name)
                        if x_val is None or y_val is None or z_val is None or x_val.strip() == "" or y_val.strip() == "" or z_val.strip() == "":
                            print(f"Skipped line {line_num}: Missing coordinate - {row}")
                            skipped_lines.append(line_num)
                            continue
                        x = float(x_val.strip())
                        y = float(y_val.strip())
                        z = float(z_val.strip())
                        verts.append((x, y, z))
                    except (ValueError, KeyError, TypeError) as e:
                        print(f"Skipped line {line_num}: Error {e} - {row}")
                        skipped_lines.append(line_num)
                        continue
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read CSV: {e}")
            return {'CANCELLED'}

        if not verts:
            self.report({'ERROR'}, "No valid points found in CSV.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new(name="CSV_Mesh")
        mesh.from_pydata(verts, [], [])
        mesh.update()

        obj = bpy.data.objects.new("CSV_Mesh", mesh)
        context.collection.objects.link(obj)

        if self.show_labels:
            vertical = self.label_orientation == 'VERTICAL'
            align = self.label_alignment
            offset_z = self.label_offset_z
            for idx, v in enumerate(verts):
                create_text_label(str(idx + 1), v, self.label_size, vertical, align, offset_z, context.collection)

        skipped_info = f" Skipped lines: {skipped_lines}" if skipped_lines else ""
        total_lines = len(verts) + len(skipped_lines)
        self.report({'INFO'}, f"Imported {len(verts)} points from {total_lines} lines.{skipped_info}")
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportCSVAsMesh.bl_idname, text="Import CSV (Disto to Mesh)")

def register():
    bpy.utils.register_class(ImportCSVAsMesh)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportCSVAsMesh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
