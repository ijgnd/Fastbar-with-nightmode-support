# -*- coding: utf-8 -*-
# pylint: skip-file
#
# Fastbar with nightmode support: an Anki 2.1 add-on adds a toolbar and toggle the sidebar
# in the Card Browser of Anki 2.1.
# Version: 0.1.1
# GitHub: https://github.com/luminousspice/anki-addons/
#
# Copyright: 2017 Luminous Spice <luminous.spice@gmail.com>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/copyleft/agpl.html
#
# Updated by The AnKing (https://www.ankingmed.com/)and /u/ijgnord
#
# Third party softwares used with Fastbar.
# QtAwesome. Copyright 2015 The Spyder development team.
# Released under the MIT License.
# https://github.com/spyder-ide/qtawesome/blob/master/LICENSE
# The Font Awesome is licensed under the SIL Open Font License.
# Six. Copyright 2010-2015 Benjamin Peterson
# Released under the MIT License.
# https://bitbucket.org/gutworth/six/src/LICENSE

# type: ignore

from aqt.qt import *
from PyQt5 import QtWidgets, QtCore
from aqt import (
    gui_hooks,
    mw,
)
from aqt.forms.browser import Ui_Dialog
from aqt.browser import Browser
from anki.sched import Scheduler as schedv1
from anki.schedv2 import Scheduler as schedv2
from anki.utils import ids2str, intTime
from anki.hooks import addHook, wrap

from . import qtawesome as qta


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    return fail


def maybe_import_other_addon(addon_id):
    try: 
        a = __import__(addon_id)
    except ModuleNotFoundError:
        return None
    else:
        return a


def check_other_addons():
    global BetterSearchAddon
    global ExtendedTagAddon
    BetterSearchAddon = maybe_import_other_addon("1052724801")  # BetterSearch
    ExtendedTagAddon = maybe_import_other_addon("1135507717")  # Extended Tag Add/Edit Dialog
gui_hooks.profile_did_open.append(check_other_addons)


from anki import version as anki_version
anki_21_version = int(anki_version.split(".")[-1]) 
if anki_21_version < 20:
    class Object():
        pass
    theme_manager = Object()
    theme_manager.night_mode = False
else:
    from aqt.theme import theme_manager


night_mode_on = False
def refresh_night_mode_state(nm_state):
    global night_mode_on
    if gc("switch to dark theme when add-on night mode is enabled"):
        night_mode_on = nm_state
addHook("night_mode_state_changed", refresh_night_mode_state)


night_mode_stylesheet = """
QToolBar { 
    background-color: #272828!important;
    background: #272828!important;
    spacing: 0px;
    color:  #272828!important;
}
QToolBar::separator{
    border: 0px solid #272828!important;
    background-color: #272828!important;
    background: #272828!important;
    margin-left: 0px;
    margin-right: 0px;
    width: 1px;
}
QToolButton {
    border: 0px solid #272828;
    border-radius: 0px;
    background-color: #272828;
    background: #272828!important;
    color:  #d7d7d7;
    margin-left: 0px;
    margin-right: 0px;
}    
QToolBar::handle {
    color: #272828;
    background:#272828;
    background-color: #272828;
}
QMacToolBar {
    border: 0px solid #272828!important;
    background-color: #272828!important;
    background: #272828!important;
    color: #272828!important;   
    spacing:0px;             
}
"""


