#!/usr/bin/env python3

# Tournament Software Suite: Signups module.
# Use checkpointing to avoid explicit Open/save.

PACKAGE="CaliforniaBurst"
VERSION="0.1"
AUTHORS = [
  "Fred Lee <fredslee27@gmail.com>"
  ]
COPYRIGHT_LINE="Copyright 2017 Fred Lee <fredslee27@gmail.com"
APP_DESCRIPTION="GUI for handling tournament signups."""


import gtk  # Gtk 2.x
import gobject
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


class Gamelist0 (list):
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

class GamelistStore (gtk.ListStore):
    """List of games: (short_code, game_title, full_desc)"""
    def __init__ (self, *args, **kwargs):
        gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.connect("row-inserted", self.on_row_inserted)
        self.changing = self.connect("row-changed", self.on_row_changed)
        self.connect("row-deleted", self.on_row_deleted)

    def import_file (self, fileobj):
        if fileobj is None:
            fileobj = string_as_file(BUILTIN_GAMELIST)
        for line in fileobj.readlines():
            if '=' in line:
                short_name, long_name = line.strip().split('=', 1)
                #fulldesc = "{}={}".format(short_name, long_name)
                #self.append((short_name, long_name, fulldesc))
                self.append((short_name, long_name, None))
            else:
                pass

    def on_row_inserted (self, mdl, path, treeiter, *args):
        pass
#        entry = mdl[treeiter]
#        full_desc = "{}={}".format(entry[0], entry[1])
#        #entry[2] = full_desc
#        mdl.set_value(treeiter, 2, full_desc)
#        print("update full_desc: %r,%r,%r" % (mdl[treeiter][0], mdl[treeiter][1], mdl[treeiter][1]))
#        return True

    def on_row_changed (self, mdl, path, treeiter, *args):
        entry = mdl[treeiter]
        full_desc = "{}={}".format(entry[0], entry[1])
        mdl.handler_block(self.changing)
        mdl.set_value(treeiter, 2, full_desc)
        mdl.handler_unblock(self.changing)
        return True

    def on_row_deleted (self, mdl, path, *args):
        return True

class Entrant (object):
    """Player and the games for which they registered."""
    def __init__ (self, name, gamelist=None):
        self.name = name
        if gamelist is None:
            gamelist = []
        self.gamelist = gamelist   # List of short_names.

class EntrantList (list):
    pass

class EntrantStore (gtk.ListStore):
    """List of entrants, for a game: (index_into_EntrantStore, name)
Special case game==None: (None, name) 
Typical case game!=None: (index_into_EntrantStore, None)
"""
    def __init__ (self):
        gtk.ListStore.__init__(self, gobject.TYPE_INT, gobject.TYPE_STRING)

#class EntrantStore (gtk.ListStore):
#    """data model for signups sheet: (name, checkbox, ...)"""
#    def __init__ (self):
#        gtk.ListStore.__init__(self, gobject.TYPE_STRING)
#
#    def resize (self, num_games):
#        pass

