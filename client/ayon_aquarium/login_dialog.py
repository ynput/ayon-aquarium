from qtpy import QtCore, QtGui, QtWidgets

from ayon_core import style, resources
from ayon_core.tools.utils import PlaceholderLineEdit

from .credentials import signin, me, load_credentials, save_credentials, clear_credentials, set_credentials_envs


class AquariumCredentialsDialog(QtWidgets.QDialog):
    SIZE_W = 400
    SIZE_H = 230

    login_changed = QtCore.Signal()
    logout_signal = QtCore.Signal()

    def __init__(self, addon, parent=None):
        super().__init__(parent)

        self.setWindowTitle("AYON - Aquarium Login")

        icon = QtGui.QIcon(resources.get_ayon_icon_filepath())
        self.setWindowIcon(icon)

        self.setWindowFlags(
            QtCore.Qt.WindowCloseButtonHint
            | QtCore.Qt.WindowMinimizeButtonHint
        )

        self._addon = addon

        self._is_logged = False
        self._validated_url = None

        # --- Inputs ---
        inputs_widget = QtWidgets.QWidget(self)

        email_label = QtWidgets.QLabel("User email:", inputs_widget)
        password_label = QtWidgets.QLabel("User password:", inputs_widget)
        server_url_label = QtWidgets.QLabel("Aquarium URL:", inputs_widget)

        server_label = QtWidgets.QLabel(inputs_widget)
        # server_url_label.setTextInteractionFlags(
        #     QtCore.Qt.TextBrowserInteraction
        # )
        # server_url_label.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))

        email_input = QtWidgets.QLineEdit(inputs_widget)
        email_input.setPlaceholderText("user.name@example.com")

        password_input = PlaceholderLineEdit(inputs_widget)
        password_input.setPlaceholderText("Your password")
        password_input.setEchoMode(PlaceholderLineEdit.Password)

        remember_checkbox = QtWidgets.QCheckBox("Remember", inputs_widget)
        remember_checkbox.setObjectName("RememberCheckbox")
        remember_checkbox.setChecked(False)

        server_url_spacer = QtWidgets.QSpacerItem(5, 5)

        inputs_layout = QtWidgets.QGridLayout(inputs_widget)
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.addWidget(server_url_label, 0, 0, QtCore.Qt.AlignRight)
        inputs_layout.addWidget(server_label, 0, 1)
        inputs_layout.addItem(server_url_spacer, 1, 0, 1, 2)
        inputs_layout.addWidget(email_label, 2, 0, QtCore.Qt.AlignRight)
        inputs_layout.addWidget(email_input, 2, 1)
        inputs_layout.addWidget(password_label, 3, 0, QtCore.Qt.AlignRight)
        inputs_layout.addWidget(password_input, 3, 1)
        inputs_layout.addWidget(remember_checkbox, 4, 1)
        inputs_layout.setColumnStretch(0, 0)
        inputs_layout.setColumnStretch(1, 1)

        # input_layout = QtWidgets.QFormLayout(inputs_widget)
        # # input_layout.setContentsMargins(10, 15, 10, 5)
        # input_layout.addRow("Aquarium URL:", server_label)
        # input_layout.addRow(email_label, email_input)
        # input_layout.addRow(password_label, password_input)
        # input_layout.addRow(None, remember_checkbox)

        # --- Error label for user ---
        messages_wrapper = QtWidgets.QWidget(self)
        user_message_label = QtWidgets.QLabel("", messages_wrapper)
        user_message_label.setWordWrap(True)
        user_message_label.setStyleSheet("color: #ff6b6b;")

        messages_layout = QtWidgets.QVBoxLayout(messages_wrapper)
        messages_layout.setContentsMargins(10, 5, 10, 5)
        messages_layout.addWidget(user_message_label)

        # --- Buttons ---
        btns_widget = QtWidgets.QWidget(self)

        btn_login = QtWidgets.QPushButton("Login", btns_widget)
        btn_login.setToolTip(
            "Signin to Aquarium with the provided credentials."
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

        self._email_input = email_input
        self._password_input = password_input
        self._remember_checkbox = remember_checkbox

        self._user_message_label = user_message_label

        self._btn_login = btn_login
        self._btn_logout = btn_logout

        token = load_credentials()
        if token:
            self._remember_checkbox.setChecked(True)
            try:
                user = me(token)
                self._email_input.setText(user.data.email)
                self._password_input.setPlaceholderText("********")
                self._is_logged = True
            except:
                self._is_logged = False

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

        self._email_input.setReadOnly(is_logged)
        self._password_input.setReadOnly(is_logged)

        self._btn_logout.setVisible(is_logged)

    def login_with_credentials(self, email, password):
        try:
            token = signin(email, password)
            if token:
                remember = self._remember_checkbox.isChecked()
                if (remember):
                    save_credentials(token)
                else:
                    clear_credentials()
                set_credentials_envs(token)
                # self._set_credentials(api_key)
                self.login_changed.emit()
                return
        except Exception as err:
            self._mark_invalid_input(self._email_input)
            self._mark_invalid_input(self._password_input)
            self._set_error(
                str(err) or "We're unable to sign in to Aquarium with these credentials"
            )


    def _set_error(self, msg=None):
        self._user_message_label.setText(msg or "")

    def _unmark_input(self, input_widget):
        input_widget.setStyleSheet("")

    def _mark_invalid_input(self, input_widget):
        input_widget.setStyleSheet("border: 1px solid #ff6b6b;")

    def _on_login(self):
        self.set_is_logged(True)
        self._close_widget()

    def _on_login_clicked(self):
        email = self._email_input.text()
        password = self._password_input.text()
        if email == "":
            self._mark_invalid_input(self._email_input)
            self._set_error("You didn't enter Email")
            return

        self.login_with_credentials(email, password)

    def _on_logout_clicked(self):
        self._email_input.setText("")
        self._password_input.setText("")
        self._password_input.setPlaceholderText("Your password")
        self.set_is_logged(False)
        self.logout_signal.emit()

    def _set_credentials(self, api_key, is_logged=True):
        # TODO maybe add widget to show the api key?
        self._set_error()

        self._unmark_input(self._server_label)
        self._unmark_input(self._email_input)
        self._unmark_input(self._password_input)

        if is_logged is not None:
            self.set_is_logged(is_logged)

    def _get_validated_url(self):
        server_url = self._addon.get_aquarium_url()
        if not server_url:
            self._set_error(
                "Aquarium URL is not defined in settings!"
            )
            return None

        # try:
        #     # Check if url can be reached
        #     result = requests.get(server_url)
        # except requests.exceptions.RequestException:
        #     self._set_error(
        #         "Specified URL could not be reached."
        #     )
        #     return None

        # # Validate if server is Aquarium server
        # # TODO implement the validation
        # if result.status_code != 200:
        #     self._set_error(
        #         "Specified URL does not lead to a valid Aquarium server."
        #     )
        #     return None
        return server_url

    def _update_url(self):
        validated_url = self._get_validated_url()

        self._validated_url = validated_url

        self._server_label.setText(validated_url or "Set server url in Studio Settings")

        self._update_widget_states()

    def _update_widget_states(self):
        url_is_valid = bool(self._validated_url)

        if not url_is_valid:
            self._server_label.setStyleSheet("color: #ff6b6b;")
        else:
            self._server_label.setStyleSheet("")

        # self._email_input.setVisible(url_is_valid)
        self._email_input.setReadOnly(not url_is_valid or self._is_logged)
        self._email_input.setEnabled(not self._is_logged)

        # self._password_input.setVisible(url_is_valid)
        self._password_input.setReadOnly(not url_is_valid or self._is_logged)
        self._password_input.setEnabled(not self._is_logged)

        self._remember_checkbox.setEnabled(url_is_valid and not self._is_logged)

        if self._is_logged:
            self._unmark_input(self._email_input)
            self._unmark_input(self._password_input)

        self._btn_login.setVisible(not self._is_logged)
        self._btn_login.setEnabled(url_is_valid)

        self._btn_logout.setVisible(self._is_logged)
        self._btn_logout.setEnabled(url_is_valid)

        self._email_input.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self._password_input.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))

    def _close_widget(self):
        self.hide()
