#!/usr/bin/env python3

# Tournament Software Suite: Signups module.

PACKAGE="CaliforniaBurst"
VERSION="0.1"
AUTHORS = [
  "Fred Lee <fredslee27@gmail.com>"
  ]
COPYRIGHT_LINE="Copyright 2017 Fred Lee <fredslee27@gmail.com"


import gtk  # Gtk 2.x
# Gtk2: because gtk2 likely to be ported to other platforms.

gtk.check_version(2, 20, 0)

import sys, os

#sys.path.append("./pychallonge.git")
#import challonge

import textwrap, time, random, pprint
try:
    import urllib2
except ImportError:
    # Assuming python3
    import urllib
import threading
import json


#LICENSE_GTK = Gtk.License.GPL_2_0

# If game list file not found, use this as default contents.
BUILTIN_GAMELIST = """\
GGX=Guilty Gear X
XRD=Guilty Gear Xrd Sign
XRDR=Guilty Gear Xrd Revelator
REV2=Guilty Gear Xrd Rev 2
ACR=Guilty Gear XX Accent Core +R
BBCF=BlazBlue Central Fiction
P4A=Persona 4 Arena
P4AU=Persona 4 Arena Ultimax
UNIB=Under Night In-Birth
UNIEL=Under Night In-Birth Exe: Late
AP=Aquapazza
DFC=Dengeki Bunko Fighting Climax
AH3=Arcana Heart 3
AH3LM=Arcana Heart 3 Love Max!!!!!
CVS2=Capcom vs SNK 2
U11=Ultimate 11
EXVS=Gundam Extreme Vs
EXFB=Gundam Extreme Vs Full Boost
EXMB=Gundam Extreme Vs Maxi Boost
"""
# override BUILTIN_GAMELIST; format is one string per line (as defined by python readline()).
GAMELIST_FILENAME="gamelist.txt"

# Filename extension for save file.
FILEEXT = "cburst"



def string_as_file (s):
    import io
    try:
        return io.StringIO(s)
    except TypeError:
        return io.StringIO(unicode(s))


class Gamelist (list):
    """List of games available for signup.
Elements are 2-tuples of: (short_name, long_name)
"""
    def __init__ (self, *args, **kwargs):
        """__init__ (self, fileobj=None)
If fileobj is not specified, use builtin gamelist.
        """
        list.__init__(self, *args, **kwargs)
        if len(args) > 0:
            self.import_file(args[0])
        elif "fileobj" in kwargs:
            self.import_file(kwargs["fileobj"])
        else:
            self.import_file(None)

    def __getitem__ (self, short_name):
        # Given short name, return reference to the corresponding entry in the list.
        # Expensive operation as it's not intended to be used often.
        filtered = [ x for x in self if x[0] == short_name ]
        if len(filtered) != 1:
            # Either not found, or more than one found.
            raise KeyError("Short name not resolvable: {}".format(short_name))
        return filtered[0]

    def import_file (self, fileobj):
        if fileobj is None:
            # Import default
            fileobj = string_as_file(BUILTIN_GAMELIST)
        for line in fileobj.readlines():
            if '=' in line:
                short_name, long_name = line.split('=', 1)
                self.append((short_name, long_name))
            else:
                pass

class Entrant (object):
    """Player and the games for which they registered."""
    def __init__ (self, name, gamelist=None):
        self.name = name
        if gamelist is None:
            gamelist = []
        self.gamelist = gamelist   # List of short_names.

class EntrantList (list):
    pass

class SignupsStore (object):
    """Checkpointed data store:
Gamelist
Players and the games for which they register.
Provisional links to exported tournaments (e.g. Challonge)
"""
    def __init__ (self):
        self.subtitle = None  # Session description, e.g. tournament name
        self.gamelist = Gamelist()
        self.entrants = EntrantList()

    def do_add_entrant (self, name__entrant, games=None, position=None):
        """add entrant to list, returns an Undo action.
  do_add_entrant(name, gameslist)
  do_add_entrant(Entrant(...))
        """
        if games is None:
            entrant = name__entrant
        else:
            entrant = Entrant(name__entrant, games)
        #self.entrants.append(entrant)
        if (position is not None) and (pos >= 0):
            self.entrants.insert(position, entrant)
        else:
            self.entrants.append(entrant)
        undo = ("do_remove_player", entrant.name)
        return undo

    def do_remove_entrant (self, name__entrant):
        """remove entrant from list, returns an Undo action (doubles as Redo).
"""
        try:
            ref = self.entrants[name]
        except KeyError:
            print("Data inconsistency: attempt to remove name which was not found: {}".format(name))
            # destroy undo history?
            return
        pos = self.entrants.find(ref)
        del self.entrants[pos]
        undo = ("do_add_player", ref.name, ref.gamelist, pos)
        return undo








