from torchinfo import summary
from Code.Test_12 import DPFD_ACAM_ISimAM_TwoChannelFusion
import torch

# ======================================================================================================================
# Hyperparameter Configuration
# Adjust these values to inspect the structural parameters of different model variants.
# ======================================================================================================================
conv_channels = 256  # Number of convolution channels (controls model width)
cbam_reduction = 8  # Reduction ratio for the Channel Attention Module
batch_size = 32  # Batch size for the dummy input
in_channels = 1  # Number of input channels

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model Initialization
model = DPFD_ACAM_ISimAM_TwoChannelFusion(in_channels, conv_channels, cbam_reduction).to(device)

# 1. High-level Model Summary
# Generates a table view of input/output shapes and parameter counts.
print("=" * 80)
print("Model Architecture Summary")
print("=" * 80)
summary(model,
        input_size=(batch_size, in_channels, 3, 4),
        col_names=["input_size", "output_size", "num_params"])

# 2. Detailed Parameter Inspection
# Iterates through all sub-modules to inspect specific weight/bias shapes.
print("\n" + "=" * 80)
print("Detailed Module & Parameter List")
print("=" * 80)

for name, module in model.named_modules():
    # Print the name of the layer/module
    print(f"Sub-module: {name}")

    # Iterate through the parameters (weights, bias) of this specific module
    for pname, p in module.named_parameters(recurse=False):
        print(f"   Parameter: {pname}, Shape: {p.shape}")