import logging
import sys

from PySide6.QtWidgets import QApplication

from house_index import __app_name__, __version__
from house_index.logging_setup import setup_logging
from house_index.paths import (
    backups_dir,
    db_path,
    logs_dir,
    migrate_legacy_data,
    photos_dir,
)
from house_index.services.backup_service import auto_backup_on_start
from house_index.services.property_service import PropertyService
from house_index.ui.main_window import LIGHT_STYLESHEET, MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Voslar")
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_STYLESHEET)

    migrate_legacy_data()

    log = logging.getLogger("house_index")
    setup_logging(logs_dir())
    log.info("%s %s starting", __app_name__, __version__)

    service = PropertyService(db_path())

    try:
        auto_backup_on_start(db_path(), photos_dir(), backups_dir())
    except Exception:
        log.exception("auto_backup_on_start failed")

    window = MainWindow(service)
    window.show()
    return app.exec()
