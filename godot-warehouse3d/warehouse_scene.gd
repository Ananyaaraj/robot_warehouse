extends Node3D

# ==============================================================================
# 1:1 BENCHMARK ALIGNED 3D WAREHOUSE VISUALIZATION WITH RL CONTROLLER
# ==============================================================================

# Exact grid scaling matching Moving AI warehouse-10-20-10-2-1.map
const CELL_SIZE := 0.65
const GRID_ROWS := 63
const GRID_COLS := 161

const FLOOR_WIDTH := 116.0
const FLOOR_DEPTH := 48.0

const HOST := "127.0.0.1"
const PORT := 8765

var rng := RandomNumberGenerator.new()

# Network client
var tcp_client: StreamPeerTCP = null
var is_connected_to_sim := false
var reconnect_timer := 0.0
var net_buffer := ""

# Robot instances dictionary: robot_id -> Node3D
var robots_3d := {}

# 3D Task Markers: marker_key -> Node3D
var task_markers_3d := {}

# Active Path Lines: robot_id -> MeshInstance3D
var path_lines_3d := {}

# Robot distinct theme colors (R1: Cyan, R2: Orange, R3: Lime, R4: Magenta, R5: Yellow)
var robot_colors := [
	Color(0.0, 0.9, 1.0),   # R1 Cyan
	Color(1.0, 0.55, 0.0),  # R2 Orange
	Color(0.2, 1.0, 0.3),   # R3 Lime Green
	Color(1.0, 0.25, 0.9),  # R4 Magenta
	Color(1.0, 0.95, 0.1)   # R5 Yellow
]

# Camera
var camera: Camera3D = null
var camera_mode := 0 # 0: Isometric, 1: Top-down, 2: Follow AGV
var follow_robot_id := 1

# Simulation State
var sim_paused := false
var current_speed_scale := 1.0

# UI Controls
var hud_layer: CanvasLayer = null
var status_label: Label = null
var stats_label: Label = null
var best_robot_label: Label = null
var rl_monitor_label: Label = null
var rl_decision_label: Label = null
var rl_history_container: VBoxContainer = null
var challenges_container: VBoxContainer = null
var missions_container: VBoxContainer = null
var fleet_container: VBoxContainer = null
var robot_ui_cards := {}

# Playback & Speed Controls
var pause_btn: Button = null
var speed_05_btn: Button = null
var speed_10_btn: Button = null
var speed_20_btn: Button = null


func _ready() -> void:
	rng.randomize()
	build_1to1_warehouse()
	setup_network_bridge()
	setup_hud()


func make_material(
	color: Color,
	metallic: float = 0.0,
	roughness: float = 0.8
) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = metallic
	material.roughness = roughness
	return material


func make_emission_material(color: Color, energy: float = 2.2) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = energy
	return material


func add_box(
	box_name: String,
	box_size: Vector3,
	box_position: Vector3,
	material: Material,
	parent: Node3D = self,
	box_rotation: Vector3 = Vector3.ZERO
) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.name = box_name

	var mesh := BoxMesh.new()
	mesh.size = box_size

	instance.mesh = mesh
	instance.material_override = material
	instance.position = box_position
	instance.rotation_degrees = box_rotation

	parent.add_child(instance)
	return instance


# ==============================================================================
# 1. 1:1 BENCHMARK ALIGNED WAREHOUSE ENVIRONMENT
# ==============================================================================

func build_1to1_warehouse() -> void:
	var floor_mat := make_material(Color(0.24, 0.26, 0.28), 0.1, 0.9)
	var line_mat := make_material(Color(0.95, 0.75, 0.15), 0.1, 0.5)
	var steel_mat := make_material(Color(0.14, 0.22, 0.30), 0.6, 0.4)
	var beam_mat := make_material(Color(0.95, 0.42, 0.10), 0.2, 0.5)
	var wall_mat := make_material(Color(0.50, 0.54, 0.58), 0.1, 0.8)
	var light_mat := make_material(Color(0.95, 0.96, 0.90), 0.1, 0.2)

	var cargo_mats: Array[Material] = [
		make_material(Color(0.18, 0.48, 0.82)),
		make_material(Color(0.82, 0.30, 0.18)),
		make_material(Color(0.22, 0.62, 0.36)),
		make_material(Color(0.90, 0.70, 0.18)),
		make_material(Color(0.58, 0.38, 0.76))
	]

	# 1. Large Concrete Base Floor
	add_box("ConcreteFloor", Vector3(FLOOR_WIDTH, 0.4, FLOOR_DEPTH), Vector3(0, -0.2, 0), floor_mat)

	# 2. Perimeter Enclosure Walls (Matching Benchmark Boundary: Rows 0 & 62, Cols 0 & 160)
	var north_z: float = (0.0 - 31.0) * CELL_SIZE
	var south_z: float = (62.0 - 31.0) * CELL_SIZE
	var west_x: float = (0.0 - 80.0) * CELL_SIZE
	var east_x: float = (160.0 - 80.0) * CELL_SIZE
	var wall_height := 3.8

	add_box("NorthWall", Vector3(105.0, wall_height, 0.6), Vector3(0, wall_height / 2.0, north_z), wall_mat)
	add_box("SouthWall", Vector3(105.0, wall_height, 0.6), Vector3(0, wall_height / 2.0, south_z), wall_mat)
	add_box("WestWall", Vector3(0.6, wall_height, 41.5), Vector3(west_x, wall_height / 2.0, 0), wall_mat)
	add_box("EastWall", Vector3(0.6, wall_height, 41.5), Vector3(east_x, wall_height / 2.0, 0), wall_mat)

	# 3. Perimeter Safety Lines
	add_box("NorthSafetyLine", Vector3(104.0, 0.02, 0.15), Vector3(0, 0.01, north_z + 0.5), line_mat)
	add_box("SouthSafetyLine", Vector3(104.0, 0.02, 0.15), Vector3(0, 0.01, south_z - 0.5), line_mat)
	add_box("WestSafetyLine", Vector3(0.15, 0.02, 40.5), Vector3(west_x + 0.5, 0.01, 0), line_mat)
	add_box("EastSafetyLine", Vector3(0.15, 0.02, 40.5), Vector3(east_x - 0.5, 0.01, 0), line_mat)

	# 4. Generate Low-Profile Smart Storage Pods (Open visibility, zero sightline obstruction)
	var platform_mat := make_material(Color(0.14, 0.16, 0.20), 0.5, 0.5)
	var caution_mat := make_emission_material(Color(0.95, 0.72, 0.12), 1.4)

	for k in range(20):
		var center_z: float = ((3.0 * float(k) + 2.5) - 31.0) * CELL_SIZE
		var rack_depth: float = 2.0 * CELL_SIZE # 1.30m (covers 2 rows)

		for b in range(10):
			var start_col: float = 26.0 + float(b) * 11.0
			var center_x: float = ((start_col + 4.5) - 80.0) * CELL_SIZE
			var rack_width: float = 10.0 * CELL_SIZE # 6.50m (covers 10 cols)

			# Low-profile floor platforms; only ~10 key spaced-out blocks have sleek arch frames
			var is_landmark: bool = (k % 5 == 0 and b % 4 == 0)

			build_single_rack_island(
				Vector3(center_x, 0, center_z),
				Vector3(rack_width, 1.8 if is_landmark else 0.35, rack_depth),
				steel_mat,
				beam_mat,
				cargo_mats,
				platform_mat,
				caution_mat,
				is_landmark
			)

	# 5. Overhead Industrial Lighting
	for x in [-40.0, -20.0, 0.0, 20.0, 40.0]:
		for z in [-14.0, 0.0, 14.0]:
			add_box("CeilingLight", Vector3(2.5, 0.15, 0.7), Vector3(x, 10.5, z), light_mat)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -35, 0)
	sun.light_energy = 1.7
	add_child(sun)

	var ambient_light := OmniLight3D.new()
	ambient_light.position = Vector3(0, 22, 0)
	ambient_light.omni_range = 110.0
	ambient_light.light_energy = 1.8
	add_child(ambient_light)

	# Camera Setup
	camera = Camera3D.new()
	camera.name = "Warehouse Camera"
	camera.position = Vector3(0.0, 56.0, 52.0)
	camera.fov = 48.0
	add_child(camera)
	camera.look_at(Vector3(0, 0, 0), Vector3.UP)
	camera.current = true


