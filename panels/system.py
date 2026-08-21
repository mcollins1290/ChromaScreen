import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return SystemPanel(*args)


ALLOWED_SERVICES = (
    "crowsnest",
    "MoonCord",
    "moonraker",
    "moonraker-telegram-bot",
    "klipper",
    "ChromaScreen",
    "sonar",
    "webcamd",
)


class SystemPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)

        reboot = self._gtk.Button('refresh', _('Restart'), 'color3')
        reboot.connect("clicked", self.reboot_poweroff, "reboot")
        reboot.set_vexpand(False)
        shutdown = self._gtk.Button('shutdown', _('Shutdown'), 'color4')
        shutdown.connect("clicked", self.reboot_poweroff, "poweroff")
        shutdown.set_vexpand(False)

        services = self.get_available_services()
        service_grid = Gtk.Grid()
        service_grid.set_row_spacing(5)
        service_grid.set_column_spacing(10)
        service_grid.set_column_homogeneous(True)
        for row, service in enumerate(services):
            label = Gtk.Label(label=service)
            label.set_halign(Gtk.Align.START)
            restart = self._gtk.Button('refresh', _('Restart'), 'color3')
            restart.connect("clicked", self.restart_service, service)
            service_grid.attach(label, 0, row, 1, 1)
            service_grid.attach(restart, 1, row, 1, 1)

        row = 0
        if services:
            scroll = self._gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll.add(service_grid)
            grid.attach(scroll, 0, row, 2, 2)
            row = 2

        grid.attach(reboot, 0, row, 1, 1)
        grid.attach(shutdown, 1, row, 1, 1)
        self.content.add(grid)

    def get_available_services(self):
        system_info = self._screen.apiclient.send_request("machine/system_info")
        if not system_info:
            return []
        available_services = system_info.get("result", {}).get("system_info", {}).get("available_services", [])
        return [service for service in ALLOWED_SERVICES if service in available_services]

    def restart_service(self, widget, service):
        self._screen._ws.send_method("machine.services.restart", {"service": service})

    def reboot_poweroff(self, widget, method):
        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)
        if method == "reboot":
            label = Gtk.Label(label=_("Are you sure you wish to reboot the system?"))
        else:
            label = Gtk.Label(label=_("Are you sure you wish to shutdown the system?"))
        vbox.add(label)
        scroll.add(vbox)
        buttons = [
            {"name": _("Host"), "response": Gtk.ResponseType.OK},
            {"name": _("Printer"), "response": Gtk.ResponseType.APPLY},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]
        dialog = self._gtk.Dialog(self._screen, buttons, scroll, self.reboot_poweroff_confirm, method)
        if method == "reboot":
            dialog.set_title(_("Restart"))
        else:
            dialog.set_title(_("Shutdown"))

    def reboot_poweroff_confirm(self, dialog, response_id, method):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.OK:
            if method == "reboot":
                os.system("systemctl reboot")
            else:
                os.system("systemctl poweroff")
        elif response_id == Gtk.ResponseType.APPLY:
            if method == "reboot":
                self._screen._ws.send_method("machine.reboot")
            else:
                self._screen._ws.send_method("machine.shutdown")
