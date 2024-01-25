from qtpy import QtCore, QtWidgets, QtGui

from openpype import resources
from openpype.lib import Logger

from .credentials import (
    get_credentials,
    check_credentials,
    clear_credentials,
)

from .login_dialog import CredentialsDialog


# NOTE this is not finished, the implementation is based on 'credentials.py'
#   and 'login_dialog.py'
class AquariumTrayWrapper:
    def __init__(self, module):
        self._log = None
        self._module = module

        self._bool_logged = False

        self._action_credentials = None

        self._widget_login = CredentialsDialog(module)
        self._widget_login.login_changed.connect(self._on_login_change)
        self._widget_login.logout_signal.connect(self._on_logout)

        self._icon_logged = QtGui.QIcon(
            resources.get_resource("icons", "circle_green.png")
        )
        self._icon_not_logged = QtGui.QIcon(
            resources.get_resource("icons", "circle_orange.png")
        )

    @property
    def log(self):
        if self._log is None:
            self._log = Logger.get_logger(self.__class__.__name__)
        return self._log

    def _show_login_widget(self):
        self._widget_login.show()
        self._widget_login.activateWindow()
        self._widget_login.raise_()

    def validate(self):
        """Validate if currently stored credentials are valid.

        Returns:
            bool: Credentials are valid or not.
        """

        cred = get_credentials()
        api_key = cred.get("api_key")

        validation = check_credentials(api_key)
        if validation:
            self._widget_login.set_credentials(api_key)
            self._module.set_credentials_to_env(api_key)
            self.log.info("Connected to Aquarium successfully")
            self._on_login_change()

            return validation

        if not validation and api_key:
            self.log.warning((
                "Current Aquarium credentials are not valid for server {}"
            ).format(self._module.get_aquarium_url()))

        self.log.info("Please sign in to Aquarium")
        self._bool_logged = False
        self._show_login_widget()

        return validation

    # Definition of Tray menu
    def tray_menu(self, parent_menu):
        # NOTE You can add more actions to the menu, like Browse, etc.

        # Menu for Tray App
        tray_menu = QtWidgets.QMenu("Aquarium", parent_menu)

        # Actions - basic
        action_credentials = QtWidgets.QAction("Credentials", tray_menu)
        action_credentials.triggered.connect(self._show_login_widget)
        if self._bool_logged:
            icon = self._icon_logged
        else:
            icon = self._icon_not_logged
        action_credentials.setIcon(icon)
        tray_menu.addAction(action_credentials)
        self._action_credentials = action_credentials

        self._bool_logged = False

        parent_menu.addMenu(tray_menu)

    def tray_exit(self):
        # Cleanup on tray exit
        pass

    # Necessary - login_dialog works with this method after logging in
    def _on_login_change(self):
        self._bool_logged = True

        if self._action_credentials:
            self._action_credentials.setIcon(self._icon_logged)
            self._action_credentials.setToolTip(
                "Logged as user \"{}\"".format(
                    self._widget_login.user_input.text()
                )
            )

    def _on_logout(self):
        clear_credentials()

        if self._action_credentials:
            self._action_credentials.setIcon(self._icon_not_logged)
            self._action_credentials.setToolTip("Logged out")

        self.log.info("Logged out of Aquarium")
        self._bool_logged = False