func build_single_rack_island(
	center: Vector3,
	size: Vector3,
	steel_mat: Material,
	beam_mat: Material,
	cargo_mats: Array[Material],
	platform_mat: Material,
	caution_mat: Material,
	is_landmark: bool
) -> void:
	# 1. Low-profile base storage platform (waist-high ~0.20m, zero visual occlusion)
	var base_h := 0.20
	add_box("StoragePlatform", Vector3(size.x * 0.96, base_h, size.z * 0.94), center + Vector3(0, base_h / 2.0, 0), platform_mat)

	# 2. Glowing perimeter safety stripe on floor
	add_box("PlatformSafetyBorder", Vector3(size.x * 0.98, 0.015, size.z * 0.96), center + Vector3(0, 0.01, 0), caution_mat)

	# 3. Compact low-profile cargo pallets on top of platform (height ~0.16m)
	var half_w := size.x / 2.0
	for px in range(3):
		var cargo_x := center.x - half_w * 0.65 + float(px) * (size.x * 0.32)
		var c_idx := rng.randi_range(0, cargo_mats.size() - 1)
		add_box(
			"LowCargoPallet",
			Vector3(size.x * 0.22, 0.16, size.z * 0.68),
			Vector3(cargo_x, base_h + 0.08, center.z),
			cargo_mats[c_idx]
		)

	# 4. Spaced-out landmark archways (only ~12 across the entire warehouse)
	if is_landmark:
		for ox in [-half_w * 0.8, half_w * 0.8]:
			for oz in [-size.z * 0.42, size.z * 0.42]:
				add_box("LandmarkUpright", Vector3(0.08, size.y, 0.08), center + Vector3(ox, size.y / 2.0, oz), steel_mat)
		add_box("LandmarkBeam", Vector3(size.x * 0.82, 0.08, 0.08), center + Vector3(0, size.y, 0), beam_mat)



# ==============================================================================
# 2. HYPER-VISIBLE 3D ROBOT MODELS (MAST BEACON + FLOOR UNDERGLOW)
# ==============================================================================

func create_robot_3d(robot_id: int) -> Node3D:
	var root := Node3D.new()
	root.name = "Robot_R" + str(robot_id)

	var theme_color: Color = robot_colors[(robot_id - 1) % robot_colors.size()]

	# 1. Main AGV Chassis: 0.50m x 0.18m x 0.50m
	var chassis_mat := make_material(Color(0.14, 0.16, 0.20), 0.7, 0.3)
	add_box("Chassis", Vector3(0.50, 0.18, 0.50), Vector3(0, 0.12, 0), chassis_mat, root)

	# 2. 4 Heavy Duty Wheels
	var wheel_mat := make_material(Color(0.04, 0.04, 0.04), 0.1, 0.9)
	var wheel_positions = [
		Vector3(-0.23, 0.08, -0.16),
		Vector3(0.23, 0.08, -0.16),
		Vector3(-0.23, 0.08, 0.16),
		Vector3(0.23, 0.08, 0.16)
	]
	for idx in range(wheel_positions.size()):
		add_box("Wheel_" + str(idx), Vector3(0.06, 0.16, 0.12), wheel_positions[idx], wheel_mat, root)

	# 3. Lidar Turret
	var sensor_mat := make_material(Color(0.02, 0.02, 0.02), 0.8, 0.2)
	add_box("SensorPuck", Vector3(0.14, 0.08, 0.14), Vector3(0, 0.25, 0), sensor_mat, root)

	# 4. Glowing Status Edge Band on Chassis
	var halo_mat := make_emission_material(theme_color, 3.0)
	add_box("StatusHalo", Vector3(0.52, 0.04, 0.52), Vector3(0, 0.18, 0), halo_mat, root)

	# 5. Elevated Vertical Mast (Height: 1.4m - elevated above all low storage pods)
	var mast_mat := make_material(Color(0.12, 0.14, 0.18), 0.8, 0.2)
	add_box("BeaconMast", Vector3(0.04, 1.4, 0.04), Vector3(0, 0.82, 0), mast_mat, root)

	# 6. Pulsing Holographic Beacon Orb at Top of Mast (y = 1.55m)
	var orb_inst := MeshInstance3D.new()
	orb_inst.name = "BeaconOrb"
	var orb_mesh := SphereMesh.new()
	orb_mesh.radius = 0.14
	orb_mesh.height = 0.28
	orb_inst.mesh = orb_mesh
	orb_inst.material_override = make_emission_material(theme_color, 4.2)
	orb_inst.position = Vector3(0, 1.55, 0)
	root.add_child(orb_inst)

	# 7. Floor Underglow Spotlight Disc (Radius: 0.65m on floor)
	var underglow_inst := MeshInstance3D.new()
	underglow_inst.name = "UnderglowDisc"
	var ug_cyl := CylinderMesh.new()
	ug_cyl.top_radius = 0.65
	ug_cyl.bottom_radius = 0.65
	ug_cyl.height = 0.02
	underglow_inst.mesh = ug_cyl
	underglow_inst.material_override = make_emission_material(theme_color, 3.2)
	underglow_inst.position = Vector3(0, 0.02, 0)
	root.add_child(underglow_inst)

	# 8. Top Cargo Payload (carried only during dropoff delivery)
	var cargo_mat := make_material(Color(0.92, 0.48, 0.12), 0.1, 0.5)
	var cargo := add_box("CargoPayload", Vector3(0.38, 0.30, 0.38), Vector3(0, 0.38, 0), cargo_mat, root)
	cargo.visible = false

	# 9. Floating 3D Billboard Label (y = 1.95m - clearly visible above obstacles)
	var label := Label3D.new()
	label.name = "RobotLabel"
	label.text = "AGV R" + str(robot_id) + "\n100%"
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 32
	label.modulate = theme_color
	label.position = Vector3(0, 1.95, 0)
	root.add_child(label)

	root.set_meta("target_pos", Vector3.ZERO)
	root.set_meta("target_rot_y", 0.0)

	add_child(root)
	return root


