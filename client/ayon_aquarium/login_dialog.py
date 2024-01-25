import requests

from qtpy import QtCore, QtGui, QtWidgets

from openpype import style, resources
from openpype.tools.utils import PlaceholderLineEdit

from .credentials import check_credentials, save_credentials


class CredentialsDialog(QtWidgets.QDialog):
    SIZE_W = 300
    SIZE_H = 230

    login_changed = QtCore.Signal()
    logout_signal = QtCore.Signal()

    def __init__(self, module, parent=None):
        super(CredentialsDialog, self).__init__(parent)

        self.setWindowTitle("AYON - Aquarium Login")

        icon = QtGui.QIcon(resources.get_openpype_icon_filepath())
        self.setWindowIcon(icon)

        self.setWindowFlags(
            QtCore.Qt.WindowCloseButtonHint
            | QtCore.Qt.WindowMinimizeButtonHint
        )

        self._module = module

        self._is_logged = False
        self._validated_url = None

        # --- Inputs ---
        inputs_widget = QtWidgets.QWidget(self)

        username_label = QtWidgets.QLabel("Username:", inputs_widget)
        password_label = QtWidgets.QLabel("Password:", inputs_widget)

        server_label = QtWidgets.QLabel(inputs_widget)
        server_label.setTextInteractionFlags(
            QtCore.Qt.TextBrowserInteraction
        )
        server_label.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))

        username_input = QtWidgets.QLineEdit(inputs_widget)
        username_input.setPlaceholderText("user.name@example.com")

        password_input = PlaceholderLineEdit(inputs_widget)
        password_input.setPlaceholderText("***secure***")
        password_input.setEchoMode(PlaceholderLineEdit.Password)

        input_layout = QtWidgets.QFormLayout(inputs_widget)
        input_layout.setContentsMargins(10, 15, 10, 5)
        input_layout.addRow("Aquarium URL:", server_label)
        input_layout.addRow(username_label, username_input)
        input_layout.addRow(password_label, password_input)

        # --- Error label for user ---
        messages_wrapper = QtWidgets.QWidget(self)
        user_message_label = QtWidgets.QLabel("", messages_wrapper)
        user_message_label.setWordWrap(True)

        messages_layout = QtWidgets.QVBoxLayout(messages_wrapper)
        messages_layout.setContentsMargins(10, 5, 10, 5)
        messages_layout.addWidget(user_message_label)

        # --- Buttons ---
        btns_widget = QtWidgets.QWidget(self)

        btn_login = QtWidgets.QPushButton("Login", btns_widget)
        btn_login.setToolTip(
            "Set Username and API Key with entered values"
        )
        btn_login.clicked.connect(self._on_login_clicked)

        btn_logout = QtWidgets.QPushButton("Logout", btns_widget)
        btn_logout.clicked.connect(self._on_logout_clicked)

        btn_close = QtWidgets.QPushButton("Close")
        btn_close.setToolTip("Close this window")
        btn_close.clicked.connect(self._close_widget)

        btns_layout = QtWidgets.QHBoxLayout(btns_widget)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.addStretch(1)
        btns_layout.addWidget(btn_login, 0)
        btns_layout.addWidget(btn_logout, 0)
        btns_layout.addWidget(btn_close, 0)

        # --- Main window layout ---
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(inputs_widget, 0)
        main_layout.addWidget(messages_wrapper, 0)
        main_layout.addStretch(1)
        main_layout.addWidget(btns_widget, 0)

        self.login_changed.connect(self._on_login)

        self._server_label = server_label

        self._username_input = username_input
        self._password_input = password_input

        self._user_message_label = user_message_label

        self._btn_login = btn_login
        self._btn_logout = btn_logout

        self._update_widget_states()

        self.setMinimumSize(QtCore.QSize(self.SIZE_W, self.SIZE_H))
        self.setMaximumSize(QtCore.QSize(self.SIZE_W + 100, self.SIZE_H + 100))
        self.setStyleSheet(style.load_stylesheet())

    def showEvent(self, event):
        super().showEvent(event)
        self._update_url()

    def closeEvent(self, event):
        event.ignore()
        self._close_widget()

    def set_is_logged(self, is_logged):
        self._is_logged = is_logged

        self._update_widget_states()

        self._username_input.setReadOnly(is_logged)
        self.api_input.setReadOnly(is_logged)

        self.btn_logout.setVisible(is_logged)

    def login_with_credentials(self, username, password):
        api_key = check_credentials(username, password)
        if api_key:
            save_credentials(api_key, False)
            self._module.set_credentials_to_env(api_key)
            self._set_credentials(api_key)
            self.login_changed.emit()
            return
        self._mark_invalid_input(self._username_input)
        self._mark_invalid_input(self.api_input)
        self._set_error(
            "We're unable to sign in to Ftrack with these credentials"
        )

    def _set_error(self, msg=None):
        self._user_message_label.setText(msg or "")

    def _unmark_input(self, input_widget):
        input_widget.setStyleSheet("")

    def _mark_invalid_input(self, input_widget):
        input_widget.setStyleSheet("border: 1px solid red;")

    def _on_login(self):
        self.set_is_logged(True)
        self._close_widget()

    def _on_login_clicked(self):
        username = self._username_input.text()
        password = self._password_input.text()
        if username == "":
            self._mark_invalid_input(self._username_input)
            self._set_error("You didn't enter Username")
            return

        self.login_with_credentials(username, password)

    def _on_logout_clicked(self):
        self._username_input.setText("")
        self.set_is_logged(False)
        self.logout_signal.emit()

    def _set_credentials(self, api_key, is_logged=True):
        # TODO maybe add widget to show the api key?
        self._set_error()

        self._unmark_input(self._server_label)
        self._unmark_input(self._username_input)
        self._unmark_input(self.api_input)

        if is_logged is not None:
            self.set_is_logged(is_logged)

    def _get_validated_url(self):
        server_url = self._module.get_aquarium_url()
        if not server_url:
            self._set_error(
                "Aquarium URL is not defined in settings!"
            )
            return None

        try:
            # Check if url can be reached
            result = requests.get(server_url)
        except requests.exceptions.RequestException:
            self._set_error(
                "Specified URL could not be reached."
            )
            return None

        # Validate if server is Aquarium server
        # TODO implement the validation
        if result.status_code != 200:
            self._set_error(
                "Specified URL does not lead to a valid Ftrack server."
            )
            return None
        return server_url

    def _update_url(self):
        validated_url = self._get_validated_url()

        self._validated_url = validated_url

        self._server_label.setText(validated_url or "< Not set >")

        self._update_widget_states()

    def _update_widget_states(self):
        # TODO finish implementation - now it is random changing of states :)
        url_is_valid = bool(self._validated_url)

        self._username_input.setVisible(not url_is_valid)
        self._password_input.setVisible(not url_is_valid)
        self._btn_login.setVisible(not url_is_valid or not self._is_logged)
        self._btn_logout.setVisible(not url_is_valid or self._is_logged)

        self._username_input.setReadOnly(self._is_logged)
        self._username_input.setEnabled(not self._is_logged)
        self._password_input.setReadOnly(self._is_logged)
        self._password_input.setEnabled(not self._is_logged)

        self._username_input.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self._password_input.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))

    def _close_widget(self):
        self.hide()
