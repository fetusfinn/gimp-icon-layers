#!/usr/bin/env python3
#
#   .ico layer scaler  
#      Finn Le Var
#
#  Copies the selected layer and scales it to the chosen 
#  sizes for the image to be exported to a .ico file
#

import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk


# the name of our plugin proc that gets created by GIMP
plugin_proc   = "flv-plugin-icon-layers"

# the name of our plugin script
plugin_binary = "create_icon_layers"

# the max number of layers that the user can create at once
max_layers    = 4

# where we want to log our ouputs to
log_file      = "D:/gimp_log.txt"

# whether we want logging enabled
logging       = False

#
# writes the given message to our log file
#
def msg(m):
    if logging:
        with open(log_file, "a") as f:
            f.write(f"{m}\n")

#
# our plugins main functionality
#
def plugin_main(procedure, run_mode, image, drawables, config, data):

    # if there are multiple drawables selected, then error and return since we only want one
    if len(drawables) > 1:
        return procedure.new_return_values (Gimp.PDBStatusType.CALLING_ERROR, GLib.Error(f"Procedure '{plugin_proc}' works with zero or one layer."))
    
    # we only want one drawable for our plugin
    elif len(drawables) == 1:

        # if the drawable isnt a layer, then error and return
        if not isinstance(drawables[0], Gimp.Layer):
            return procedure.new_return_values (Gimp.PDBStatusType.CALLING_ERROR, GLib.Error(f"Procedure '{plugin_proc}' works with layers only."))

        # get our layer
        layer    = drawables[0]

    # if we're in the interactive step, then create and show our dialog
    if run_mode == Gimp.RunMode.INTERACTIVE:
        
        # init GimpUI
        GimpUi.init(plugin_binary)

        # create our dialog
        dialog = GimpUi.ProcedureDialog.new(procedure, config, "Icon Sizes")

        # the names of different properties
        frame_name  = "toggle-frame-{}"
        tog_name    = "size-{}-toggle"
        size_name   = "size-{}"
        box_name    = "box-{}"

        # list of names of the frames that we've created and want to draw
        names     = []

        # list of box names to draw on our dialog
        box_names = []

        # names of the widgets to add to the next box
        box_items = []

        # our widgets
        frames  = []
        boxes   = []

        # how many frames we want per box
        frames_per_box = 2

        # create a frame for each layer
        for i in range(max_layers):

            # if the last toggle wasnt enabled then dont draw anything past that
            # if not last_tog:
            #     break
            
            # build this frames name and add it to our list
            names.append(frame_name.format(i))

            # build our toggle's name
            tog = tog_name.format(i)

            # add a frame that is enabled based on the corresponding toggle, for the corresponding size param 
            w = dialog.fill_frame(names[-1], tog, False, size_name.format(i))

            # store our widget
            frames.append(w)

            # add this frames name to our list of names for the next box
            box_items.append(names[-1])

            # if we've got two or more names for our box then create it and add them to it
            if len(box_items) >= frames_per_box:

                # store the 
                bname = box_name.format(len(boxes))

                # create our box using our 
                b = dialog.fill_box(bname, box_items)

                # set horizontal align
                b.set_orientation(Gtk.Orientation.HORIZONTAL)

                # store the widget
                boxes.append(b)

                # store our boxs name
                box_names.append(bname)

                # start fresh for the next box
                box_items.clear()

        # draw our items
        dialog.fill(box_names)

        # if okay wasnt pressed then just return here and exit
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
        
        # okay was pressed, just destroy our dialog and run the rest of our plugin script
        else:
            dialog.destroy()

    # the final sizes that we want to resize our icon layers to
    icon_sizes = []

    # get all the properties
    for i in range(max_layers):
        if config.get_property(tog_name .format(i)):
            icon_sizes.append(config.get_property(size_name.format(i)))
    
    msg(f"base layer : {layer.get_name()}")
    msg(f"copies to make : {len(icon_sizes)}")

    # if we have any enabled sizes
    if len(icon_sizes) > 0:

        msg("adding layers")

        # how many we've created so far, used for the position of the next layer
        created = 0

        # iterate backwards so we create them going big to small
        for size in reversed(icon_sizes):
            msg(f"  {size}")

            # create a new layer based off our base layer
            copy = Gimp.Layer.new_from_drawable(layer, image)

            # set its name to its size
            copy.set_name(f"{size}x{size}")

            # insert it into our image
            image.insert_layer(copy, None, -created)

            # scale our layer down to size
            copy.scale(size, size, False)

            # increase
            created += 1

        msg("finished creating layers")


    # make sure we've actually destroyed our dialog, shouldnt happen but to be safe
    if dialog is not None:
        dialog.destroy()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

#
# our plugin class that extends gimps plugin class
#
# need this to register our plugin
#
class icon_scaler(Gimp.PlugIn):

    def do_query_procedures(self):
        return [ plugin_proc ]

    # setup our plugins metadata
    def do_create_procedure(self, name):
        procedure = None

        # if the current process is ours, then set our metadata
        if name == plugin_proc:

            # create our proc and set the metadata
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, plugin_main, None)
            procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.NO_DRAWABLES)
            procedure.set_menu_label("Create Icon Layers")
            procedure.set_attribution("Finn Le var", "subcache.co", "2025")
            procedure.add_menu_path ("<Image>/Layer")
            procedure.set_documentation ("Duplicate the selected layer at different sizes", "Copies the selected layer and scales it to the chosen sizes for the image to be exported to a .ico file", name)

            # our different args for the user to set to be used by our plugin

            # base values for our args
            name     = "size-{}"
            nick     = "Layer {} size"
            desc     = "The size to scale this layer to"
            size_min = 16
            size_max = 512
            base_ext = 5
            tog_name = name + "-toggle"
            tog_nick = "Use layer"
            tog_desc = "Whether to duplicate and scale another layer"
            flags    = GObject.ParamFlags.READWRITE

            for i in range(max_layers):

                # int arg for our size element
                procedure.add_int_argument(name.format(i), nick.format(i+1), desc, size_min, size_max, (2 ** (base_ext + i)), flags)

                # bool arg for our toggles
                procedure.add_boolean_argument(tog_name.format(i), tog_nick, tog_desc, True,  flags)

        return procedure

# register our class in GIMP
Gimp.main(icon_scaler.__gtype__, sys.argv)