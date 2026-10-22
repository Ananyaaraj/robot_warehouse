extends Node3D

# Large, open industrial warehouse
const FLOOR_WIDTH := 120.0
const FLOOR_DEPTH := 100.0
const RACK_HEIGHT := 7.0

const HOST := "127.0.0.1"
const PORT := 8765

var rng := RandomNumberGenerator.new()

# Network bridge
var tcp_client: StreamPeerTCP = null
var is_connected_to_sim := false
var reconnect_timer := 0.0
var net_buffer := ""

# Robot instances dictionary: robot_id -> Node3D
var robots_3d := {}

# Active Camera
var camera: Camera3D = null
var camera_mode := 0 # 0: Isometric, 1: Top-down, 2: Follow R1
var follow_robot_id := 1

# Simulation State Cache
var sim_paused := false
var sim_speed := 1.0

# UI Controls
var hud_layer: CanvasLayer = null
var status_label: Label = null
var stats_label: Label = null
var fleet_container: VBoxContainer = null
var robot_ui_cards := {}


func _ready() -> void:
	rng.randomize()
	build_warehouse()
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


func make_emission_material(color: Color, energy: float = 1.5) -> StandardMaterial3D:
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
# 1. WAREHOUSE ENVIRONMENT CREATION (PRESERVED & EXPANDED)
# ==============================================================================

func build_warehouse() -> void:
	var floor_mat := make_material(Color(0.31, 0.34, 0.36))
	var line_mat := make_material(Color(0.95, 0.72, 0.16))
	var steel_mat := make_material(Color(0.13, 0.23, 0.32), 0.55, 0.4)
	var beam_mat := make_material(Color(0.95, 0.40, 0.12), 0.2, 0.5)
	var pallet_mat := make_material(Color(0.48, 0.30, 0.16))
	var wall_mat := make_material(Color(0.58, 0.62, 0.65))
	var light_mat := make_material(Color(0.95, 0.96, 0.89), 0.1, 0.35)

	var cargo_mats: Array[Material] = [
		make_material(Color(0.16, 0.44, 0.76)),
		make_material(Color(0.80, 0.28, 0.17)),
		make_material(Color(0.20, 0.58, 0.34)),
		make_material(Color(0.88, 0.67, 0.18)),
		make_material(Color(0.53, 0.35, 0.72)),
		make_material(Color(0.72, 0.75, 0.78))
	]

	# Huge concrete floor
	add_box(
		"Warehouse Concrete Floor",
		Vector3(FLOOR_WIDTH, 0.5, FLOOR_DEPTH),
		Vector3(0, -0.3, 0),
		floor_mat
	)

	# Safety boundaries
	add_box("Front Safety Line", Vector3(FLOOR_WIDTH - 2, 0.025, 0.18), Vector3(0, -0.025, FLOOR_DEPTH / 2.0 - 2), line_mat)
	add_box("Rear Safety Line", Vector3(FLOOR_WIDTH - 2, 0.025, 0.18), Vector3(0, -0.025, -FLOOR_DEPTH / 2.0 + 2), line_mat)
	add_box("Left Safety Line", Vector3(0.18, 0.025, FLOOR_DEPTH - 4), Vector3(-FLOOR_WIDTH / 2.0 + 2, -0.025, 0), line_mat)
	add_box("Right Safety Line", Vector3(0.18, 0.025, FLOOR_DEPTH - 4), Vector3(FLOOR_WIDTH / 2.0 - 2, -0.025, 0), line_mat)

	# Floor grid lines
	for x in range(-50, 51, 10):
		add_box("Floor Grid Vertical", Vector3(0.035, 0.012, FLOOR_DEPTH - 6), Vector3(float(x), -0.035, 0), line_mat)
	for z in range(-40, 41, 10):
		add_box("Floor Grid Horizontal", Vector3(FLOOR_WIDTH - 6, 0.012, 0.035), Vector3(0, -0.034, float(z)), line_mat)

	# Perimeter supports
	for x in range(-50, 51, 20):
		for z in [-47.0, 47.0]:
			add_box("Perimeter Support", Vector3(0.6, 10.0, 0.6), Vector3(float(x), 4.7, z), steel_mat)
	for z in range(-40, 41, 20):
		for x in [-57.0, 57.0]:
			add_box("Side Support", Vector3(0.6, 10.0, 0.6), Vector3(x, 4.7, float(z)), steel_mat)

	# Rear wall with loading bays
	add_box("Rear Warehouse Wall", Vector3(FLOOR_WIDTH - 2, 9.0, 0.5), Vector3(0, 4.2, -49.0), wall_mat)
	for x in [-42.0, -28.0, -14.0, 0.0, 14.0, 28.0, 42.0]:
		add_box("Loading Door", Vector3(6.0, 4.8, 0.12), Vector3(x, 2.4, -48.7), steel_mat)
		add_box("Loading Door Header", Vector3(6.8, 0.3, 0.3), Vector3(x, 4.95, -48.5), beam_mat)

	# Storage Rows
	var rack_rows: Array[float] = [-34.0, -18.0, -2.0, 14.0, 30.0]
	for i in range(rack_rows.size()):
		build_rack_row("Storage Row " + str(i + 1), rack_rows[i], -46.0, 46.0, cargo_mats, steel_mat, beam_mat, pallet_mat)

	# Extra floor stacks
	for x in [-48.0, -36.0, 36.0, 48.0]:
		for z in [-25.0, -9.0, 7.0, 23.0]:
			build_standalone_stack(Vector3(x, 0, z), cargo_mats, pallet_mat)

	# Central robot corridor
	add_box("Central Aisle Left Boundary", Vector3(0.16, 0.025, FLOOR_DEPTH - 8), Vector3(-8.0, 0.005, 0), line_mat)
	add_box("Central Aisle Right Boundary", Vector3(0.16, 0.025, FLOOR_DEPTH - 8), Vector3(8.0, 0.005, 0), line_mat)

	# Ceiling light fixtures
	for x in range(-40, 41, 20):
		for z in range(-30, 31, 20):
			add_box("Industrial Ceiling Light", Vector3(3.0, 0.18, 0.9), Vector3(float(x), 10.0, float(z)), light_mat)

	# Directional and ambient lighting
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -32, 0)
	sun.light_energy = 1.4
	add_child(sun)

	var ambient_light := OmniLight3D.new()
	ambient_light.position = Vector3(0, 22, 0)
	ambient_light.omni_range = 120.0
	ambient_light.light_energy = 1.8
	add_child(ambient_light)

	# Isometric Camera
	camera = Camera3D.new()
	camera.name = "Warehouse Camera"
	camera.position = Vector3(82.0, 78.0, 95.0)
	camera.fov = 50.0
	add_child(camera)
	camera.look_at(Vector3(0, 0, 0), Vector3.UP)
	camera.current = true


