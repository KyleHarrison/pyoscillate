from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from ipywidgets import HTML, Checkbox, FloatSlider, HBox, VBox, interactive_output

from pyoscillate.patches.base import Patch, PatchRack
from pyoscillate.patches.presets import PresetController


@dataclass(frozen=True)
class SliderSpec:
    name: str
    minimum: float
    maximum: float
    step: float
    default: float
    description: str
    help_text: str


def patch_widget(
    rack: PatchRack,
    name: str,
    build: Callable[..., Patch],
    parameters: Sequence[SliderSpec],
    controller: PresetController | None = None,
    *,
    enabled_description: str | None = None,
    volume_default: float = 0.6,
) -> VBox:
    """Build the standard live-updating notebook controls for a patch."""
    enabled = Checkbox(
        value=False,
        description=enabled_description or f"{name} on/off",
    )
    sliders = {
        spec.name: FloatSlider(
            min=spec.minimum,
            max=spec.maximum,
            step=spec.step,
            value=spec.default,
            description=spec.name,
        )
        for spec in parameters
    }
    volume = FloatSlider(
        min=0, max=2, step=0.1, value=volume_default, description="volume"
    )
    controls = {"enabled": enabled, **sliders, "volume": volume}

    def set_params(**values: Any) -> None:
        if controller is not None and controller.applying:
            return
        if not values["enabled"]:
            rack.stop(name)
            return

        patch = rack.get(name)
        live_values = {spec.name: values[spec.name] for spec in parameters}
        if patch is None:
            patch = build(**live_values)
            rack.start(name, patch)
        else:
            patch.update(live_values)
        patch.set("volume", values["volume"])

    if controller is not None:
        controller.register(
            name,
            controls,
            lambda: set_params(
                **{
                    control_name: widget.value
                    for control_name, widget in controls.items()
                }
            ),
        )

    output = interactive_output(set_params, controls)
    rows = [HBox([sliders[spec.name], HTML(spec.help_text)]) for spec in parameters]
    rows.append(
        HBox([volume, HTML("Output level for this patch, limited so it won't clip.")])
    )
    return VBox([enabled, *rows, output])
