from __future__ import annotations

from pyo.lib._core import PyoError
from pyo.lib.server import Server

import flet as ft
from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.psyambient import soundscape_fm
from pyoscillate.patches.widgets import SliderSpec

PATCH_NAME = "soundscape_fm"
ACCENT = "#00A896"
BACKGROUND = "#101716"
PANEL = "#182220"
TEXT = "#F4F7F6"
MUTED = "#A9B8B4"


def _decimal_places(step: float) -> int:
    return max(0, len(str(step).partition(".")[2].rstrip("0")))


class SoundscapeFmApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.server: Server | None = None
        self.rack = PatchRack()
        self.patch: Patch | None = None
        self.sliders: dict[str, ft.Slider] = {}

        self.status = ft.Text("Stopped", color=MUTED, size=13)
        self.play_button = ft.Button(
            "Play",
            icon=ft.Icons.PLAY_ARROW,
            bgcolor=ACCENT,
            color="#07110F",
            on_click=self.toggle_audio,
        )

        self._configure_page()
        self._build_view()

    def _configure_page(self) -> None:
        self.page.title = "FM Soundscape"
        self.page.bgcolor = BACKGROUND
        self.page.padding = 0
        self.page.theme = ft.Theme(font_family="Avenir Next")
        self.page.window.width = 720
        self.page.window.height = 850
        self.page.window.min_width = 420
        self.page.window.min_height = 600
        self.page.on_close = self.close

    def _build_view(self) -> None:
        parameter_controls = [self._parameter_control(spec) for spec in soundscape_fm.PARAMETERS]
        volume_spec = SliderSpec(
            "volume",
            0,
            2,
            0.1,
            0.6,
            "Output level",
            "",
        )
        parameter_controls.append(self._parameter_control(volume_spec))

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                "FM SOUNDSCAPE", size=12, color=ACCENT, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "Chaotic drift", size=34, color=TEXT, weight=ft.FontWeight.BOLD
                            ),
                            self.status,
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    self.play_button,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=28,
            bgcolor="#121D1B",
        )
        controls = ft.Column(
            controls=parameter_controls,
            spacing=12,
        )
        self.page.add(
            ft.Column(
                controls=[
                    header,
                    ft.Container(content=controls, padding=28),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )

    def _parameter_control(self, spec: SliderSpec) -> ft.Container:
        precision = _decimal_places(spec.step)
        value_text = ft.Text(
            f"{spec.default:.{precision}f}",
            color=ACCENT,
            size=13,
            weight=ft.FontWeight.BOLD,
        )
        slider = ft.Slider(
            min=spec.minimum,
            max=spec.maximum,
            divisions=round((spec.maximum - spec.minimum) / spec.step),
            value=spec.default,
            active_color=ACCENT,
            inactive_color="#31403D",
            thumb_color=TEXT,
        )

        def update_parameter() -> None:
            value = float(slider.value if slider.value is not None else spec.default)
            value_text.value = f"{value:.{precision}f}"
            if self.patch is not None:
                self.patch.set(spec.name, value)
            self.page.update()

        slider.on_change = update_parameter
        self.sliders[spec.name] = slider
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(spec.description, color=TEXT, size=15),
                            value_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    slider,
                ],
                spacing=2,
            ),
            padding=16,
            bgcolor=PANEL,
            border_radius=6,
        )

    def _values(self) -> dict[str, float]:
        return {
            spec.name: float(self.sliders[spec.name].value or spec.default)
            for spec in soundscape_fm.PARAMETERS
        }

    def _set_running(self, running: bool) -> None:
        self.status.value = "Playing" if running else "Stopped"
        self.status.color = ACCENT if running else MUTED
        self.play_button.content = "Stop" if running else "Play"
        self.play_button.icon = ft.Icons.STOP if running else ft.Icons.PLAY_ARROW

    def toggle_audio(self) -> None:
        if self.patch is not None:
            self.rack.stop(PATCH_NAME)
            self.patch = None
            self._set_running(False)
            self.page.update()
            return

        try:
            if self.server is None:
                self.server = Server(nchnls=2).boot()
                self.server.start()
            patch = soundscape_fm.build(**self._values())
            patch.volume = float(self.sliders["volume"].value or 0.6)
            self.patch = self.rack.start(PATCH_NAME, patch)
            self._set_running(True)
        except (OSError, PyoError, RuntimeError) as error:
            self.patch = None
            self.status.value = f"Audio error: {error}"
            self.status.color = "#FF8A80"
        self.page.update()

    def close(self) -> None:
        self.rack.stop_all()
        self.patch = None
        if self.server is not None:
            self.server.stop()
            self.server.shutdown()
            self.server = None


def main(page: ft.Page) -> None:
    SoundscapeFmApp(page)


if __name__ == "__main__":
    ft.run(main)