func build_rack_row(
	row_name: String,
	z: float,
	start_x: float,
	end_x: float,
	cargo_mats: Array[Material],
	steel_mat: Material,
	beam_mat: Material,
	pallet_mat: Material
) -> void:
	var x := start_x
	while x <= end_x:
		for z_offset in [-0.9, 0.9]:
			add_box(row_name + " Steel Upright", Vector3(0.24, RACK_HEIGHT, 0.24), Vector3(x, RACK_HEIGHT / 2.0, z + z_offset), steel_mat)

		for level in range(3):
			var shelf_y := 1.2 + float(level) * 2.25
			add_box(row_name + " Orange Shelf Beam", Vector3(2.8, 0.2, 2.0), Vector3(x + 1.4, shelf_y, z), beam_mat)

			for pallet_index in range(2):
				var pallet_x := x + 0.7 + float(pallet_index) * 1.35
				var cargo_height := rng.randf_range(0.7, 1.2)
				var cargo_index := rng.randi_range(0, cargo_mats.size() - 1)

				add_box("Storage Pallet", Vector3(1.15, 0.18, 1.4), Vector3(pallet_x, shelf_y + 0.2, z), pallet_mat)
				add_box(
					"Colored Cargo Load",
					Vector3(rng.randf_range(0.8, 1.05), cargo_height, 1.05),
					Vector3(pallet_x, shelf_y + 0.28 + cargo_height / 2.0, z),
					cargo_mats[cargo_index]
				)
		x += 3.0


