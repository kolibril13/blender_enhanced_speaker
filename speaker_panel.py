# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
from bpy.types import Panel, PropertyGroup, Operator
from bpy.props import PointerProperty, StringProperty


def get_speakers(self, context):
    """Return list of speakers in the scene for the enum property."""
    items = [("NONE", "Select Speaker...", "No speaker selected", "SPEAKER", 0)]
    for i, obj in enumerate(bpy.data.objects):
        if obj.type == 'SPEAKER':
            items.append((obj.name, obj.name, f"Speaker: {obj.name}", "SPEAKER", i + 1))
    return items


def update_selected_speaker(self, context):
    """Called when the speaker selection changes."""
    pass


class ENHANCED_SPEAKER_PG_settings(PropertyGroup):
    """Property group for enhanced speaker settings."""
    
    selected_speaker: StringProperty(
        name="Selected Speaker",
        description="The currently selected speaker object",
        default="",
    )


class ENHANCED_SPEAKER_OT_select_sound(Operator):
    """Open file browser to select a sound file for the speaker"""
    bl_idname = "enhanced_speaker.select_sound"
    bl_label = "Select Sound File"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        subtype='FILE_PATH',
        default="",
    )
    
    filter_glob: StringProperty(
        default="*.wav;*.mp3;*.ogg;*.flac;*.aiff;*.aif",
        options={'HIDDEN'},
    )
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.enhanced_speaker
        speaker_name = settings.selected_speaker
        return speaker_name and speaker_name in bpy.data.objects
    
    def execute(self, context):
        settings = context.scene.enhanced_speaker
        speaker_obj = bpy.data.objects.get(settings.selected_speaker)
        
        if not speaker_obj or speaker_obj.type != 'SPEAKER':
            self.report({'ERROR'}, "No valid speaker selected")
            return {'CANCELLED'}
        
        # Load or get the sound
        sound = bpy.data.sounds.load(self.filepath, check_existing=True)
        
        # Assign the sound to the speaker
        speaker_obj.data.sound = sound
        
        self.report({'INFO'}, f"Loaded sound: {sound.name}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ENHANCED_SPEAKER_OT_clear_sound(Operator):
    """Clear the sound from the selected speaker"""
    bl_idname = "enhanced_speaker.clear_sound"
    bl_label = "Clear Sound"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.enhanced_speaker
        speaker_name = settings.selected_speaker
        if speaker_name and speaker_name in bpy.data.objects:
            speaker_obj = bpy.data.objects[speaker_name]
            return speaker_obj.type == 'SPEAKER' and speaker_obj.data.sound is not None
        return False
    
    def execute(self, context):
        settings = context.scene.enhanced_speaker
        speaker_obj = bpy.data.objects.get(settings.selected_speaker)
        
        if speaker_obj and speaker_obj.type == 'SPEAKER':
            speaker_obj.data.sound = None
            self.report({'INFO'}, "Sound cleared")
        
        return {'FINISHED'}


class ENHANCED_SPEAKER_PT_main_panel(Panel):
    """Enhanced Speaker Panel in the N-panel"""
    bl_label = "Enhanced Speaker"
    bl_idname = "ENHANCED_SPEAKER_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Speaker"
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.enhanced_speaker
        
        # Speaker selection
        layout.label(text="Speaker Selection:")
        layout.prop_search(
            settings, "selected_speaker",
            bpy.data, "speakers",
            text="",
            icon='SPEAKER'
        )
        
        # Alternative: search in objects but filter to speakers
        # This allows selecting by object name
        box = layout.box()
        box.label(text="Or select from objects:")
        
        # Create a column for speaker buttons
        col = box.column(align=True)
        speakers_found = False
        for obj in bpy.data.objects:
            if obj.type == 'SPEAKER':
                speakers_found = True
                row = col.row(align=True)
                # Highlight if this is the selected speaker
                if obj.name == settings.selected_speaker:
                    row.alert = True
                op = row.operator(
                    "enhanced_speaker.set_speaker",
                    text=obj.name,
                    icon='SPEAKER'
                )
                op.speaker_name = obj.name
        
        if not speakers_found:
            col.label(text="No speakers in scene", icon='INFO')
        
        layout.separator()
        
        # Show sound info if speaker is selected
        speaker_name = settings.selected_speaker
        if speaker_name:
            # Try to find the speaker object
            speaker_obj = None
            
            # First check if it's an object name
            if speaker_name in bpy.data.objects:
                obj = bpy.data.objects[speaker_name]
                if obj.type == 'SPEAKER':
                    speaker_obj = obj
            
            # Also check if it matches a speaker data name
            if not speaker_obj and speaker_name in bpy.data.speakers:
                # Find an object using this speaker data
                for obj in bpy.data.objects:
                    if obj.type == 'SPEAKER' and obj.data.name == speaker_name:
                        speaker_obj = obj
                        break
            
            if speaker_obj:
                self.draw_speaker_info(layout, speaker_obj)
            else:
                layout.label(text="Speaker not found", icon='ERROR')
    
    def draw_speaker_info(self, layout, speaker_obj):
        """Draw information about the selected speaker."""
        box = layout.box()
        box.label(text=f"Speaker: {speaker_obj.name}", icon='SPEAKER')
        
        speaker_data = speaker_obj.data
        
        # Sound file section
        box.separator()
        box.label(text="Sound File:")
        
        if speaker_data.sound:
            sound = speaker_data.sound
            
            # Show sound name
            row = box.row()
            row.label(text=sound.name, icon='SOUND')
            
            # Show filepath (truncated if too long)
            filepath = sound.filepath
            if len(filepath) > 40:
                filepath = "..." + filepath[-37:]
            box.label(text=filepath)
            
            # Sound info
            if sound.packed_file:
                box.label(text="(Packed)", icon='PACKAGE')
            
            # Buttons row
            row = box.row(align=True)
            row.operator("enhanced_speaker.select_sound", text="Change", icon='FILEBROWSER')
            row.operator("enhanced_speaker.clear_sound", text="Clear", icon='X')
            
            # Quick access to sound properties
            box.separator()
            box.prop(speaker_data, "volume")
            box.prop(speaker_data, "pitch")
            
        else:
            box.label(text="No sound loaded", icon='INFO')
            box.operator("enhanced_speaker.select_sound", text="Load Sound", icon='FILEBROWSER')


class ENHANCED_SPEAKER_OT_set_speaker(Operator):
    """Set the selected speaker"""
    bl_idname = "enhanced_speaker.set_speaker"
    bl_label = "Select Speaker"
    bl_options = {'REGISTER', 'UNDO'}
    
    speaker_name: StringProperty()
    
    def execute(self, context):
        context.scene.enhanced_speaker.selected_speaker = self.speaker_name
        return {'FINISHED'}


def register():
    bpy.types.Scene.enhanced_speaker = PointerProperty(type=ENHANCED_SPEAKER_PG_settings)


def unregister():
    del bpy.types.Scene.enhanced_speaker
