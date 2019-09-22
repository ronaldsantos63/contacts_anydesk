import sys
import os
from typing import Any, List, Union, Dict

# Widgets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QSizeGrip
from PyQt5.QtWidgets import QItemDelegate
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QStyleOptionViewItem
from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import QStyleOptionButton

# Gui
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QIcon

# Core
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QProcess
from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QRect

# Datatabase
from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtSql import QSqlRecord
from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtSql import QSqlError

db: QSqlDatabase = None


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    if hasattr(sys, '_MEIPASS2'):
        return os.path.join(sys._MEIPASS2, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def connection() -> bool:
    global db

    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('database.db')
    if db.open():
        print(f'connected to database successfully')
        return True
    else:
        print('connection failed')
        return False


def create_table_contacts() -> bool:
    _cmd = QSqlQuery(db)
    return _cmd.exec_("create table if not exists contacts(id integer primary key autoincrement, "
                      "action varchar(10) DEFAULT 'ACESSAR', anydesk varchar(10) not null, name varchar(200) not null)")


class NewContact(QDialog):
    __model: QSqlTableModel
    __record: QSqlRecord = None
    __row: int = None
    __editing: bool

    def __init__(self, parent: QWidget = None, flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(), model: QSqlTableModel = None, record: QSqlRecord = None, row: int = None):
        super(NewContact, self).__init__(parent, flags)
        if not model:
            raise Exception('Model é obrigatório!')
        self.__model = model
        self.__init_ui()
        if not record:
            self.__editing = False
            self.__record = self.__model.record()
        else:
            self.__editing = True
            self.__record = record
            self.__row = row
            self.__populate()

    def __populate(self):
        self.anydesk_txt.setText(self.__record.value('anydesk'))
        self.name_txt.setText(self.__record.value('name'))
        self.anydesk_txt.selectAll()

    def __init_ui(self):
        self.setWindowIcon(QIcon(resource_path("logo.ico")))
        self.setWindowTitle('Contato')
        rootLayout = QGridLayout()

        anydesk_lbl = QLabel('Anydesk: ')
        self.anydesk_txt = QLineEdit()

        rootLayout.addWidget(anydesk_lbl, 0, 0)
        rootLayout.addWidget(self.anydesk_txt, 0, 1)

        name_lbl = QLabel('Nome: ')
        self.name_txt = QLineEdit()

        rootLayout.addWidget(name_lbl, 1, 0)
        rootLayout.addWidget(self.name_txt, 1, 1)

        hbox_btn = QHBoxLayout()
        save_btn = QPushButton('Salvar')
        cancel_btn = QPushButton('Cancelar')
        hbox_btn.addWidget(save_btn)
        hbox_btn.addWidget(cancel_btn)

        rootLayout.addWidget(QSizeGrip(self), 2, 0)
        rootLayout.addLayout(hbox_btn, 2, 1)

        self.setLayout(rootLayout)

        self.anydesk_txt.textEdited.connect(self.__set_anydesk)
        self.anydesk_txt.returnPressed.connect(
            self.__anydesk_txt_return_pressed)
        self.name_txt.textEdited.connect(self.__set_name)
        self.name_txt.returnPressed.connect(self.__name_txt_return_pressed)
        save_btn.clicked.connect(self.__save)
        cancel_btn.clicked.connect(self.__cancel)

    def __save(self) -> None:
        r = QMessageBox.question(self, 'Atenção',
                                 'Deseja salvar?',
                                 buttons=QMessageBox.Yes | QMessageBox.No,
                                 defaultButton=QMessageBox.Yes)
        if r == QMessageBox.Yes:
            if not self.anydesk_txt.text().strip():
                QMessageBox.warning(
                    self, 'Atenção', 'O campo anydesk é obrigatório')
                return
            if not self.name_txt.text().strip():
                QMessageBox.warning(
                    self, 'Atenção', 'O campo nome é obrigatório')
                return

            # * since the id field has the autoincrement attribute,
            # * it is not necessary to indicate its value,
            # * that is because this field of the request is removed.
            # self.__record.setValue('id', self.__contact.id)
            # self.__record.setValue("anydesk", self.__contact.anydesk)
            # record.setValue('name', self.__contact.name)

            if not self.__editing:
                self.__record.setValue('action', 'ACESSAR')
                # * -1 is set to indicate that it will be added to the last row
                if self.__model.insertRecord(-1, self.__record):
                    if not self.__model.submitAll():
                        self.__model.revertAll()
                        QMessageBox.critical(
                            self, 'Erro',
                            f'Ocorreu um erro ao salvar!\nErro: {self.__model.lastError().text()}')
                        return
                    # db.commit()
                    QMessageBox.information(
                        self, 'Informção',
                        'Salvo com sucesso!')
                    self.accept()
                else:
                    self.__model.revertAll()
                    QMessageBox.critical(
                        self, 'Erro',
                        f'Ocorreu um erro ao salvar!\nErro: {self.__model.lastError().text()}')
            else:
                if self.__model.updateRowInTable(self.__row, self.__record):
                    if not self.__model.submitAll():
                        self.__model.revertAll()
                        QMessageBox.critical(
                            self, 'Erro',
                            f'Ocorreu um erro ao salvar!\nErro: {self.__model.lastError().text()}')
                        return
                    # db.commit()
                    QMessageBox.information(
                        self, 'Informção',
                        'Salvo com sucesso!')
                    self.accept()
                else:
                    self.__model.revertAll()
                    QMessageBox.critical(
                        self, 'Erro',
                        f'Ocorreu um erro ao salvar!\nErro: {self.__model.lastError().text()}')

    def __cancel(self) -> None:
        self.reject()

    def __set_anydesk(self, value: str) -> None:
        self.__record.setValue('anydesk', value.strip())

    def __set_name(self, value: str) -> None:
        self.__record.setValue('name', value.strip())

    def __anydesk_txt_return_pressed(self):
        self.name_txt.setFocus()
        self.name_txt.selectAll()

    def __name_txt_return_pressed(self):
        self.__save()

    def keyPressEvent(self, ev: QKeyEvent):
        if ev.key() == Qt.Key_Return:
            ev.ignore()
            return


class ButtonDelegate(QStyledItemDelegate):
    clicked = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(ButtonDelegate, self).__init__(parent)
        self._pressed = None

    def paint(self, painter, option, index):
        painter.save()
        opt = QStyleOptionButton()
        opt.text = index.data()
        opt.rect = option.rect
        opt.palette = option.palette
        if self._pressed and self._pressed == (index.row(), index.column()):
            opt.state = QStyle.State_Enabled | QStyle.State_Sunken
        else:
            opt.state = QStyle.State_Enabled | QStyle.State_Raised
        QApplication.style().drawControl(QStyle.CE_PushButton, opt, painter)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonPress:
            # store the position that is clicked
            self._pressed = (index.row(), index.column())
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            if self._pressed == (index.row(), index.column()):
                # we are at the same place, so emit
                self.clicked.emit(*self._pressed)
            elif self._pressed:
                # different place.
                # force a repaint on the pressed cell by emitting a dataChanged
                # Note: This is probably not the best idea
                # but I've yet to find a better solution.
                oldIndex = index.model().index(*self._pressed)
                self._pressed = None
                index.model().dataChanged.emit(oldIndex, oldIndex)
            self._pressed = None
            return True
        else:
            # for all other cases, default action will be fine
            return super(ButtonDelegate, self).editorEvent(event, model, option, index)


class Window(QWidget):
    tbl_contacts: QTableView
    model: QSqlTableModel
    selectedIndex: QModelIndex = None

    def __init__(self) -> None:
        super().__init__()
        print(f'connect to datase: {connection()}')
        print(f'create table contacts: {create_table_contacts()}')
        self.__init_ui()
        self.__initialize_model()

    def __initialize_model(self) -> None:
        self.model.setTable('contacts')
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        # self.model.setQuery('SELECT * FROM contacts')

        self.model.setHeaderData(0, Qt.Horizontal, 'ID')
        self.model.setHeaderData(1, Qt.Horizontal, 'AÇÃO')
        self.model.setHeaderData(2, Qt.Horizontal, 'ANYDESK')
        self.model.setHeaderData(3, Qt.Horizontal, 'NOME')
        self.model.select()
        self.tbl_contacts.setColumnHidden(0, True)

    def __init_ui(self) -> None:
        self.setWindowIcon(QIcon(resource_path("logo.ico")))
        self.setWindowTitle('Lista de Contatos')
        self.model = QSqlTableModel()

        self.setMinimumSize(600, 400)
        hbox: QHBoxLayout = QHBoxLayout()

        self.tbl_contacts = QTableView()
        button_delegate = ButtonDelegate()
        button_delegate.clicked[int, int].connect(
            self.__on_click_button_delegate)
        self.tbl_contacts.setEditTriggers(QTableView.NoEditTriggers)
        # Type Selection
        self.tbl_contacts.setAlternatingRowColors(True)
        self.tbl_contacts.setSelectionMode(QTableView.SingleSelection)
        self.tbl_contacts.setSelectionBehavior(QTableView.SelectRows)
        self.tbl_contacts.setModel(self.model)
        self.tbl_contacts.setItemDelegateForColumn(1, button_delegate)
        # Enable sorting
        self.tbl_contacts.setSortingEnabled(True)
        # Adjust Header
        horizontal_header: QHeaderView = self.tbl_contacts.horizontalHeader()
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        horizontal_header.setStretchLastSection(True)
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size.setHorizontalStretch(1)
        self.tbl_contacts.setSizePolicy(size)
        # events
        self.tbl_contacts.clicked.connect(self.__set_selected_row)

        hbox.addWidget(self.tbl_contacts)

        vbox: QVBoxLayout = QVBoxLayout()

        self.new_btn: QPushButton = QPushButton('Novo')
        self.new_btn.clicked.connect(self.__new)
        self.edit_btn: QPushButton = QPushButton('Editar')
        self.edit_btn.clicked.connect(self.__edit)
        self.destroy_btn: QPushButton = QPushButton('Excluir')
        self.destroy_btn.clicked.connect(self.__destroy)

        vbox.addWidget(self.new_btn)
        vbox.addWidget(self.edit_btn)
        vbox.addWidget(self.destroy_btn)
        vbox.addStretch(1)

        hbox.addLayout(vbox)

        self.setLayout(hbox)
        self.show()

    def __new(self):
        dlg = NewContact(self, model=self.model)
        dlg.exec_()

    def __edit(self):
        if not self.selectedIndex:
            QMessageBox.warning(
                self, 'Atenção', 'É necessário selecionar um item para alterar!')
            return
        record: QSqlRecord = self.model.record(self.selectedIndex.row())
        dlg = NewContact(self, model=self.model, record=record,
                         row=self.selectedIndex.row())
        dlg.exec_()

    def __destroy(self):
        if self.selectedIndex:
            r = QMessageBox.question(
                self, 'Atenção',
                f'Tem certeza que deseja excluir o <b>{self.selectedIndex.data()}</b>',
                QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.No)
            if r == QMessageBox.Yes:
                self.model.deleteRowFromTable(self.selectedIndex.row())
                self.model.submitAll()

    def __access(self, row: int):
        record: QSqlRecord = self.model.record(row)
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.start('anydesk', [record.value('anydesk')])
        process.stateChanged.connect(
            lambda state: self.__state_process(row, state))

    def __set_selected_row(self, index: QModelIndex):
        self.selectedIndex = index

    def __state_process(self, row: int, state):
        status = {
            QProcess.NotRunning: 'ACESSAR',
            QProcess.Starting: 'ABRINDO',
            QProcess.Running: 'ACESSANDO'
        }
        print(f'Process: {status[state]}')
        self.__update_action(row, status[state])

    def __on_click_button_delegate(self, row: int, column: int):
        print(f'button_delegate - value1: {row} - value2: {column}')
        self.__access(row)

    def __update_action(self, row: int, message: str):
        record: QSqlRecord = self.model.record(row)
        record.setValue('action', message)
        if self.model.updateRowInTable(row, record):
            if not self.model.submitAll():
                self.model.revertAll()
                QMessageBox.critical(
                    self, 'Erro',
                    f'Ocorreu um erro ao salvar!\nErro: {self.model.lastError().text()}')
                return
        else:
            self.model.revertAll()
            QMessageBox.critical(
                self, 'Erro',
                f'Ocorreu um erro ao salvar!\nErro: {self.model.lastError().text()}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