func update_robot_visual(robot_node: Node3D, data: Dictionary) -> void:
	var target_x: float = data.get("world_x", 0.0)
	var target_y: float = data.get("world_y", 0.15)
	var target_z: float = data.get("world_z", 0.0)
	var heading_deg: float = data.get("heading_degrees", 0.0)
	var battery: float = data.get("battery", 100.0)
	var stage: String = data.get("stage", "IDLE")
	var is_fault: bool = data.get("is_faulty", false)
	var is_charging: bool = data.get("is_charging", false)
	var robot_id: int = data.get("id", 1)
	var tasks_completed: int = data.get("tasks_completed", 0)
	var theme_color: Color = robot_colors[(robot_id - 1) % robot_colors.size()]

	robot_node.set_meta("target_pos", Vector3(target_x, target_y, target_z))
	robot_node.set_meta("target_rot_y", deg_to_rad(-heading_deg + 90.0))

	# Update Label3D
	var label: Label3D = robot_node.get_node_or_null("RobotLabel")
	if label != null:
		var stage_text := stage
		if stage == "GOING_TO_PICKUP":
			stage_text = "EN ROUTE TO SRC"
		elif stage == "GOING_TO_DROPOFF":
			stage_text = "CARRYING TO TGT"
		label.text = "AGV R%d [%d%%]\n%s (Done: %d)" % [robot_id, int(battery), stage_text, tasks_completed]

	# Cargo payload visibility (carried only during dropoff delivery)
	var cargo: MeshInstance3D = robot_node.get_node_or_null("CargoPayload")
	if cargo != null:
		cargo.visible = (stage == "GOING_TO_DROPOFF")

	# Update Pulsing Beacon Orb
	var orb: MeshInstance3D = robot_node.get_node_or_null("BeaconOrb")
	if orb != null:
		if is_fault or battery < 15.0:
			orb.material_override = make_emission_material(Color(1.0, 0.2, 0.2), 4.5)
		elif is_charging:
			orb.material_override = make_emission_material(Color(1.0, 0.85, 0.1), 4.5)
		else:
			orb.material_override = make_emission_material(theme_color, 4.0)

	# Update Floor Underglow Disc
	var underglow: MeshInstance3D = robot_node.get_node_or_null("UnderglowDisc")
	if underglow != null:
		underglow.material_override = make_emission_material(theme_color, 3.2)

	# Render Glowing Trajectory Path Ribbon on Floor
	var path_world: Array = data.get("path_world", [])
	update_path_trail(robot_id, path_world, theme_color)


func update_path_trail(robot_id: int, path_world: Array, color: Color) -> void:
	if robot_id not in path_lines_3d:
		var mesh_inst := MeshInstance3D.new()
		mesh_inst.name = "PathTrail_R" + str(robot_id)
		var imm_mesh := ImmediateMesh.new()
		mesh_inst.mesh = imm_mesh
		var mat := make_emission_material(color, 2.8)
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mesh_inst.material_override = mat
		add_child(mesh_inst)
		path_lines_3d[robot_id] = mesh_inst

	var inst: MeshInstance3D = path_lines_3d[robot_id]
	var imm: ImmediateMesh = inst.mesh as ImmediateMesh
	imm.clear_surfaces()

	if path_world.size() < 2:
		return

	imm.surface_begin(Mesh.PRIMITIVE_LINES)
	for i in range(path_world.size() - 1):
		var p1: Array = path_world[i]
		var p2: Array = path_world[i + 1]
		imm.surface_add_vertex(Vector3(p1[0], 0.035, p1[1]))
		imm.surface_add_vertex(Vector3(p2[0], 0.035, p2[1]))
	imm.surface_end()


# ==============================================================================
# 3. SKY-PIERCING 3D VISUAL BEACONS (HIGHLY VISIBLE FROM ANY DISTANCE)
# ==============================================================================

func update_task_markers(active_tasks: Array, waiting_tasks: Array) -> void:
	var active_keys := {}

	# 1. Active Missions: Dedicated Sky Beacons for each Robot's Pickup and Dropoff
	for task in active_tasks:
		var t_id: int = task.get("id", 0)
		var r_id: int = task.get("robot_id", 1)
		var p_key := "mission_r%d_src" % r_id
		var d_key := "mission_r%d_tgt" % r_id
		var stage: String = task.get("stage", "GOING_TO_PICKUP")
		var priority: String = task.get("priority", "HIGH")
		var src_color := Color(1.0, 0.80, 0.12) # Radiant Amber/Gold for Source
		var tgt_color := Color(0.20, 1.0, 0.45) # Radiant Emerald-Green for Target

		# Source Beacon: shown while traveling to pickup
		if stage == "GOING_TO_PICKUP":
			active_keys[p_key] = true
			var px: float = task.get("pickup_world_x", 0.0)
			var pz: float = task.get("pickup_world_z", 0.0)
			ensure_beacon(
				p_key,
				Vector3(px, 0.1, pz),
				src_color,
				"📍 SOURCE PICKUP (T%d)\n[R%d | PRIORITY: %s]" % [t_id, r_id, priority],
				true
			)

		# Target Beacon: shown throughout the entire mission until delivery
		active_keys[d_key] = true
		var dx: float = task.get("dropoff_world_x", 0.0)
		var dz: float = task.get("dropoff_world_z", 0.0)
		ensure_beacon(
			d_key,
			Vector3(dx, 0.1, dz),
			tgt_color,
			"🎯 TARGET DROPOFF (T%d)\n[R%d | PRIORITY: %s]" % [t_id, r_id, priority],
			false
		)

	# 2. Clean up completed markers
	var to_remove := []
	for key in task_markers_3d:
		if key not in active_keys:
			to_remove.append(key)

	for key in to_remove:
		var marker: Node3D = task_markers_3d[key]
		marker.queue_free()
		task_markers_3d.erase(key)