class BasePaneling (object):
    """Paneling pattern:
Keep local field 'ui' holding Gtk widget.
Keep local data (extended ui state) outside of ui elements.
make_ui() in super to create from scratch.
build_ui() to populate UI.
"""
    def __init__ (self):
        self.ui = self.make_ui()
    def make_ui (self, substrate=None):
        if substrate is None:
            ui = gtk.HBox()
        else:
            ui = substrate
        self.build_ui(ui)
        ui.paneling = self
        return ui

class GamelistPaneling (BasePaneling):
    """Window panel (tab?) for modifying gamelist."""
    def build_ui (self, ui):
        pass

class EntrantlistPaneling (BasePaneling):
    """Window panel (tab?) for modifying entrants list: Player name and games desired."""
    def build_ui (self, ui):
        pass

class BracketPaneling (BasePaneling):
    """Panel/tab for handling tournament exports (setting up brackets)."""
    def build_ui (self, ui):
        pass

class MainPaneling (BasePaneling):
    """Main window, signups."""
    def build_ui (self, ui):
        pass
        

class SignupsMainW (gtk.Window):
    """Main window for signups."""
    def __init__ (self, subtitle=None):
        gtk.Window.__init__(self)
        self.build_ui(self, subtitle=subtitle)

    def build_ui (self, ui, subtitle=None):
        ui.set_size_request(640, 480)
        if subtitle is not None:
            self.set_subtitle(subtitle)
        ui.layout = gtk.VBox()
        ui.add(ui.layout)
        self.menubar = gtk.MenuBar()
        self.central = MainPaneling()
        self.statusbar = gtk.Statusbar()
        ui.layout.pack_start(self.menubar, False, True, 0)
        ui.layout.pack_start(self.central.ui, True, True, 0)
        ui.layout.pack_start(self.statusbar, False, True, 0)
        return ui

    def set_subtitle (self, subtitle):
        self.subtitle = subtitle
        self._full_title = "{}: {}".format(self.base_title, self.subtitle)
        self.set_title(self.full_title)

    def present_menubar (self, menudesc):
        pass



class SignupsUI (object):
    """UI state information and event handler.
Collects the various windows together if there are multiple.
Connects UI elements to actions (no store-modifying within widget instances).
"""
    # Intended to be subsumed into a larger "Tournament" GtkApplication,
    # so there shouldn't be a corresponding Signups(Gtk.Application).
    def __init__ (self, store=None):
        self.basetitle = "Signups"
        if store is None:
            store = SignupsStore()
        self.store = store
        self.build_ops()
        self.build_ui()

    def build_ui (self):
        self.mainw = SignupsMainW()
        self.mainw.connect("delete-event", self.on_close_main)

    def make_main_window (self, subtitle=None):
        mainw = gtk.Window()
        full_title = ""
        if subtitle:
            full_title = "{}: {}".format(self.basetitle, subtitle)
        else:
            full_title = self.basetitle
        mainw.set_title(full_title)
        mainw.set_size_request(640, 480)

    def build_main_menubar (self):
        MENUDESC = """<?xml version="1.0"?>
<ui>
  <menubar>
    <menu name="_File" action="act_FileMenu">
      <menuitem name="_New" action="act_file_new"/>
      <menuitem name="_Open" action="act_file_open"/>
      <menuitem name="_Save" action="act_file_save"/>
      <menuitem name="Save _As" action="act_file_saveas"/>
      <separator/>
      <menuitem name="_Quit" action="act_quit"/>
    </menu>
    <menu name="_Help" action="act_HelpMenu">
      <menuitem name="_Contents" action="act_help_contents"/>
      <menuitem name="_About" action="act_help_about"/>
    </menu>
  </menubar>
</ui>
"""
        return menubar

    def build_ops (self):
        """To support Undo, all actions affecting data should have a forward and reverse operation.
Operations without a reversible counterpart destroy Undo history.
Reverse operation may be a lambda that yields an action+arguments tuple.
"""
        pass

    def on_close_main (self, w, *args):
        # TODO: confirm save.
        gtk.main_quit()


if __name__ == "__main__":
    ui = SignupsUI()
    ui.mainw.show_all()
    gtk.main()

