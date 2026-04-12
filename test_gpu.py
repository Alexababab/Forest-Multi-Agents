import torch
print(f"CUDA 可用性: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"检测到的显卡: {torch.cuda.get_device_name(0)}")