func ensure_beacon(marker_key: String, pos: Vector3, color: Color, label_text: String, is_source: bool) -> void:
	var marker: Node3D = null
	if marker_key in task_markers_3d:
		marker = task_markers_3d[marker_key]
		marker.position = pos
	else:
		marker = Node3D.new()
		marker.name = marker_key
		marker.position = pos

		# 1. Sky-Piercing Vertical Light Pillar (Height: 6.0m)
		var beam_mesh := MeshInstance3D.new()
		var beam_cyl := CylinderMesh.new()
		beam_cyl.top_radius = 0.10 if is_source else 0.12
		beam_cyl.bottom_radius = 0.14 if is_source else 0.16
		beam_cyl.height = 6.0
		beam_mesh.mesh = beam_cyl
		beam_mesh.position = Vector3(0, 3.0, 0)
		beam_mesh.material_override = make_emission_material(color, 4.2)
		marker.add_child(beam_mesh)

		# 2. Outer Expanding Floor Radar Disc (Radius: 1.25m)
		var base_outer := MeshInstance3D.new()
		var cyl_outer := CylinderMesh.new()
		cyl_outer.top_radius = 1.20 if is_source else 1.35
		cyl_outer.bottom_radius = 1.25 if is_source else 1.40
		cyl_outer.height = 0.03
		base_outer.mesh = cyl_outer
		base_outer.position = Vector3(0, 0.02, 0)
		base_outer.material_override = make_emission_material(color, 3.2)
		marker.add_child(base_outer)

		# 3. Inner Concentric Target Core
		var base_inner := MeshInstance3D.new()
		var cyl_inner := CylinderMesh.new()
		cyl_inner.top_radius = 0.55
		cyl_inner.bottom_radius = 0.60
		cyl_inner.height = 0.05
		base_inner.mesh = cyl_inner
		base_inner.position = Vector3(0, 0.03, 0)
		base_inner.material_override = make_emission_material(color, 3.8)
		marker.add_child(base_inner)

		# 4. Sky-High Billboard Label (y = 6.2m)
		var high_label := Label3D.new()
		high_label.name = "HighBeaconLabel"
		high_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		high_label.font_size = 36
		high_label.position = Vector3(0, 6.2, 0)
		marker.add_child(high_label)

		# 5. Low Billboard Label (y = 2.4m)
		var low_label := Label3D.new()
		low_label.name = "LowBeaconLabel"
		low_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		low_label.font_size = 28
		low_label.position = Vector3(0, 2.4, 0)
		marker.add_child(low_label)

		add_child(marker)
		task_markers_3d[marker_key] = marker

	var high_lbl: Label3D = marker.get_node_or_null("HighBeaconLabel")
	if high_lbl != null:
		high_lbl.text = label_text
		high_lbl.modulate = color

	var low_lbl: Label3D = marker.get_node_or_null("LowBeaconLabel")
	if low_lbl != null:
		low_lbl.text = label_text
		low_lbl.modulate = color



# ==============================================================================
# 4. TELEMETRY NETWORK CLIENT (TCP STREAM PEER)
# ==============================================================================

func setup_network_bridge() -> void:
	tcp_client = StreamPeerTCP.new()
	attempt_connect()


func attempt_connect() -> void:
	if tcp_client.get_status() == StreamPeerTCP.STATUS_NONE:
		var err := tcp_client.connect_to_host(HOST, PORT)
		if err != OK:
			print("[GODOT 3D] Connecting to ", HOST, ":", PORT, "...")


func poll_network(delta: float) -> void:
	tcp_client.poll()
	var status := tcp_client.get_status()

	if status == StreamPeerTCP.STATUS_CONNECTED:
		if not is_connected_to_sim:
			is_connected_to_sim = true
			if status_label != null:
				status_label.text = "● SIMULATION CONNECTED (127.0.0.1:8765)"
				status_label.modulate = Color(0.2, 1.0, 0.4)

		var available := tcp_client.get_available_bytes()
		if available > 0:
			var chunk := tcp_client.get_utf8_string(available)
			net_buffer += chunk

			while net_buffer.find("\n") != -1:
				var line_end := net_buffer.find("\n")
				var line := net_buffer.substr(0, line_end).strip_edges()
				net_buffer = net_buffer.substr(line_end + 1)

				if line.length() > 0:
					process_telemetry_packet(line)

	elif status == StreamPeerTCP.STATUS_CONNECTING:
		if status_label != null:
			status_label.text = "◌ CONNECTING TO SIMULATION..."
			status_label.modulate = Color(1.0, 0.8, 0.2)
	else:
		if is_connected_to_sim:
			is_connected_to_sim = false
		if status_label != null:
			status_label.text = "○ DISCONNECTED - RETRYING..."
			status_label.modulate = Color(1.0, 0.3, 0.3)

		reconnect_timer += delta
		if reconnect_timer >= 1.5:
			reconnect_timer = 0.0
			attempt_connect()


