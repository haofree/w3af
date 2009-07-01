import gtk
import gobject
from optsview import OptsView

class EditorPage(gtk.VBox):
    __gsignals__ = {
         'edited' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)), 
         'restored': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
         'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
         'closed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
         # should not allow to be closed in an inconsistent state
    }
 
    def __init__(self, optList, values):
        super(EditorPage, self).__init__()
        view = OptsView()
        for opt in optList:
            name = opt.getName()
            value = values[name] if name in values else opt.getDefaultValue()
            view.addOption(opt, value)
        
        view.connect('edited', self.__edited)
        view.connect('changed', self.__changed)
        view.connect('restored', self.__restored)
        self._view = view
        self.__fillContent()


    # view callbacks
    def __edited(self, widg, opts):
        self.emit('edited', opts)
        print opts

    def __changed(self, widg, *opt):
        self.emit('changed')
        print opt

    def __restored(self, *_):
        self.emit('restored')

    # buttons callbacks
    def __commit(self, *_):
        self._view.commit()

    def __rollback(self, *_):
        self._view.rollback()

    def __restoreDefaults(self, *_):
        self._view.resetDefaults()

    def __close(self, *_):
        if self._view.isUnsaved():
            dialog = gtk.Dialog()
            dialog.add_button("Save", gtk.RESPONSE_ACCEPT)
            dialog.add_button("Discard changes", gtk.RESPONSE_REJECT)
            dialog.add_button("Cancel", gtk.RESPONSE_CANCEL)
            response = dialog.run()
            dialog.destroy()

            if response==gtk.RESPONSE_ACCEPT:
                self.__commit()
            elif response==gtk.RESPONSE_REJECT:
                self.__rollback()
            elif response==gtk.RESPONSE_CANCEL:
                return

        self.emit('closed')


    def __fillContent(self):
        self.pack_start(self._view)

        # Will need buttons: save, restore defaults, undo changes, close
        okButton = gtk.Button("Save")
        okButton.connect('clicked', self.__commit)
        undoButton = gtk.Button("Undo")
        undoButton.connect('clicked', self.__rollback)
        defaultButton = gtk.Button('Restore defaults')
        defaultButton.connect('clicked', self.__restoreDefaults)
        closeButton = gtk.Button("Close")
        closeButton.connect('clicked', self.__close)

        self.pack_end(okButton)
        self.pack_end(undoButton)
        self.pack_end(defaultButton)
        self.pack_end(closeButton)


class EditorNotebook(gtk.Notebook):
    def __init__(self):
        super(EditorNotebook, self).__init__()
        self._pagesByName = {} # name --> (index, page)
        self._pagesByIdx = {} # index --> (name, page)
    
    def open(self, name, optList, values):
        if name in self._pagesByName:
            idx, page = self._pagesByName[name]
            self.set_current_page(idx)
            return page

        page = EditorPage(optList, values)
        label = gtk.Label(name)
        idx = self.append_page(page, tab_label=label)
        self._pagesByName[name] = (idx, page)
        self._pagesByIdx[name] = (name, page)

        page.connect('edited', self.__clearLabel, name)
        page.connect('restored', self.__clearLabel, name) 
        page.connect('changed', self.__markLabel, name) 
        page.connect('closed', self.__closed, name)

    def __setLabel(self, page, text):
        label = self.get_tab_label(page)
        if label:
            label.set_markup(text)

    def __clearLabel(self, page, *rest):
        name = rest[-1]
        self.__setLabel(page, name)

    def __markLabel(self, page, *rest):
        name = rest[-1]
        self.__setLabel(page, "<b>%s</b>" % name)

    def __closed(self, page, name):
        idx = self._pagesByName[name][0]
        self.remove_page(idx)

gobject.type_register(EditorPage)