class SignupsStore (object):
    """Checkpointed data store:
Gamelist
Players and the games for which they register.
Provisional links to exported tournaments (e.g. Challonge)
"""
    def __init__ (self):
        self.subtitle = None  # Session description, e.g. tournament name
        self.presetlist = GamelistStore()
        self.presetlist.import_file(None)
        self.gamelist = GamelistStore()
        self.entrantlist = EntrantStore()

    def do_add_entrant (self, name, game=None, position=None):
        """add entrant to list, returns an Undo action.
  do_add_entrant(name, None) - global list
  do_add_entrant(name, game) - add entrant to particular game

Returns: Undo action
        """
        targetlist = None
        if not game:
            # global list
            targetlist = self.entrantlist
        else:
            # particular game.
            targetlist = None
        if targetlist is None:
            return None
        if (position is not None) and (position >= 0):
            targetlist.insert(position, (0, name))
        else:
            targetlist.append((0, name))
        undo = (self.do_remove_entrant, (name, game))
        return undo

    def do_remove_entrant (self, name, game=None):
        """remove entrant from list, returns an Undo action (doubles as Redo).
  do_remove_entrant(name, game) - remove entrant from particular game.

Returns: Undo action
"""
        targetlist = None
        if not targetlist:
            # Do not remove from global list; only modify in place.
            return None
        culls = [ gtk.TreeRowReference(targetlist, it) for it in targetlist if it.name == name ]
        if culls:
            targetlist.remove(cull[0])
            undo = (self.do_add_entrant, (name, game))
            return undo
        return None

    def do_add_games (self, gameinfolist, positions=None):
        """Add games to gamelist:
do_add_games([ (short_code, game_title, full_desc), ...])

Returns: Undo action
"""
        undoable = []
        for gameidx in range(len(gameinfolist)):
            gameinfo = gameinfolist[gameidx]
            short_code = game_title = full_desc = None
            try:
                short_code = gameinfo[0]
                game_title = gameinfo[1]
                full_desc = gameinfo[2]
            except IndexError:
                pass
            if positions:
                pos = positions[gameidx]
                self.gamelist.insert(pos, (short_code, game_title, full_desc))
            else:
                self.gamelist.append((short_code, game_title, full_desc))
            undoable.append(short_code)
        undo = (self.do_remove_games, (undoable,))
        return undo

    def do_remove_games (self, short_code_list):
        """Remove games from gamelist:
do_remove_games ([ short_code, ...])

Returns: Undo action
"""
        undoable = [] # Row data.
        undopos = []  # Original positions per row data.
        culls = []
        for gameidx in range(len(self.gamelist)):
            rowiter = self.gamelist.get_iter(gameidx)
            rowdata = self.gamelist.get(rowiter, 0, 1, 2)
            if rowdata[0] in short_code_list:
                treepath = self.gamelist.get_path(rowiter)
                treeref = gtk.TreeRowReference(self.gamelist, treepath)
                culls.append(treeref)
                undoable.append(rowdata)
                undopos.append(gameidx)
        for culliter in culls:
            culliter = self.gamelist.get_iter(culliter.get_path())
            self.gamelist.remove(culliter)
        undo = (self.do_add_games, (undoable,undopos))
        return undo






class BasePaneling (object):
    """Paneling pattern:
Keep local field 'ui' holding Gtk widget.
Keep local data (extended ui state) outside of ui elements.
make_ui() in super to create from scratch.
build_ui() to populate UI.
"""
    SUBSTRATE = gtk.HBox
    def __init__ (self):
        self.ui = self.make_ui()
    def make_ui (self, substrate=None):
        if substrate is None:
            ui = self.SUBSTRATE()
        else:
            ui = substrate
        self.build_ui(ui)
        ui.paneling = self
        return ui

class GamelistPaneling (BasePaneling):
    """Window panel (tab?) for modifying gamelist."""
    def build_ui (self, ui):
        self.preset_model = None
        self.choose_model = None

        self.presetview = gtk.TreeView(self.preset_model)
        self.txtrender = gtk.CellRendererText()
        col0 = gtk.TreeViewColumn('Presets', self.txtrender, text=2)
        self.presetview.append_column(col0)
        ui.pack_start(self.presetview, True, True, 0)

        transfercol = gtk.VBox()
        spacer0 = gtk.Label()
        spacer1 = gtk.Label()
        spacer2 = gtk.Label()
        self.btn_add = gtk.Button("_Add")
        self.btn_del = gtk.Button("_Del")
        transfercol.pack_start(spacer0, True, True, 0)
        transfercol.pack_start(self.btn_add, False, False, 0)
        transfercol.pack_start(spacer1, False, True, 0)
        transfercol.pack_start(self.btn_del, False, False, 0)
        transfercol.pack_start(spacer2, True, True, 0)
        ui.pack_start(transfercol, False, True, 0)

        choosecol = gtk.VBox()
        self.chooseview = gtk.TreeView(self.choose_model)
        self.txtrender2 = gtk.CellRendererText()
        col0 = gtk.TreeViewColumn('Chosen', self.txtrender2, text=2)
        self.chooseview.append_column(col0)

        manualrow = gtk.HBox()
        self.lbl_manual = gtk.Label("Game:")
        self.entry_manual = gtk.Entry()
        self.btn_manual = gtk.Button("_Manual Add")
        manualrow.pack_start(self.lbl_manual, False, False, 0)
        manualrow.pack_start(self.entry_manual, True, True, 0)
        manualrow.pack_start(self.btn_manual, False, False, 0)
        choosecol.pack_start(self.chooseview, True, True, 0)
        choosecol.pack_start(manualrow, False, True, 0)
        ui.pack_start(choosecol, True, True, 0)

        return

    def set_preset_model (self, mdl):
        self.preset_model = mdl
        self.presetview.set_model(self.preset_model)

    def set_choose_model (self, mdl):
        self.choose_model = mdl
        self.chooseview.set_model(self.choose_model)