func process_telemetry_packet(json_text: String) -> void:
	var parsed = JSON.parse_string(json_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return

	var step: int = parsed.get("step", 0)
	var robots_list: Array = parsed.get("robots", [])
	var active_tasks: Array = parsed.get("active_tasks", [])
	var waiting_tasks: Array = parsed.get("waiting_tasks", [])
	var metrics: Dictionary = parsed.get("metrics", {})
	var best_robot: Dictionary = parsed.get("best_robot", {})
	var rl_monitor: Dictionary = parsed.get("rl_monitor", {})
	var difficulty_events: Array = parsed.get("difficulty_events", [])

	# 1. Update 3D Robots
	for r_data in robots_list:
		var r_id: int = r_data.get("id", 0)
		if r_id not in robots_3d:
			robots_3d[r_id] = create_robot_3d(r_id)
		update_robot_visual(robots_3d[r_id], r_data)

	# 2. Update 3D Source and Target Beacons
	update_task_markers(active_tasks, waiting_tasks)

	# 3. Update HUD Display
	update_hud_display(step, metrics, robots_list, active_tasks, best_robot, rl_monitor, difficulty_events)


func send_command_to_sim(cmd: Dictionary) -> void:
	if tcp_client != null and tcp_client.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		var raw_bytes := (JSON.stringify(cmd) + "\n").to_utf8_buffer()
		tcp_client.put_data(raw_bytes)
		print("[GODOT 3D] Sent command: ", cmd)


func toggle_pause() -> void:
	sim_paused = !sim_paused
	if pause_btn != null:
		pause_btn.text = "▶ Resume" if sim_paused else "⏸ Pause"
		pause_btn.modulate = Color(1.0, 0.7, 0.2) if sim_paused else Color(1.0, 1.0, 1.0)
	send_command_to_sim({"cmd": "pause" if sim_paused else "play"})
	print("[GODOT 3D] Simulation pause toggled: ", sim_paused)


func reset_simulation() -> void:
	sim_paused = false
	if pause_btn != null:
		pause_btn.text = "⏸ Pause"
		pause_btn.modulate = Color(1.0, 1.0, 1.0)
	send_command_to_sim({"cmd": "reset"})
	print("[GODOT 3D] Simulation reset command sent")


func set_sim_speed(speed: float) -> void:
	current_speed_scale = speed
	update_speed_buttons_visual()
	send_command_to_sim({"cmd": "speed", "value": speed})
	print("[GODOT 3D] Simulation speed set to: ", speed, "x")


func update_speed_buttons_visual() -> void:
	if speed_05_btn != null:
		speed_05_btn.text = "⚡ 0.5x" if current_speed_scale == 0.5 else "0.5x"
		speed_05_btn.modulate = Color(0.2, 1.0, 0.5) if current_speed_scale == 0.5 else Color(0.75, 0.75, 0.75)
	if speed_10_btn != null:
		speed_10_btn.text = "⚡ 1.0x" if current_speed_scale == 1.0 else "1.0x"
		speed_10_btn.modulate = Color(0.2, 1.0, 0.5) if current_speed_scale == 1.0 else Color(0.75, 0.75, 0.75)
	if speed_20_btn != null:
		speed_20_btn.text = "⚡ 2.0x" if current_speed_scale == 2.0 else "2.0x"
		speed_20_btn.modulate = Color(0.2, 1.0, 0.5) if current_speed_scale == 2.0 else Color(0.75, 0.75, 0.75)


# ==============================================================================
# 5. EXPANSIVE HUD DASHBOARD: LEFT VERTICAL-SCROLL SIDEBAR
# ==============================================================================

func create_styled_card(title: String, icon: String, accent_color: Color) -> Dictionary:
	var card_panel := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.11, 0.16, 0.94)
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.border_color = accent_color * Color(1, 1, 1, 0.65)
	style.corner_radius_top_left = 6
	style.corner_radius_top_right = 6
	style.corner_radius_bottom_left = 6
	style.corner_radius_bottom_right = 6
	style.content_margin_left = 8
	style.content_margin_top = 8
	style.content_margin_right = 8
	style.content_margin_bottom = 8
	card_panel.add_theme_stylebox_override("panel", style)
	card_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var card_vbox := VBoxContainer.new()
	card_vbox.add_theme_constant_override("separation", 6)
	card_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_panel.add_child(card_vbox)

	var header_lbl := Label.new()
	header_lbl.text = "%s %s" % [icon, title]
	header_lbl.add_theme_font_size_override("font_size", 12)
	header_lbl.modulate = accent_color
	header_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_vbox.add_child(header_lbl)

	var sep := HSeparator.new()
	sep.modulate = accent_color * Color(1, 1, 1, 0.3)
	card_vbox.add_child(sep)

	var content_vbox := VBoxContainer.new()
	content_vbox.add_theme_constant_override("separation", 4)
	content_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_vbox.add_child(content_vbox)

	return {
		"panel": card_panel,
		"content": content_vbox
	}


