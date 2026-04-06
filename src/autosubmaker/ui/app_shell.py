from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nicegui import app, ui

from autosubmaker.bootstrap.startup import BootstrapContext, bootstrap_application
from autosubmaker.services.queue_service import QueueService

if TYPE_CHECKING:
    from nicegui.client import Client
    from nicegui.events import NativeEventArguments
    from autosubmaker.ui.pages.main_page import MainPage


@dataclass(slots=True)
class AppContext:
    bootstrap: BootstrapContext
    queue_service: QueueService


_ACTIVE_PAGE: "MainPage | None" = None
_NATIVE_DROP_HANDLER_REGISTERED = False


def create_and_run_app() -> None:
    from autosubmaker.ui.pages.main_page import MainPage

    global _NATIVE_DROP_HANDLER_REGISTERED

    bootstrap = bootstrap_application()
    context = AppContext(
        bootstrap=bootstrap,
        queue_service=QueueService(),
    )

    def set_active_page(page: "MainPage") -> None:
        global _ACTIVE_PAGE
        _ACTIVE_PAGE = page

    def clear_active_page(page: "MainPage") -> None:
        global _ACTIVE_PAGE
        if _ACTIVE_PAGE is page:
            _ACTIVE_PAGE = None

    def dispatch_native_drop(event: "NativeEventArguments") -> None:
        if _ACTIVE_PAGE is None:
            return
        _ACTIVE_PAGE.handle_native_drop(event)

    if not _NATIVE_DROP_HANDLER_REGISTERED:
        app.native.on("drop", dispatch_native_drop)
        _NATIVE_DROP_HANDLER_REGISTERED = True

    def build_root(client: "Client") -> None:
        ui.colors(primary="#0f4c81", secondary="#d17b0f", accent="#1f7a4c")
        page = MainPage(
            context=context,
            ui_client=client,
        )
        set_active_page(page)
        client.on_delete(lambda: clear_active_page(page))
        page.build()

    ui.run(
        root=build_root,
        native=True,
        reload=False,
        title="AutoSubMaker",
    )