class EntrantlistPaneling (BasePaneling):
    """Window panel (tab?) for modifying entrants list: Player name and games desired."""
    def build_ui (self, ui):
        return

class BracketPaneling (BasePaneling):
    """Panel/tab for handling tournament exports (setting up brackets)."""
    def build_ui (self, ui):
        return

class MainPaneling (BasePaneling):
    """Main window, signups."""
    SUBSTRATE = gtk.Notebook
    def build_ui (self, ui):
        self.gamelist = GamelistPaneling()
        self.entrantlist = EntrantlistPaneling()
        self.bracketing = BracketPaneling()
        ui.set_tab_pos(gtk.POS_LEFT)
        ui.append_page(self.gamelist.ui, gtk.Label("1 Gamelist"))
        ui.append_page(self.entrantlist.ui, gtk.Label("2 Signups"))


class SignupsMainW (gtk.Window):
    """Main window for signups."""
    def __init__ (self, subtitle=None, menubar=None, presetlist_model=None, gamelist_model=None, entrantlist_model=None, bracketlist_model=None):
        gtk.Window.__init__(self)
        # list of games
        self.presetlist_model = presetlist_model
        self.gamelist_model = gamelist_model
        # list of entrants
        self.entrantlist_model = entrantlist_model
        # list of tracked exported brackets.
        self.bracketlist_model = bracketlist_model
        self.build_ui(self, subtitle=subtitle, menubar=menubar)

    def build_ui (self, ui, subtitle=None, menubar=None):
        ui.set_size_request(640, 480)
        if subtitle is not None:
            self.set_subtitle(subtitle)
        ui.layout = gtk.VBox()
        ui.add(ui.layout)
        self.menubar = menubar or gtk.MenuBar()
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

class SignupsAboutW (gtk.AboutDialog):
    """About dialog."""
    def __init__ (self):
        gtk.AboutDialog.__init__(self)
        self.set_name(PACKAGE)
        self.set_version(VERSION)
        self.set_license("GNU General Public License v2.0 or later")
        self.set_authors(AUTHORS)
        self.set_comments(APP_DESCRIPTION)


