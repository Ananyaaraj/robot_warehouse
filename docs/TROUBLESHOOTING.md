# Troubleshooting Guide

This guide covers verified solutions for common operational and development issues in the multi-robot warehouse fleet system.

---

## 1. Environment & Dependencies

### Issue: `ModuleNotFoundError: No module named 'warehouse'` or `'core'`
**Cause:** Python executable invoked outside the root workspace without the repository root in `sys.path`.  
**Resolution:**
- Always run commands from `D:\multi_robot`.
- Run scripts as modules where applicable:
  ```powershell
  .\venv\Scripts\python.exe -m pytest tests -v
  ```
- All standalone entry points (`benchmark_runner.py`, `train_ppo.py`, `evaluate.py`, `telemetry_server.py`) automatically insert `PROJECT_ROOT` into `sys.path`.

### Issue: `ExecutionPolicy` error when activating virtualenv in PowerShell
**Cause:** Windows restricts script execution by default.  
**Resolution:**
Run directly using the interpreter binary:
```powershell
& ".\venv\Scripts\python.exe" <script.py>
```
Or allow script execution for the current user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 2. Godot 3D Visualization & Bridge

### Issue: Godot displays "○ DISCONNECTED - RETRYING..." on the HUD
**Cause:** The Python telemetry server is not running or port 8765 is in use.  
**Resolution:**
1. Start the telemetry server first:
   ```powershell
   .\venv\Scripts\python.exe bridge\telemetry_server.py
   ```
2. Verify port 8765 is listening:
   ```powershell
   Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
   ```
3. If port is blocked by a previous process, kill it:
   ```powershell
   Stop-Process -Id (Get-NetTCPConnection -LocalPort 8765).OwningProcess -Force
   ```

### Issue: Godot displays black screen or crashes on older GPU
**Cause:** Vulkan Forward+ driver incompatibility.  
**Resolution:** The project is already configured for `gl_compatibility` in `godot-warehouse3d/project.godot`. Ensure your display driver is up to date, or launch with `--rendering-driver opengl3`.

---

## 3. RL Training & Checkpoint Handling

### Issue: `UserWarning: Evaluation environment is not wrapped with a Monitor wrapper`
**Cause:** Gymnasium wrapper order warning during evaluation callback.  
**Resolution:** Harmless informational warning from SB3; evaluation rewards and lengths are tracked accurately by `MaskableEvalCallback`.

### Issue: Training is slow or high CPU usage
**Cause:** By default, rollouts run on all available CPU threads.  
**Resolution:** To restrict thread usage, set PyTorch threads before training:
```python
import torch
torch.set_num_threads(6)
```
In our tests on the Intel Core Ultra 5 225H, training achieves **~900 FPS**, completing 30,000 timesteps in ~35 seconds.