func build_standalone_stack(position: Vector3, cargo_mats: Array[Material], pallet_mat: Material) -> void:
	add_box("Floor Storage Pallet", Vector3(1.8, 0.18, 1.8), position + Vector3(0, 0.09, 0), pallet_mat)
	var levels := rng.randi_range(2, 4)
	for level in range(levels):
		var height := rng.randf_range(0.8, 1.25)
		var cargo_index := rng.randi_range(0, cargo_mats.size() - 1)
		add_box(
			"Floor Stacked Cargo",
			Vector3(rng.randf_range(1.0, 1.5), height, rng.randf_range(1.0, 1.5)),
			position + Vector3(0, 0.18 + height / 2.0 + float(level) * 1.3, 0),
			cargo_mats[cargo_index]
		)


# ==============================================================================
# 2. REALISTIC 3D ROBOT INSTANCING & VISUALIZATION
# ==============================================================================

func create_robot_3d(robot_id: int) -> Node3D:
	var root := Node3D.new()
	root.name = "Robot_R" + str(robot_id)

	# 1. Main AGV Chassis (Lower metallic body)
	var chassis_mat := make_material(Color(0.18, 0.22, 0.26), 0.7, 0.3)
	var chassis := add_box("Chassis", Vector3(1.5, 0.35, 1.8), Vector3(0, 0.2, 0), chassis_mat, root)

	# 2. Four Drive Wheels
	var wheel_mat := make_material(Color(0.08, 0.08, 0.08), 0.1, 0.9)
	var wheel_positions = [
		Vector3(-0.75, 0.15, -0.55),
		Vector3(0.75, 0.15, -0.55),
		Vector3(-0.75, 0.15, 0.55),
		Vector3(0.75, 0.15, 0.55)
	]
	for idx in range(wheel_positions.size()):
		add_box("Wheel_" + str(idx), Vector3(0.18, 0.3, 0.4), wheel_positions[idx], wheel_mat, root)

	# 3. Lidar / Optical Sensor Puck
	var sensor_mat := make_material(Color(0.05, 0.05, 0.05), 0.8, 0.2)
	add_box("SensorPuck", Vector3(0.35, 0.15, 0.35), Vector3(0, 0.45, 0), sensor_mat, root)

	# 4. Status Light Halo / Strip (Glows based on state)
	var halo_mat := make_emission_material(Color(0.2, 0.6, 1.0), 2.0)
	var halo := add_box("StatusHalo", Vector3(1.54, 0.06, 1.84), Vector3(0, 0.36, 0), halo_mat, root)

	# 5. Top Cargo Payload Box (Visible only when carrying cargo)
	var cargo_mat := make_material(Color(0.85, 0.45, 0.15), 0.1, 0.6)
	var cargo := add_box("CargoPayload", Vector3(1.1, 0.65, 1.1), Vector3(0, 0.75, 0), cargo_mat, root)
	cargo.visible = false

	# 6. Floating Label3D
	var label := Label3D.new()
	label.name = "RobotLabel"
	label.text = "R" + str(robot_id) + "\n100%"
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 36
	label.modulate = Color(1.0, 1.0, 1.0)
	label.position = Vector3(0, 1.6, 0)
	root.add_child(label)

	# Target attributes for smooth interpolation
	root.set_meta("target_pos", Vector3.ZERO)
	root.set_meta("target_rot_y", 0.0)

	add_child(root)
	return root