class ActionHistory (gtk.ListStore):
    """Action history, utilized for undo history.
'cursor' point to current history node row.    
Each row correlates to a specific state of data, transitions record the changes to the state.
For each row, the 'undo' column restores state from future node;
the 'redo' column restores state to future node.
"""
    def __init__ (self, undo_action=None, redo_action=None):
        # Tuple of (undo_func, undo_args, redo_func, redo_args)
        gtk.ListStore.__init__(self, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
        self.count = 0
        self.cursor = None  # Current point in action history.
        self.undo_action = undo_action
        self.redo_action = redo_action
        if self.undo_action:
            self.undo_action.set_sensitive(False)
        if self.redo_action:
            self.redo_action.set_sensitive(False)

    def boh (self):
        """Predicate: at Beginning of History (disable Undo)"""
        return (self.cursor is None) or (self.count <= 0)

    def eoh (self):
        """Predicate: at End of History (disable Redo)"""
        return self.cursor >= self.count

    def backtrack (self):
        """Step one backwards in history, as Undo."""
        if self.cursor >= 0:
            track = self.cursor - 1
            node = self[track]
            func, args = node[0], node[1]
            redo = func(*args)
            self.cursor -= 1
            if self.redo_action:
                self.redo_action.set_sensitive(True)
        if self.cursor <= 0:
            if self.undo_action:
                self.undo_action.set_sensitive(False)
        return self.cursor >= 0

    def foretrack (self):
        """Step one forward in history, as Redo."""
        if self.cursor < self.count:
            track = self.cursor
            node = self[track]
            func, args = node[2], node[3]
            undo = func(*args)
            self.cursor += 1
            if self.undo_action:
                self.undo_action.set_sensitive(True)
        if self.cursor >= self.count:
            if self.redo_action:
                self.redo_action.set_sensitive(False)
        return self.cursor < self.count

    def redcut (self):
        """Cut history at cursor, as overwriting Redo stack."""
        if self.cursor is not None:
            marks = range(self.cursor, len(self))
            culls = [ gtk.TreeRowRefernce(rowiter) for rowiter in marks ]
            for cull in culls:
                self.remove(cull.get_iter())
            self.count -= len(culls)
            self.cursor = self.count
        if self.redo_action:
            self.redo_action.set_sensitive(False)
        return

    def commit (self, transaction, undo):
        """Add one action step into history.
  transaction - current call to step forward in history (new action).
  undo - future call to make on an undo; if None, cuts Undo stack (action cannot be undone).
"""
        if undo is None:
            self.clear()
            enditer = self.append((None, None, transaction[0], transaction[1]))
        else:
            enditer = self.append((undo[0], undo[1], transaction[0], transaction[1]))
        self.count += 1
        self.cursor = self.count
        if self.undo_action:
            self.undo_action.set_sensitive(True)
        if self.redo_action:
            self.redo_action.set_sensitive(False)

    def advance (self, do, *args):
        """Typical case of new user action, erasing Redo stack."""
        self.redcut()
        undo = do(*args)
        self.commit((do, args), (undo[0], undo[1]))

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
        self.accel_group = gtk.AccelGroup()
        self.action_group = gtk.ActionGroup("global")
        self.build_ops()
        self.build_ui()
        self.mainw.add_accel_group(self.accel_group)
        self.undostack = []   # The Undo stack
        self.redostack = []   # The Redo stack
        self.history = ActionHistory(self.act_edit_undo, self.act_edit_redo)  # Undo/Redo stack.

    def build_ui (self):
        self.menubar = self.build_main_menubar()
        self.mainw = SignupsMainW(menubar=self.menubar)
        self.mainw.connect("delete-event", self.on_close_main)
        self.mainw.central.gamelist.set_preset_model(self.store.presetlist)
        self.mainw.central.gamelist.set_choose_model(self.store.gamelist)

        uigamelist = self.mainw.central.gamelist
        uigamelist.presetview.connect("row-activated", self.on_presetview_row_activated)
        self.act_gamelist_pick.connect_proxy(uigamelist.btn_add)
        self.act_gamelist_del.connect_proxy(uigamelist.btn_del)
        self.act_gamelist_manual.connect_proxy(uigamelist.btn_manual)

        self.aboutdlg = SignupsAboutW()

    def make_main_window (self, subtitle=None):
        mainw = gtk.Window()
        full_title = ""
        if subtitle:
            full_title = "{}: {}".format(self.basetitle, subtitle)
        else:
            full_title = self.basetitle
        mainw.set_title(full_title)
        mainw.set_size_request(640, 480)

    def make_menu (self, menudesc, variant=None):
        """
menudesc is list of 3-tuples = (label, action, accelerator)
submenu when action is menudesc (i.e. list of 3-tuples)
"""
        if variant is None:
            variant = gtk.Menu
        menu = variant()
        for desciter in menudesc:
            # desciter <- None   =>  Menu Separator
            # desciter <- gtk.Action()  =>  GtkAction proxy
            # desciter <- (lbl, cb, hotkey=None)  =>  direct menu item
            # desciter <- (lbl, [submenu]) => submenu
            menuitem = None
            if desciter is None:
                menuitem = gtk.SeparatorMenuItem()
            else:
                menuitem = None
                try:
                    desciter.connect_proxy
                    #menuitem = gtk.MenuItem(use_underline=True)
                    menuitem = gtk.ImageMenuItem()
                    desciter.connect_proxy(menuitem)
                except AttributeError:
                    pass
                if menuitem is None:
                    lbl = action = accel = None
                    try:
                        lbl = desciter[0]
                        action = desciter[1]
                        accel = desciter[2]
                    except IndexError:
                        pass
                    menuitem = gtk.MenuItem(lbl, use_underline=True)
                    if isinstance(action, list):
                        submenu = self.make_menu(action)
                        menuitem.set_submenu(submenu)
                    elif callable(action):
                        menuitem.connect("activate", action)
                    if accel:
                        keyval, keymod = None, None
                        if isinstance(accel, tuple):
                            keyval, keymod = accel
                        elif accel:
                            accel = gtk.accelerator_parse(accel)
                            if keyval is not None:
                                menuitem.add_accelerator("activate", self.accel_group, keyval, keymod, gtk.ACCEL_VISIBLE)
            if menuitem:
                menu.append(menuitem)
        return menu

    def push_undo (self, undoinfo, preserve_redo=False):
        """Store new undo node because of a new action.  Destroys redo stack."""
        if not preserve_redo:
            self.redostack = []
        self.undostack.append(undoinfo)
    def pop_undo (self):
        """Help execute an undo action."""
        undoinfo = None
        if self.undostack:
            undoinfo = self.undostack.pop()
        return undoinfo
    def push_redo (self, redoinfo):
        """Store a new redo action after carrying out an undo."""
        self.redostack.append(redoinfo)
    def pop_redo (self):
        """Help execute a redo operation."""
        redoinfo = None
        if self.redostack:
            redoinfo = self.redostack.pop()
        return redoinfo

    def make_menubar (self, menubardesc):
        menubar = self.make_menu(menubardesc, variant=gtk.MenuBar)
        return menubar

    def build_main_menubar (self):
        # menuitem <- ( stock_id, gtkAction )
        # menuitem <- ( stock_id, callback, accelerator )
        # menuitem <- ( menu_label, gtkAction )
        # menuitem <- ( menu_label, callback, accelerator )
        # menuitem <- ( menu_label, [ submenu_description ] )
        MENUDESC = [
          ('_File', [
            self.act_file_new,
            self.act_file_open,
            self.act_file_save,
            self.act_file_saveas,
            None,
            self.act_file_close,
            None,
            self.act_quit,
            ]),
          ('_Edit', [
            self.act_edit_undo,
            self.act_edit_redo,
            None,
            self.act_edit_cut,
            self.act_edit_copy,
            self.act_edit_paste,
            None,
            self.act_preferences,
            ]),
          ('_Help', [
            self.act_help,
            None,
            self.act_about,
            ]),
          ]
        return self.make_menubar(MENUDESC)

    def build_ops (self):
        """To support Undo, all actions affecting data should have a forward and reverse operation.
Operations without a reversible counterpart destroy Undo history.
Reverse operation may be a lambda that yields an action+arguments tuple.
"""
        def make_action (name, label, hint, stockid, cb, hotkey=None):
            act = gtk.Action(name, label, hint, stockid)
            act.connect("activate", cb)
            act.set_accel_group(self.accel_group)
            self.action_group.add_action_with_accel(act, hotkey)
            act.connect_accelerator()
            self.__dict__.__setitem__(name, act)
        make_action("act_file_new", "_New", "Create new session", gtk.STOCK_NEW, self.nop, "<Control>n")
        make_action("act_file_open", "_Open", "Restore a session", gtk.STOCK_OPEN, self.on_file_open)
        make_action("act_file_save", "_Save", "Save session", gtk.STOCK_SAVE, self.on_file_save)
        make_action("act_file_saveas", "Save _As", "Save session", gtk.STOCK_SAVE_AS, self.on_file_saveas, "<Control><Shift>s")
        make_action("act_file_close", "_Close", "Close session", gtk.STOCK_CLOSE, self.on_file_close)
        make_action("act_quit", "_Quit", "Quit application", gtk.STOCK_QUIT, self.on_close_main)
        make_action("act_edit_undo", "Undo", "Undo action", gtk.STOCK_UNDO, self.on_edit_undo, "Undo")
        make_action("act_edit_redo", "Redo", "Redo action", gtk.STOCK_REDO, self.on_edit_redo, "Redo")
        make_action("act_edit_cut", "C_ut", "Cut", gtk.STOCK_CUT, self.nop)
        make_action("act_edit_copy", "_Copy", "Copy", gtk.STOCK_COPY, self.nop)
        make_action("act_edit_paste", "_Paste", "Paste", gtk.STOCK_PASTE, self.nop)
        make_action("act_preferences", "Pr_eferences", "Change preferences", gtk.STOCK_PREFERENCES, self.nop)
        make_action("act_help", "_Contents", "Help contents", gtk.STOCK_HELP, self.nop)
        make_action("act_about", "_About", "About application", gtk.STOCK_ABOUT, self.on_about)

        make_action("act_gamelist_pick", "_Add", "Add preset to chosen", None, self.on_gamelist_pick)
        make_action("act_gamelist_del", "_Del", "Delete chosen entry", None, self.on_gamelist_del)
        make_action("act_gamelist_manual", "_Manual Add", "Manually add chosen game", None, self.on_gamelist_manual)
        return

    def on_accel (self, *args):
        print("on_accel: %r" % (args,))

    def nop (self, w, *args):
        print("nop")
        return True

    def on_file_open (self, w, *args):
        print("load")
        return True

    def on_file_open (self, w, *args):
        return True

    def on_file_save (self, w, *args):
        return True

    def on_file_saveas (self, w, *args):
        return True

    def on_file_close (self, w, *args):
        return True

    def on_edit_undo (self, w, *args):
        self.history.backtrack()
        return True

    def on_edit_redo (self, w, *args):
        self.history.foretrack()
        return True

    def on_edit_cut (self, w, *args):
        return True

    def on_edit_copy (self, w, *args):
        return True

    def on_edit_paste (self, w, *args):
        return True

    def on_preferences (self, w, *args):
        return True

    def on_help_contents (self, w, *args):
        return True

    def on_about (self, w, *args):
        self.aboutdlg.run()
        self.aboutdlg.hide()
        return True

    def on_presetview_row_activated (self, w, *args):
        presetview = w
        treesel = presetview.get_selection()
        sels = treesel.get_selected_rows()
        if not sels:
            return True
        mdl, rows = sels
        #for row in rows:
        #    self.store.gamelist.append(self.store.presetlist[row])
        gameinfolist = [ self.store.presetlist[row] for row in rows ]
        self.history.advance(self.store.do_add_games, gameinfolist)
        return True

    def on_gamelist_pick (self, w, *args):
        uigamelist = self.mainw.central.gamelist
        presetview = uigamelist.presetview
        treesel = presetview.get_selection()
        sels = treesel.get_selected_rows()
        if not sels:
            return True
        mdl, rows = sels
        #for row in rows:
        #    self.store.gamelist.append(self.store.presetlist[row])
        gameinfolist = [ self.store.presetlist[row] for row in rows ]
        self.history.advance(self.store.do_add_games, gameinfolist)
        return True

    def on_gamelist_del (self, w, *args):
        uigamelist = self.mainw.central.gamelist
        chooseview = uigamelist.chooseview
        treesel = chooseview.get_selection()
        sels = treesel.get_selected_rows()
        if not sels:
            return True
        mdl, rows = sels
        #culls = [ gtk.TreeRowReference(mdl, row) for row in rows ]
        #for cullref in culls:
        #    treeiter = mdl.get_iter(cullref.get_path())
        #    mdl.remove(treeiter)
        culls = [ row[0] for row in rows ]
        self.history.advance(self.store.do_remove_games, culls)
        return True

    def on_gamelist_manual (self, w, *args):
        uigamelist = self.mainw.central.gamelist
        manual_entry = uigamelist.entry_manual
        fulldesc = manual_entry.get_text()
        if fulldesc:
            if '=' in fulldesc:
                short_name, game_title = fulldesc.split('=', 1)
                gameinfo = (short_name, game_title, None)
            else:
                gameinfo = (short_name, game_title, None)
            manual_entry.set_text("")
            self.history.advance(self.store.do_add_games, [gameinfo])
            return True
        else:
            return False

    def on_close_main (self, w, *args):
        # TODO: confirm save.
        print("quit")
        gtk.main_quit()


if __name__ == "__main__":
    store = SignupsStore()
    ui = SignupsUI(store)
    ui.mainw.show_all()
    gtk.main()