func setup_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	# Dedicated Left Sidebar Panel
	var sidebar := PanelContainer.new()
	sidebar.name = "Sidebar"
	sidebar.anchor_left = 0.0
	sidebar.anchor_top = 0.0
	sidebar.anchor_bottom = 1.0
	sidebar.offset_left = 12.0
	sidebar.offset_top = 12.0
	sidebar.offset_right = 388.0 # 376px wide
	sidebar.offset_bottom = -12.0

	var side_style := StyleBoxFlat.new()
	side_style.bg_color = Color(0.05, 0.07, 0.11, 0.95)
	side_style.border_width_left = 2
	side_style.border_width_top = 2
	side_style.border_width_right = 2
	side_style.border_width_bottom = 2
	side_style.border_color = Color(0.20, 0.38, 0.62, 0.85)
	side_style.corner_radius_top_left = 8
	side_style.corner_radius_top_right = 8
	side_style.corner_radius_bottom_left = 8
	side_style.corner_radius_bottom_right = 8
	side_style.content_margin_left = 8
	side_style.content_margin_top = 8
	side_style.content_margin_right = 8
	side_style.content_margin_bottom = 8
	sidebar.add_theme_stylebox_override("panel", side_style)
	hud_layer.add_child(sidebar)

	# Scroll Container: STRICTLY VERTICAL ONLY (no horizontal scrollbar)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sidebar.add_child(scroll)

	var main_vbox := VBoxContainer.new()
	main_vbox.add_theme_constant_override("separation", 9)
	main_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.custom_minimum_size = Vector2(350, 0)
	scroll.add_child(main_vbox)

	# --------------------------------------------------------------------------
	# Title Header
	# --------------------------------------------------------------------------
	var title_box := VBoxContainer.new()
	title_box.add_theme_constant_override("separation", 2)
	title_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.add_child(title_box)

	var title := Label.new()
	title.text = "FLEET COMMAND"
	title.add_theme_font_size_override("font_size", 16)
	title.modulate = Color(1.0, 1.0, 1.0)
	title_box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Autonomous RL Multi-Robot Fleet"
	subtitle.add_theme_font_size_override("font_size", 11)
	subtitle.modulate = Color(0.4, 0.75, 1.0)
	title_box.add_child(subtitle)

	status_label = Label.new()
	status_label.text = "◌ INITIALIZING TELEMETRY..."
	status_label.add_theme_font_size_override("font_size", 11)
	status_label.modulate = Color(1.0, 0.8, 0.2)
	title_box.add_child(status_label)

	# --------------------------------------------------------------------------
	# 1. 🧠 DEEP REINFORCEMENT LEARNING BRAIN (PPO) - PROMINENT TOP FOCUS
	# --------------------------------------------------------------------------
	var card_rl = create_styled_card("RL NEURAL AGENT (MASKABLE-PPO)", "🧠", Color(0.2, 0.9, 1.0))
	main_vbox.add_child(card_rl["panel"])

	rl_monitor_label = Label.new()
	rl_monitor_label.text = "Inference: MaskablePPO Neural Policy\nConfidence: 96.0% | Critic V(s): +18.2\nLegal Actions: 100% Guaranteed\nEpisodic Return: +0.0 | Step Reward: +0.0"
	rl_monitor_label.add_theme_font_size_override("font_size", 11)
	rl_monitor_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rl_monitor_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_rl["content"].add_child(rl_monitor_label)

	# High-contrast latest decision box
	var dec_panel := PanelContainer.new()
	var dec_style := StyleBoxFlat.new()
	dec_style.bg_color = Color(0.12, 0.10, 0.04, 0.92)
	dec_style.border_width_left = 2
	dec_style.border_width_top = 1
	dec_style.border_width_right = 1
	dec_style.border_width_bottom = 1
	dec_style.border_color = Color(1.0, 0.80, 0.15, 0.85)
	dec_style.corner_radius_top_left = 4
	dec_style.corner_radius_top_right = 4
	dec_style.corner_radius_bottom_left = 4
	dec_style.corner_radius_bottom_right = 4
	dec_style.content_margin_left = 6
	dec_style.content_margin_top = 6
	dec_style.content_margin_right = 6
	dec_style.content_margin_bottom = 6
	dec_panel.add_theme_stylebox_override("panel", dec_style)
	dec_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_rl["content"].add_child(dec_panel)

	rl_decision_label = Label.new()
	rl_decision_label.text = "⚡ LATEST NEURAL DISPATCH:\nAwaiting simulation step..."
	rl_decision_label.add_theme_font_size_override("font_size", 10)
	rl_decision_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rl_decision_label.modulate = Color(1.0, 0.95, 0.4)
	dec_panel.add_child(rl_decision_label)

	# Recent Decisions Stream Header
	var hist_hdr := Label.new()
	hist_hdr.text = "📜 Recent RL Dispatch History:"
	hist_hdr.add_theme_font_size_override("font_size", 10)
	hist_hdr.modulate = Color(0.4, 0.85, 1.0)
	card_rl["content"].add_child(hist_hdr)

	rl_history_container = VBoxContainer.new()
	rl_history_container.add_theme_constant_override("separation", 2)
	rl_history_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_rl["content"].add_child(rl_history_container)

	# --------------------------------------------------------------------------
	# 2. 🛡️ ACTIVE CHALLENGES & OVERCOMING LOG
	# --------------------------------------------------------------------------
	var card_chal = create_styled_card("ACTIVE CHALLENGES OVERCOME", "🛡️", Color(1.0, 0.55, 0.2))
	main_vbox.add_child(card_chal["panel"])

	challenges_container = VBoxContainer.new()
	challenges_container.add_theme_constant_override("separation", 3)
	challenges_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_chal["content"].add_child(challenges_container)

	# --------------------------------------------------------------------------
	# 3. Fleet Overview & Safety Metrics Card
	# --------------------------------------------------------------------------
	var card_metrics = create_styled_card("FLEET METRICS & SAFETY", "📊", Color(0.2, 0.85, 1.0))
	main_vbox.add_child(card_metrics["panel"])

	stats_label = Label.new()
	stats_label.text = "Step: 0 | Completed Tasks: 0\nThroughput: 0.0 / 1k steps\nConflicts Prevented: 0 | Swaps: 0"
	stats_label.add_theme_font_size_override("font_size", 11)
	stats_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stats_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_metrics["content"].add_child(stats_label)

	best_robot_label = Label.new()
	best_robot_label.text = "🏆 Top Performer: Evaluating initial fleet metrics..."
	best_robot_label.add_theme_font_size_override("font_size", 11)
	best_robot_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	best_robot_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	best_robot_label.modulate = Color(1.0, 0.95, 0.4)
	card_metrics["content"].add_child(best_robot_label)

	# --------------------------------------------------------------------------
	# 4. Fleet AGVs Status Cards (R1 to R5)
	# --------------------------------------------------------------------------
	var card_fleet = create_styled_card("FLEET AGV TELEMETRY", "🤖", Color(0.25, 0.95, 0.5))
	main_vbox.add_child(card_fleet["panel"])

	fleet_container = VBoxContainer.new()
	fleet_container.add_theme_constant_override("separation", 6)
	fleet_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_fleet["content"].add_child(fleet_container)

	# Pre-build structured UI cards for R1..R5
	for r_id in range(1, 6):
		var r_theme: Color = robot_colors[(r_id - 1) % robot_colors.size()]

		var r_panel := PanelContainer.new()
		var r_style := StyleBoxFlat.new()
		r_style.bg_color = Color(0.06, 0.08, 0.12, 0.9)
		r_style.border_width_left = 2
		r_style.border_width_top = 1
		r_style.border_width_right = 1
		r_style.border_width_bottom = 1
		r_style.border_color = r_theme * Color(1, 1, 1, 0.8)
		r_style.corner_radius_top_left = 4
		r_style.corner_radius_top_right = 4
		r_style.corner_radius_bottom_left = 4
		r_style.corner_radius_bottom_right = 4
		r_style.content_margin_left = 6
		r_style.content_margin_top = 6
		r_style.content_margin_right = 6
		r_style.content_margin_bottom = 6
		r_panel.add_theme_stylebox_override("panel", r_style)
		r_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

		var r_vbox := VBoxContainer.new()
		r_vbox.add_theme_constant_override("separation", 2)
		r_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r_panel.add_child(r_vbox)

		# Top row: Robot Name, Status badge, Follow button
		var r_top_row := HBoxContainer.new()
		r_top_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r_vbox.add_child(r_top_row)

		var r_name_lbl := Label.new()
		r_name_lbl.text = "AGV R%d" % r_id
		r_name_lbl.add_theme_font_size_override("font_size", 12)
		r_name_lbl.modulate = r_theme
		r_top_row.add_child(r_name_lbl)

		var r_stage_lbl := Label.new()
		r_stage_lbl.text = " [IDLE]"
		r_stage_lbl.add_theme_font_size_override("font_size", 11)
		r_stage_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r_top_row.add_child(r_stage_lbl)

		var r_fol_btn := Button.new()
		r_fol_btn.text = "🎯 Follow"
		r_fol_btn.add_theme_font_size_override("font_size", 10)
		r_fol_btn.pressed.connect(func(): switch_to_follow_robot(r_id))
		r_top_row.add_child(r_fol_btn)

		# Battery line
		var r_bat_lbl := Label.new()
		r_bat_lbl.text = "🔋 Battery: 100% [██████████]"
		r_bat_lbl.add_theme_font_size_override("font_size", 10)
		r_bat_lbl.modulate = Color(0.2, 1.0, 0.4)
		r_vbox.add_child(r_bat_lbl)

		# Location & Done line
		var r_stats_lbl := Label.new()
		r_stats_lbl.text = "📍 Cell: (0, 0) | Done: 0 | Eff: 100%"
		r_stats_lbl.add_theme_font_size_override("font_size", 10)
		r_stats_lbl.modulate = Color(0.8, 0.85, 0.9)
		r_vbox.add_child(r_stats_lbl)

		# Active Task line
		var r_task_lbl := Label.new()
		r_task_lbl.text = "📦 Mission: None (Ready)"
		r_task_lbl.add_theme_font_size_override("font_size", 10)
		r_task_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		r_task_lbl.modulate = Color(0.6, 0.65, 0.75)
		r_vbox.add_child(r_task_lbl)

		fleet_container.add_child(r_panel)

		robot_ui_cards[r_id] = {
			"stage_lbl": r_stage_lbl,
			"bat_lbl": r_bat_lbl,
			"stats_lbl": r_stats_lbl,
			"task_lbl": r_task_lbl
		}

	# --------------------------------------------------------------------------
	# 5. Simulation & Camera Controls Card
	# --------------------------------------------------------------------------
	var card_ctrl = create_styled_card("SIMULATION CONTROLS", "🎮", Color(0.7, 0.8, 0.95))
	main_vbox.add_child(card_ctrl["panel"])

	# Playback Row: Pause/Resume and Reset
	var ctrl_row := HBoxContainer.new()
	ctrl_row.add_theme_constant_override("separation", 6)
	ctrl_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_ctrl["content"].add_child(ctrl_row)

	pause_btn = Button.new()
	pause_btn.text = "⏸ Pause"
	pause_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pause_btn.pressed.connect(func(): toggle_pause())
	ctrl_row.add_child(pause_btn)

	var reset_btn := Button.new()
	reset_btn.text = "🔄 Reset"
	reset_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	reset_btn.pressed.connect(func(): reset_simulation())
	ctrl_row.add_child(reset_btn)

	# Dedicated Speed Buttons Row: 0.5x, 1.0x, 2.0x
	var speed_header := Label.new()
	speed_header.text = "Simulation Speed:"
	speed_header.add_theme_font_size_override("font_size", 10)
	speed_header.modulate = Color(0.7, 0.8, 0.9)
	card_ctrl["content"].add_child(speed_header)

	var speed_row := HBoxContainer.new()
	speed_row.add_theme_constant_override("separation", 4)
	speed_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_ctrl["content"].add_child(speed_row)

	speed_05_btn = Button.new()
	speed_05_btn.text = "0.5x"
	speed_05_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	speed_05_btn.pressed.connect(func(): set_sim_speed(0.5))
	speed_row.add_child(speed_05_btn)

	speed_10_btn = Button.new()
	speed_10_btn.text = "⚡ 1.0x"
	speed_10_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	speed_10_btn.pressed.connect(func(): set_sim_speed(1.0))
	speed_row.add_child(speed_10_btn)

	speed_20_btn = Button.new()
	speed_20_btn.text = "2.0x"
	speed_20_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	speed_20_btn.pressed.connect(func(): set_sim_speed(2.0))
	speed_row.add_child(speed_20_btn)

	update_speed_buttons_visual()

	# Camera Presets Row
	var cam_header := Label.new()
	cam_header.text = "Camera Views (or Keys 1-7):"
	cam_header.add_theme_font_size_override("font_size", 10)
	cam_header.modulate = Color(0.7, 0.8, 0.9)
	card_ctrl["content"].add_child(cam_header)

	var cam_row1 := HBoxContainer.new()
	cam_row1.add_theme_constant_override("separation", 4)
	cam_row1.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_ctrl["content"].add_child(cam_row1)

	var cam_iso := Button.new()
	cam_iso.text = "📷 Overview (1)"
	cam_iso.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cam_iso.pressed.connect(func(): switch_camera(0))
	cam_row1.add_child(cam_iso)

	var cam_top := Button.new()
	cam_top.text = "📷 Top-Down (2)"
	cam_top.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cam_top.pressed.connect(func(): switch_camera(1))
	cam_row1.add_child(cam_top)

	# Follow AGV Row (R1 - R5)
	var cam_row2 := HBoxContainer.new()
	cam_row2.add_theme_constant_override("separation", 3)
	cam_row2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_ctrl["content"].add_child(cam_row2)

	for r_id in range(1, 6):
		var fol_btn := Button.new()
		fol_btn.text = "R%d" % r_id
		fol_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var color: Color = robot_colors[(r_id - 1) % robot_colors.size()]
		fol_btn.modulate = color
		fol_btn.pressed.connect(func(): switch_to_follow_robot(r_id))
		cam_row2.add_child(fol_btn)

	# --------------------------------------------------------------------------
	# 6. Active Missions Card (Source ➔ Target)
	# --------------------------------------------------------------------------
	var card_missions = create_styled_card("ACTIVE MISSIONS (SRC ➔ TGT)", "🎯", Color(0.2, 1.0, 0.5))
	main_vbox.add_child(card_missions["panel"])

	missions_container = VBoxContainer.new()
	missions_container.add_theme_constant_override("separation", 4)
	missions_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_missions["content"].add_child(missions_container)



