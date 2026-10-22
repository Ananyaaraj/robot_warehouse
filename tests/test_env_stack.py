import sys

def test_stack():
    print(f"Python: {sys.version}")
    import torch
    print(f"PyTorch version: {torch.__version__}")
    import gymnasium as gym
    print(f"Gymnasium version: {gym.__version__}")
    import stable_baselines3 as sb3
    print(f"Stable-Baselines3 version: {sb3.__version__}")
    import sb3_contrib
    print(f"SB3-Contrib version: {sb3_contrib.__version__}")
    import matplotlib
    print(f"Matplotlib version: {matplotlib.__version__}")
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
    import websockets
    print(f"WebSockets version: {websockets.__version__}")
    print("ALL ENVIRONMENT DEPENDENCIES VERIFIED!")

if __name__ == "__main__":
    test_stack()