func update_robot_visual(robot_node: Node3D, data: Dictionary) -> void:
	var target_x: float = data.get("world_x", 0.0)
	var target_y: float = data.get("world_y", 0.25)
	var target_z: float = data.get("world_z", 0.0)
	var heading_deg: float = data.get("heading_degrees", 0.0)
	var battery: float = data.get("battery", 100.0)
	var stage: String = data.get("stage", "IDLE")
	var is_fault: bool = data.get("is_faulty", false)
	var is_charging: bool = data.get("is_charging", false)
	var robot_id: int = data.get("id", 1)

	robot_node.set_meta("target_pos", Vector3(target_x, target_y, target_z))
	robot_node.set_meta("target_rot_y", deg_to_rad(-heading_deg + 90.0))

	# Update Label3D
	var label: Label3D = robot_node.get_node_or_null("RobotLabel")
	if label != null:
		label.text = "R%d [%d%%]\n%s" % [robot_id, int(battery), stage]

	# Update Cargo visibility
	var cargo: MeshInstance3D = robot_node.get_node_or_null("CargoPayload")
	if cargo != null:
		cargo.visible = (stage == "GOING_TO_DROPOFF")

	# Update Status Halo Emission Color
	var halo: MeshInstance3D = robot_node.get_node_or_null("StatusHalo")
	if halo != null:
		var state_color := Color(0.2, 0.6, 1.0) # Blue IDLE
		if is_fault or battery < 15.0:
			state_color = Color(1.0, 0.15, 0.15) # Red Fault / Low
		elif is_charging:
			state_color = Color(1.0, 0.85, 0.1) # Yellow Charging
		elif stage == "GOING_TO_DROPOFF":
			state_color = Color(0.15, 0.95, 0.35) # Green Transporting
		elif stage == "GOING_TO_PICKUP":
			state_color = Color(0.1, 0.85, 0.95) # Cyan Moving to Pickup

		var halo_mat := make_emission_material(state_color, 2.2)
		halo.material_override = halo_mat


# ==============================================================================
# 3. TELEMETRY NETWORK CLIENT (TCP STREAM PEER)
# ==============================================================================

func setup_network_bridge() -> void:
	tcp_client = StreamPeerTCP.new()
	attempt_connect()


func attempt_connect() -> void:
	if tcp_client.get_status() == StreamPeerTCP.STATUS_NONE:
		var err := tcp_client.connect_to_host(HOST, PORT)
		if err != OK:
			print("[GODOT 3D] Failed to initiate connection to ", HOST, ":", PORT)


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
			print("[GODOT 3D] Lost connection to Python simulation.")
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
	var metrics: Dictionary = parsed.get("metrics", {})

	for r_data in robots_list:
		var r_id: int = r_data.get("id", 0)
		if r_id not in robots_3d:
			robots_3d[r_id] = create_robot_3d(r_id)
		update_robot_visual(robots_3d[r_id], r_data)

	# Update HUD Dashboard
	update_hud_display(step, metrics, robots_list)


func send_command_to_sim(cmd: Dictionary) -> void:
	if tcp_client != null and tcp_client.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		var json_str := JSON.stringify(cmd) + "\n"
		tcp_client.put_utf8_string(json_str)


# ==============================================================================
# 4. HUD DASHBOARD & CAMERA CONTROLS
# ==============================================================================

func setup_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	var panel := PanelContainer.new()
	panel.position = Vector2(16, 16)
	panel.size = Vector2(380, 480)
	hud_layer.add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	panel.add_child(vbox)

	var title := Label.new()
	title.text = "WAREHOUSE FLEET 3D"
	title.add_theme_font_size_override("font_size", 18)
	vbox.add_child(title)

	status_label = Label.new()
	status_label.text = "◌ INITIALIZING NETWORK..."
	status_label.modulate = Color(1.0, 0.8, 0.2)
	vbox.add_child(status_label)

	stats_label = Label.new()
	stats_label.text = "Step: 0 | Completed: 0 | Throughput: 0.0\nConflicts: 0 | Swaps Saved: 0 | Deadlocks: 0"
	vbox.add_child(stats_label)

	var sep := HSeparator.new()
	vbox.add_child(sep)

	var fleet_title := Label.new()
	fleet_title.text = "FLEET AGV STATUS:"
	vbox.add_child(fleet_title)

	fleet_container = VBoxContainer.new()
	fleet_container.add_theme_constant_override("separation", 4)
	vbox.add_child(fleet_container)

	var sep2 := HSeparator.new()
	vbox.add_child(sep2)

	# Control Buttons
	var btn_row := HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 6)
	vbox.add_child(btn_row)

	var pause_btn := Button.new()
	pause_btn.text = "⏸ Pause"
	pause_btn.pressed.connect(func():
		sim_paused = !sim_paused
		pause_btn.text = "▶ Resume" if sim_paused else "⏸ Pause"
		send_command_to_sim({"cmd": "pause" if sim_paused else "play"})
	)
	btn_row.add_child(pause_btn)

	var reset_btn := Button.new()
	reset_btn.text = "🔄 Reset"
	reset_btn.pressed.connect(func():
		send_command_to_sim({"cmd": "reset"})
	)
	btn_row.add_child(reset_btn)

	var speed_btn := Button.new()
	speed_btn.text = "⚡ Speed 2x"
	speed_btn.pressed.connect(func():
		sim_speed = 2.0 if sim_speed == 1.0 else 1.0
		speed_btn.text = "⚡ Speed 1x" if sim_speed == 2.0 else "⚡ Speed 2x"
		send_command_to_sim({"cmd": "speed", "value": sim_speed})
	)
	btn_row.add_child(speed_btn)

	# Camera Presets
	var cam_row := HBoxContainer.new()
	cam_row.add_theme_constant_override("separation", 6)
	vbox.add_child(cam_row)

	var cam1 := Button.new()
	cam1.text = "📷 Iso"
	cam1.pressed.connect(func(): switch_camera(0))
	cam_row.add_child(cam1)

	var cam2 := Button.new()
	cam2.text = "📷 Top"
	cam2.pressed.connect(func(): switch_camera(1))
	cam_row.add_child(cam2)

	var cam3 := Button.new()
	cam3.text = "📷 Follow R1"
	cam3.pressed.connect(func(): switch_camera(2))
	cam_row.add_child(cam3)


