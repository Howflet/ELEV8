import time

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from building import Building
from elevator import Direction
from passenger import Passenger
from simulation import Simulation


class Visualizer:
    def __init__(self, simulation):
        self.sim = simulation
        self.console = Console()

    def _get_passengers(self):
        with self.sim._id_lock:
            return list(self.sim._all_passengers.values())

    def _passenger_status(self, passenger):
        STATUS_COLORS = {
            "waiting":  "yellow",
            "boarding": "bright_green",
            "riding":   "cyan",
            "leaving":  "bright_yellow",
            "arrived":  "green",
        }
        return (passenger.status.capitalize(), STATUS_COLORS.get(passenger.status, "white"))

    def _render(self):
        building = self.sim.building
        elevators = building.elevators
        passengers = self._get_passengers()

        # --- Building grid ---
        grid = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
        grid.add_column("Floor", style="bold", width=7, justify="right")
        for elev in elevators:
            grid.add_column(f"Elev {elev.elevator_id}", width=14, justify="center")
        grid.add_column("Waiting", min_width=20)

        for floor in range(building.floors - 1, -1, -1):
            cells = []
            for elev in elevators:
                if elev.current_floor == floor:
                    arrow = {"UP": "▲", "DOWN": "▼", "IDLE": "■"}[elev.direction.name]
                    n_pax = len(elev.current_passengers)
                    cells.append(f"[bold green]{arrow} E{elev.elevator_id}[/bold green] ({n_pax})")
                elif floor in elev.destination_floor:
                    cells.append("[dim yellow]  ◦[/dim yellow]")
                else:
                    cells.append("")

            waiting = [
                p for p in passengers
                if p.status == "waiting" and p.current_floor == floor
            ]
            waiting_str = "  ".join(
                f"[yellow]P{p.passenger_id}→{p.destination_floor}[/yellow]" for p in waiting
            )

            grid.add_row(f"{floor:2d}", *cells, waiting_str)

        # --- Passenger status table ---
        pax_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
        pax_table.add_column("ID",     width=4)
        pax_table.add_column("From",   width=6, justify="center")
        pax_table.add_column("To",     width=6, justify="center")
        pax_table.add_column("Status", width=10)

        for p in passengers:
            status, color = self._passenger_status(p)
            pax_table.add_row(
                f"P{p.passenger_id}",
                str(p.current_floor),
                str(p.destination_floor),
                f"[{color}]{status}[/{color}]",
            )

        # --- Event log ---
        with self.sim._log_lock:
            log_lines = list(self.sim._log_lines[-10:])
        log_text = "\n".join(log_lines) or "[dim](no events yet)[/dim]"

        return Group(
            Panel(
                grid,
                title=f"[bold blue]{building.name}[/bold blue]  [dim]Tick {self.sim.tick_count}[/dim]",
                border_style="blue",
            ),
            Panel(pax_table, title="Passengers", border_style="cyan"),
            Panel(log_text,  title="Event Log",  border_style="dim"),
        )

    def _all_arrived(self):
        passengers = self._get_passengers()
        return len(passengers) > 0 and all(p.status in ("arrived", "leaving") for p in passengers)

    def run(self, max_ticks=None, stop_when_done=True):
        """Observe and render the simulation. The sim must already be running in a background thread."""
        with Live(self._render(), refresh_per_second=4, console=self.console) as live:
            while True:
                live.update(self._render())
                if stop_when_done and self._all_arrived():
                    self.sim.running = False
                    break
                if max_ticks and self.sim.tick_count >= max_ticks:
                    self.sim.running = False
                    break
                time.sleep(self.sim.seconds_per_floor)

        self.console.print(
            f"\n[bold green]Simulation complete — {self.sim.tick_count} ticks.[/bold green]"
        )
