import sys
import time
import signal
import logging
import traceback

from aquarium import Aquarium
from aquarium import exceptions

from ayon_api import (
    get_secrets,
    init_service,
    get_service_addon_name,
    get_service_addon_version,
    get_service_addon_settings,
)

log = logging.getLogger(__name__)


IGNORED_AQ_TOPICS: set = {}
ALLOWED_AQ_TOPICS: set = {
    "item.created.Asset",
    "item.updated.Asset",
    "item.created.Shot",
    "item.updated.Shot",
    "item.created.Sequence",
    "item.updated.Sequence",
    "item.created.Episode",
    "item.updated.Episode",
    "item.created.Task",
    "item.updated.Task",
    # "item.created.Project", # prevents double project creation
    # "item.updated.Project",
    "user.assigned",
    "user.unassigned",
}


def get_service_label() -> str:
    return " ".join([str(get_service_addon_name()), str(get_service_addon_version())])


def connect_to_ayon():
    """Connect to AYON server."""
    try:
        init_service()
        connected = True
    except Exception:
        connected = False

    if not connected:
        print("Failed to connect to AYON server.")
        # Sleep for 10 seconds, so it is possible to see the message in
        #   docker
        # NOTE: Because AYON connection failed, there's no way how to log it
        #   to AYON server (obviously)... So stdout is all we have.
        time.sleep(10)
        sys.exit(1)

    log.info("Connected to AYON server.")


def register_signals(_AQS: "AquariumServices"):
    """Register signals to stop Aquarium services"""

    def signal_handler(sig, frame):
        print("Process stop requested. Terminating process.")
        _AQS.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


class AquariumServices:
    """
    Aquarium services for AYON.
    This class is used by leecher and processor services to limit code repetition.
    """

    bot_key: str
    aq = Aquarium()
    listener = None

    leecher = None
    processor = None

    session_fail_logged = 0
    IGNORE_TOPICS = []

    def __init__(self, level=logging.INFO):
        self.listener = None
        self.session_fail_logged = 0

        aquarium_log = logging.getLogger("aquarium")
        aquarium_log.setLevel(level)

        self.log = logging.getLogger(__name__)

    @property
    def connected(self):
        return bool(self.aq.token is not None and self.aq.token != "")

    @property
    def listenning(self):
        state = False
        if self.listener is not None:
            state = self.listener.listening
        return state

    def _connect(self):
        aquarium_settings = get_service_addon_settings()

        url = aquarium_settings["url"]
        domain = aquarium_settings["domain"]

        secrets_by_name = {secret["name"]: secret["value"] for secret in get_secrets()}

        services = aquarium_settings["services"]
        bot_key = services["bot_key"]
        bot_secret = services["bot_secret"]
        if bot_key in secrets_by_name:
            bot_key = secrets_by_name[bot_key]

        if bot_secret in secrets_by_name:
            bot_secret = secrets_by_name[bot_secret]

        if not bot_key or not bot_secret:
            return (
                "Missing Aquarium bot _key or secret in settings."
                f" Please check your settings of {get_service_label()}."
            )

        self.aq.api_url = url
        self.aq.domain = domain
        self.aq.bot(bot_key).signin(bot_secret)

        self.bot_key = bot_key

    def connect(self):
        tb_content = None
        error_summary = "Failed to initialize Aquarium connection."
        try:
            error_message = self._connect()
        except exceptions.AuthentificationError:
            error_message = (
                "Aquarium bot credential in settings are not valid."
                f" Please check your settings of {get_service_label()}."
            )
        except Exception:
            error_message = f"{error_summary} Crashed!!!"
            tb_lines = traceback.format_exception(*sys.exc_info())
            tb_content = "".join(tb_lines)

        if self.aq.token is not None and self.aq.token != "":
            return self

        if not error_message:
            error_message = error_summary
        self.log.error(error_message)
        if tb_content:
            print(tb_content)
        if (tb_content is not None and self.session_fail_logged == 2) or (
            tb_content is None and self.session_fail_logged == 1
        ):
            return

    def listen(self):
        if self.aq is None:
            return

        self.listener = self.aq.events.listen()
        while not self.listener.listening:
            time.sleep(0.1)

        return self.listener

    def stop(self):
        self.log.info("Aquarium stop requested. Terminating process.")
        if self.listener is not None and self.listenning:
            self.listener.stop()

        if self.processor:
            self.processor.stop()
        self.log.info("Termination finished.")