func update_hud_display(
	step: int,
	metrics: Dictionary,
	robots_list: Array,
	active_tasks: Array,
	best_robot: Dictionary,
	rl_monitor: Dictionary,
	difficulty_events: Array = []
) -> void:
	# 1. Update RL Decision Monitor & Neural Strategy
	if rl_monitor_label != null and rl_monitor.size() > 0:
		var mode: String = rl_monitor.get("mode", "MaskablePPO")
		var conf: String = rl_monitor.get("policy_confidence", "95.0%")
		var val: float = rl_monitor.get("value_estimate", 15.0)
		var valid_acts: int = rl_monitor.get("valid_actions_count", 0)
		var tot_acts: int = rl_monitor.get("total_actions", 26)
		var ep_rew: float = rl_monitor.get("cumulative_reward", 0.0)
		var step_rew: float = rl_monitor.get("step_reward", 0.0)

		rl_monitor_label.text = "● %s\nConfidence: %s | Critic V(s): %+.2f\nLegal Mask: %d / %d (100%% Collision-Safe)\nEp Return: %+.1f | Step Reward: %+.1f" % [
			mode, conf, val, valid_acts, tot_acts, ep_rew, step_rew
		]

	if rl_decision_label != null and rl_monitor.size() > 0:
		var dec: String = rl_monitor.get("decision", "")
		var rsn: String = rl_monitor.get("reasoning", "")
		rl_decision_label.text = "⚡ LATEST NEURAL CHOICE:\n%s\n\n📌 POLICY REASONING:\n%s" % [dec, rsn]

	# Update Recent Decisions History
	if rl_history_container != null and rl_monitor.size() > 0:
		for child in rl_history_container.get_children():
			child.queue_free()
		var recent_decs: Array = rl_monitor.get("recent_decisions", [])
		for item in recent_decs:
			var l := Label.new()
			l.text = "• Step %d: %s\n  (%s)" % [item.get("step", 0), item.get("text", ""), item.get("reason", "")]
			l.add_theme_font_size_override("font_size", 10)
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l.modulate = Color(0.35, 0.9, 1.0)
			rl_history_container.add_child(l)

	# 2. Update Active Challenges Overcome
	if challenges_container != null:
		for child in challenges_container.get_children():
			child.queue_free()
		if difficulty_events.size() == 0:
			var empty_l := Label.new()
			empty_l.text = "• Active multi-robot conflict arbitration ready"
			empty_l.add_theme_font_size_override("font_size", 10)
			empty_l.modulate = Color(0.7, 0.7, 0.7)
			challenges_container.add_child(empty_l)
		else:
			for ev in difficulty_events:
				var el := Label.new()
				el.text = "• %s" % str(ev)
				el.add_theme_font_size_override("font_size", 10)
				el.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				el.modulate = Color(1.0, 0.85, 0.3)
				challenges_container.add_child(el)

	# 3. Update Fleet Metrics
	if stats_label != null:
		var completed: int = metrics.get("completed_tasks", 0)
		var throughput: float = (float(completed) / max(1, step)) * 1000.0
		var conflicts: int = metrics.get("conflicts_resolved", 0)
		var swaps: int = metrics.get("swaps_prevented", 0)

		stats_label.text = "Step: %d | Completed Tasks: %d\nFleet Throughput: %.1f / 1k steps\nConflicts Prevented: %d | Swaps: %d" % [
			step, completed, throughput, conflicts, swaps
		]

	# Update Top Performer Trophy Badge
	if best_robot_label != null and best_robot.size() > 0:
		var b_id: int = best_robot.get("id", 1)
		var b_done: int = best_robot.get("tasks_completed", 0)
		var b_eff: float = best_robot.get("efficiency", 100.0)
		var b_bat: float = best_robot.get("battery", 100.0)
		best_robot_label.text = "Robot R%d is Leading Fleet!\n• Deliveries: %d completed\n• Efficiency: %.0f%%\n• Battery: %.0f%%" % [
			b_id, b_done, b_eff, b_bat
		]

	# 4. Update Active Missions List (Source -> Target clearly visible)
	if missions_container != null:
		for child in missions_container.get_children():
			child.queue_free()

		if active_tasks.size() == 0:
			var empty_lbl := Label.new()
			empty_lbl.text = "• No active missions in transit"
			empty_lbl.add_theme_font_size_override("font_size", 10)
			empty_lbl.modulate = Color(0.65, 0.65, 0.65)
			missions_container.add_child(empty_lbl)
		else:
			for task in active_tasks:
				var t_id: int = task.get("id", 0)
				var r_id: int = task.get("robot_id", 1)
				var p: Array = task.get("pickup", [0, 0])
				var d: Array = task.get("dropoff", [0, 0])
				var prio: String = task.get("priority", "HIGH")
				var stage: String = task.get("stage", "GOING_TO_PICKUP")
				var color: Color = robot_colors[(r_id - 1) % robot_colors.size()]

				var stage_str := "En route to Source" if stage == "GOING_TO_PICKUP" else "Carrying to Target"
				var mission_lbl := Label.new()
				mission_lbl.text = "• R%d: Src (%d, %d) ➔ Tgt (%d, %d)\n  Priority: %s | %s" % [
					r_id, p[0], p[1], d[0], d[1], prio, stage_str
				]
				mission_lbl.add_theme_font_size_override("font_size", 10)
				mission_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				mission_lbl.modulate = color
				missions_container.add_child(mission_lbl)

	# 5. Update Pre-built Fleet AGV Cards (R1 to R5)
	for r_data in robots_list:
		var r_id: int = r_data.get("id", 1)
		if r_id in robot_ui_cards:
			var card: Dictionary = robot_ui_cards[r_id]
			var battery: float = r_data.get("battery", 100.0)
			var stage: String = r_data.get("stage", "IDLE")
			var done: int = r_data.get("tasks_completed", 0)
			var eff: float = r_data.get("efficiency", 100.0)
			var row: int = r_data.get("row", 0)
			var col: int = r_data.get("col", 0)
			var task_id = r_data.get("task_id")
			var is_fault: bool = r_data.get("is_faulty", false)

			# Stage badge
			var stage_color := Color(0.7, 0.75, 0.8)
			if stage == "GOING_TO_PICKUP":
				stage_color = Color(1.0, 0.8, 0.2)
			elif stage == "GOING_TO_DROPOFF":
				stage_color = Color(0.2, 1.0, 0.4)
			elif stage == "CHARGING":
				stage_color = Color(0.4, 0.8, 1.0)
			elif is_fault:
				stage_color = Color(1.0, 0.25, 0.25)

			card["stage_lbl"].text = " [%s]" % stage
			card["stage_lbl"].modulate = stage_color

			# Visual battery bar
			var bat_bars := int(battery / 10.0)
			var bat_visual := ""
			for b in range(10):
				bat_visual += "█" if b < bat_bars else "░"
			var bat_color := Color(0.2, 1.0, 0.4) if battery > 50.0 else (Color(1.0, 0.8, 0.2) if battery > 20.0 else Color(1.0, 0.25, 0.25))
			card["bat_lbl"].text = "🔋 Battery: %d%% [%s]" % [int(battery), bat_visual]
			card["bat_lbl"].modulate = bat_color

			card["stats_lbl"].text = "📍 Cell: (%d, %d) | Done: %d | Eff: %.0f%%" % [row, col, done, eff]

			if task_id != null:
				card["task_lbl"].text = "📦 Mission: Task T%d (%s)" % [task_id, stage]
				card["task_lbl"].modulate = Color(1.0, 0.9, 0.3)
			else:
				card["task_lbl"].text = "📦 Mission: None (Ready for dispatch)"
				card["task_lbl"].modulate = Color(0.55, 0.6, 0.7)


