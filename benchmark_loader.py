
from pathlib import Path
from dataclasses import dataclass


# Project folders
ROOT = Path(__file__).resolve().parent
MAP_FILE = ROOT / "data" / "maps" / "raw" / "warehouse-10-20-10-2-1.map"
SCENARIO_DIR = ROOT / "data" / "scenarios" / "raw"


@dataclass
class WarehouseMap:
    width: int
    height: int
    grid: list

    def is_walkable(self, x, y):
        return (
            0 <= x < self.width
            and 0 <= y < self.height
            and self.grid[y][x]
        )


@dataclass
class Scenario:
    bucket: int
    start: tuple
    goal: tuple
    optimal_distance: float


def load_map(file_path):
    """Load a Moving AI octile map."""

    with open(file_path, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    if len(lines) < 4 or lines[0] != "type octile":
        raise ValueError("Invalid or unsupported map format.")

    height = int(lines[1].split()[1])
    width = int(lines[2].split()[1])

    if lines[3] != "map":
        raise ValueError("Missing map data header.")

    map_rows = lines[4:]

    if len(map_rows) != height:
        raise ValueError(
            f"Expected {height} map rows, found {len(map_rows)}."
        )

    # Moving AI map symbols:
    # . = traversable
    # G/S = traversable
    # @/O/T/W = blocked
    walkable_symbols = {".", "G", "S"}
    blocked_symbols = {"@", "O", "T", "W"}

    grid = []

    for y, row in enumerate(map_rows):
        if len(row) != width:
            raise ValueError(
                f"Row {y} has {len(row)} cells; expected {width}."
            )

        cells = []

        for x, symbol in enumerate(row):
            if symbol in walkable_symbols:
                cells.append(True)
            elif symbol in blocked_symbols:
                cells.append(False)
            else:
                raise ValueError(
                    f"Unknown map symbol {symbol!r} at ({x}, {y})."
                )

        grid.append(cells)

    return WarehouseMap(width, height, grid)


def load_scenarios(file_path, warehouse):
    """Load and validate scenarios for the given warehouse map."""

    scenarios = []

    with open(file_path, "r", encoding="utf-8") as file:
        first_line = file.readline().strip()

        if first_line != "version 1":
            raise ValueError("Unsupported scenario file version.")

        for line_number, line in enumerate(file, start=2):
            if not line.strip():
                continue

            parts = line.split()

            if len(parts) != 9:
                raise ValueError(
                    f"Invalid scenario row at line {line_number}."
                )

            bucket = int(parts[0])
            map_name = parts[1]
            map_width = int(parts[2])
            map_height = int(parts[3])

            start_x = int(parts[4])
            start_y = int(parts[5])
            goal_x = int(parts[6])
            goal_y = int(parts[7])
            distance = float(parts[8])

            if map_name != MAP_FILE.name:
                raise ValueError(
                    f"Unexpected map name at line {line_number}: "
                    f"{map_name}"
                )

            if (map_width, map_height) != (
                warehouse.width, warehouse.height
            ):
                raise ValueError(
                    f"Scenario dimensions mismatch at line {line_number}."
                )

            start = (start_x, start_y)
            goal = (goal_x, goal_y)

            if not warehouse.is_walkable(*start):
                raise ValueError(
                    f"Invalid or blocked start {start} "
                    f"at line {line_number}."
                )

            if not warehouse.is_walkable(*goal):
                raise ValueError(
                    f"Invalid or blocked goal {goal} "
                    f"at line {line_number}."
                )

            scenarios.append(
                Scenario(bucket, start, goal, distance)
            )

    return scenarios


def main():
    print("Loading warehouse benchmark...")

    warehouse = load_map(MAP_FILE)

    walkable_count = sum(
        sum(row) for row in warehouse.grid
    )

    blocked_count = (
        warehouse.width * warehouse.height - walkable_count
    )

    print("\nMAP LOADED SUCCESSFULLY")
    print(f"Dimensions: {warehouse.width} x {warehouse.height}")
    print(f"Walkable cells: {walkable_count}")
    print(f"Blocked cells: {blocked_count}")

    scenario_file = (
        SCENARIO_DIR / "warehouse-10-20-10-2-1-random-1.scen"
    )

    scenarios = load_scenarios(scenario_file, warehouse)

    print("\nSCENARIOS LOADED SUCCESSFULLY")
    print(f"Scenario file: {scenario_file.name}")
    print(f"Total scenarios: {len(scenarios)}")

    print("\nFirst 5 scenarios:")

    for index, scenario in enumerate(scenarios[:5], start=1):
        print(
            f"{index}. Start={scenario.start}, "
            f"Goal={scenario.goal}, "
            f"Optimal distance={scenario.optimal_distance}"
        )


if __name__ == "__main__":
    main()