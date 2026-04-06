from __future__ import annotations

from dataclasses import dataclass

from nicegui import ui

from autosubmaker.bootstrap.startup import BootstrapContext, bootstrap_application
from autosubmaker.services.queue_service import QueueService


@dataclass(slots=True)
class AppContext:
    bootstrap: BootstrapContext
    queue_service: QueueService


def create_and_run_app() -> None:
    from autosubmaker.ui.pages.main_page import MainPage

    bootstrap = bootstrap_application()
    context = AppContext(
        bootstrap=bootstrap,
        queue_service=QueueService(),
    )

    ui.colors(primary="#0f4c81", secondary="#d17b0f", accent="#1f7a4c")
    MainPage(context).build()

    ui.run(
        native=True,
        reload=False,
        title="AutoSubMaker",
    )