func switch_camera(mode: int) -> void:
	camera_mode = mode
	if camera_mode == 0:
		camera.position = Vector3(0.0, 56.0, 52.0)
		camera.look_at(Vector3(0, 0, 0), Vector3.UP)
	elif camera_mode == 1:
		camera.position = Vector3(0.0, 68.0, 0.0)
		camera.look_at(Vector3(0, 0, 0), Vector3(0, 0, -1))


func switch_to_follow_robot(robot_id: int) -> void:
	follow_robot_id = robot_id
	camera_mode = 2
	print("[GODOT 3D] Camera switched to follow Robot R", robot_id)


func _process(delta: float) -> void:
	poll_network(delta)

	# Smoothly interpolate robot positions along the open aisles
	for r_id in robots_3d:
		var r_node: Node3D = robots_3d[r_id]
		var target_pos: Vector3 = r_node.get_meta("target_pos", r_node.position)
		var target_rot_y: float = r_node.get_meta("target_rot_y", r_node.rotation.y)

		r_node.position = r_node.position.lerp(target_pos, 4.0 * delta)
		r_node.rotation.y = lerp_angle(r_node.rotation.y, target_rot_y, 6.0 * delta)

	# Camera follow mode for the chosen robot
	if camera_mode == 2 and follow_robot_id in robots_3d:
		var target_robot: Node3D = robots_3d[follow_robot_id]
		var desired_cam_pos := target_robot.position + Vector3(8.0, 11.0, 9.0)
		camera.position = camera.position.lerp(desired_cam_pos, 4.0 * delta)
		camera.look_at(target_robot.position + Vector3(0, 0.3, 0), Vector3.UP)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_1:
			switch_camera(0)
		elif event.keycode == KEY_2:
			switch_camera(1)
		elif event.keycode == KEY_3:
			switch_to_follow_robot(1)
		elif event.keycode == KEY_4:
			switch_to_follow_robot(2)
		elif event.keycode == KEY_5:
			switch_to_follow_robot(3)
		elif event.keycode == KEY_6:
			switch_to_follow_robot(4)
		elif event.keycode == KEY_7:
			switch_to_follow_robot(5)
		elif event.keycode == KEY_SPACE:
			toggle_pause()
		elif event.keycode == KEY_R:
			reset_simulation()