class Fastbar:
    def addToolBar(self):  # self is browser
        tb = QToolBar("Fastbar")
        tb.setObjectName("Fastbar")
        tb.setIconSize(QtCore.QSize(15, 15))
        tb.setToolButtonStyle(3)

        self.form.actionToggle_Sidebar.triggered.connect(
            lambda: self.sidebarDockWidget.toggleViewAction().trigger()
        )
        self.form.actionToggle_Bury.triggered.connect(self.onBury)
        self.form.actionToggle_Fastbar.triggered.connect(
            lambda: tb.toggleViewAction().trigger()
        )

        self.form.actionDelete.setText("Delete Note")


        all_actions = [
            ["actionToggle_Fastbar", "ei.remove-sign"],       #  0
            ["actionToggle_Sidebar", "fa.exchange"],          #  1
            ["actionAdd", "fa.plus-square"],                  #  2
            ["action_Info", "fa.info-circle"],                #  3
            ["actionToggle_Mark", "fa.star"],                 #  4
            ["actionToggle_Suspend", "fa.pause-circle"],      #  5
            ["actionToggle_Bury", "fa.step-backward"],        #  6
            ["actionChange_Deck", "fa.inbox"],                #  7
            ["actionChangeModel", "fa.leanpub"],              #  8
            ["actionAdd_Tags", "fa.tag"],                     #  9
            ["actionRemove_Tags", "fa.eraser"],               # 10
            ["actionClear_Unused_Tags", "fa.magic"],          # 11
            ["actionDelete", "fa.trash-o"],                   # 12
            ["actionReschedule" if anki_21_version < 41 else "action_set_due_date", "fa.history"],
            ["actionReposition", "fa.sign-in"],
        ]
        ExTaDiNo = gc("button for Extended Tag Edit Addon", 12)
        if ExtendedTagAddon and ExTaDiNo:
            if hasattr(self, "ExTaDiAction"):
                all_actions.insert(ExTaDiNo, [self.ExTaDiAction, "fa.tags"])
        BeSeNo = gc("button for BetterSearch", 13)
        if BetterSearchAddon and BeSeNo:
            if hasattr(self, "BeSeAction"):
                all_actions.insert(BeSeNo, [self.BeSeAction, "fa.search-plus"])

        for idx, val in enumerate(all_actions):
            action_name, icon_name = val

            if isinstance(action_name, str):
                action = getattr(self.form, action_name, None)
            else:
                action = action_name

            if action is None:
                continue
            if gc("enable compact mode"):
                # TODO: Create custom QToolBar widget to handle word-wrapping
                # properly
                action_text = action.text()
                if " " in action_text:
                    word_wrapped_text = action_text.replace(" ", "\n", 1)
                else:
                    # hacky way to align single-line labels
                    # "\n" contains an invisible space, since qt strips tailing whitespace
                    word_wrapped_text = action_text + "\n‎"
                action.setText(word_wrapped_text)
            icon = qta.icon(icon_name, color="white" if night_mode_on or theme_manager.night_mode else "black")  
            action.setIcon(icon)
            tb.addAction(action)
            # if idx != len(all_actions)-1:  # python uses zero-based indexing
            #     tb.addSeparator()

        if night_mode_on:
            tb.setStyleSheet(night_mode_stylesheet)
        else:
            tb.setStyleSheet("QToolBar{spacing:0px;}")
        self.addToolBar(tb)

    def isBuried(self):
        if mw.col.schedVer() == 1:
            return not not (self.card and self.card.queue == -2)
        if mw.col.schedVer() == 2:
            return not not (self.card and self.card.queue in [-2, -3])

    def onBury(self):
        self.editor.saveNow(self._onBury)

    def _onBury(self):
        bur = not self.isBuried()
        c = self.selectedCards()
        if bur:
            self.col.sched.buryCards(c)
        else:
            self.col.sched.unburiedCards(c)
        self.model.reset()
        self.mw.requireReset()

    def unburiedCards(self, ids):
        "Unburied cards."
        self.col.log(ids)
        if mw.col.schedVer() == 1:
            self.col.db.execute(
                "update cards set queue=type,mod=?,usn=? "
                "where queue = -2 and id in " + ids2str(ids),
                intTime(),
                self.col.usn(),
            )
        elif mw.col.schedVer() == 2:
            self.col.db.execute(
                "update cards set queue=type,mod=?,usn=? "
                "where queue in (-2,-3) and id in " + ids2str(ids),
                intTime(),
                self.col.usn(),
            )

    def setupUi(self, Dialog):
        def createQAction(objname, text):
            out = QtWidgets.QAction(Dialog)
            out.setObjectName(objname)
            out.setText(text)
            return out
 
        self.actionToggle_Sidebar = createQAction("toggleSidebar", "Toggle Sidebar")
        self.actionToggle_Bury = createQAction("toggleBury", "Toggle Bury")
        self.actionToggle_Fastbar = createQAction("toggleFastbar", "Toggle Fastbar")

        self.menuJump.addSeparator()
        self.menuJump.addAction(self.actionToggle_Sidebar)
        self.menuJump.addAction(self.actionToggle_Fastbar)
        self.menu_Cards.addSeparator()
        self.menu_Cards.addAction(self.actionToggle_Bury)


addHook("browser.setupMenus", Fastbar.addToolBar)
Browser.isBuried = Fastbar.isBuried
Browser.onBury = Fastbar.onBury
Browser._onBury = Fastbar._onBury
schedv1.unburiedCards = Fastbar.unburiedCards
schedv2.unburiedCards = Fastbar.unburiedCards

Ui_Dialog.setupUi = wrap(Ui_Dialog.setupUi, Fastbar.setupUi)