func update_hud_display(step: int, metrics: Dictionary, robots_list: Array) -> void:
	if stats_label != null:
		var completed: int = metrics.get("completed_tasks", 0)
		var throughput: float = (float(completed) / max(1, step)) * 1000.0
		var conflicts: int = metrics.get("conflicts_resolved", 0)
		var swaps: int = metrics.get("swaps_prevented", 0)
		var deadlocks: int = metrics.get("deadlocks_detected", 0)

		stats_label.text = "Step: %d | Completed: %d | Throughput: %.1f\nConflicts: %d | Swaps: %d | Deadlocks: %d" % [
			step, completed, throughput, conflicts, swaps, deadlocks
		]

	for r_data in robots_list:
		var r_id: int = r_data.get("id", 1)
		var battery: float = r_data.get("battery", 100.0)
		var stage: String = r_data.get("stage", "IDLE")

		if r_id not in robot_ui_cards:
			var card := Label.new()
			fleet_container.add_child(card)
			robot_ui_cards[r_id] = card

		robot_ui_cards[r_id].text = "• R%d: [%d%% Battery] | %s" % [r_id, int(battery), stage]


func switch_camera(mode: int) -> void:
	camera_mode = mode
	if camera_mode == 0:
		camera.position = Vector3(82.0, 78.0, 95.0)
		camera.look_at(Vector3(0, 0, 0), Vector3.UP)
	elif camera_mode == 1:
		camera.position = Vector3(0.0, 95.0, 0.0)
		camera.look_at(Vector3(0, 0, 0), Vector3(0, 0, -1))


func _process(delta: float) -> void:
	poll_network(delta)

	# Smoothly interpolate robot positions and rotations
	for r_id in robots_3d:
		var r_node: Node3D = robots_3d[r_id]
		var target_pos: Vector3 = r_node.get_meta("target_pos", r_node.position)
		var target_rot_y: float = r_node.get_meta("target_rot_y", r_node.rotation.y)

		r_node.position = r_node.position.lerp(target_pos, 10.0 * delta)
		r_node.rotation.y = lerp_angle(r_node.rotation.y, target_rot_y, 10.0 * delta)

	# Camera follow mode
	if camera_mode == 2 and follow_robot_id in robots_3d:
		var target_robot: Node3D = robots_3d[follow_robot_id]
		var desired_cam_pos := target_robot.position + Vector3(12.0, 16.0, 14.0)
		camera.position = camera.position.lerp(desired_cam_pos, 4.0 * delta)
		camera.look_at(target_robot.position + Vector3(0, 0.5, 0), Vector3.UP)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_1:
			switch_camera(0)
		elif event.keycode == KEY_2:
			switch_camera(1)
		elif event.keycode == KEY_3:
			switch_camera(2)
		elif event.keycode == KEY_SPACE:
			sim_paused = !sim_paused
			send_command_to_sim({"cmd": "pause" if sim_paused else "play"})
		elif event.keycode == KEY_R:
			send_command_to_sim({"cmd": "reset"})
