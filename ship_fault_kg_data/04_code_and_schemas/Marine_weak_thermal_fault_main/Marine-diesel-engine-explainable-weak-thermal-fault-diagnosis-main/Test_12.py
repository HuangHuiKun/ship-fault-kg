import torch.nn as nn
import torch
import torch.nn.functional as F
from sklearn.decomposition import PCA
from Code.config import * # Assuming this contains hyperparameters like dropout, kernel_size, etc.

# =====================================================================================================================
class ChannelAttention(nn.Module):
    """
    Channel Attention Module (CAM).

    Mechanisms:
        Computes channel-wise importance weights by applying Global Average Pooling (GAP)
        and Global Max Pooling (GMP), followed by a shared Multi-Layer Perceptron (MLP).
        This emphasizes informative channels and suppresses less useful ones.
    """

    def __init__(self, in_channels, reduction_ratio=16):
        super().__init__()
        # Global Average Pooling: Output shape (batch, channels, 1, 1)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        # Global Max Pooling: Output shape (batch, channels, 1, 1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        # Shared MLP: Dimensionality reduction -> ReLU -> Restoration
        self.fc = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // reduction_ratio, 1, bias=False),  # Dimensionality reduction
            nn.ReLU(),
            nn.Conv2d(in_channels // reduction_ratio, in_channels, 1, bias=False)   # Restore dimensionality
        )
        self.sigmoid = nn.Sigmoid()  # Map output to [0, 1] range

    def forward(self, x):
        # Pass average-pooled features through the shared MLP
        avg_out = self.fc(self.avg_pool(x))
        # Pass max-pooled features through the shared MLP
        max_out = self.fc(self.max_pool(x))
        # Element-wise summation of both branches
        out = avg_out + max_out

        return self.sigmoid(out)


# =====================================================================================================================
class SpatialAttention(nn.Module):
    """
    Spatial Attention Module (SAM).

    Mechanisms:
        Generates a spatial attention map to highlight 'where' the informative features are.
        Utilizes channel-wise mean and max pooling followed by a convolution layer.
    """

    def __init__(self, kernel_size=7):
        super().__init__()
        # Ensure padding maintains the spatial dimensions (H, W)
        padding = (kernel_size - 1) // 2
        # Convolution layer to compress 2 channels (avg + max) into 1 channel spatial map
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # Channel-wise statistics
        avg_out = torch.mean(x, dim=1, keepdim=True)       # Mean pooling along channel axis
        max_out, _ = torch.max(x, dim=1, keepdim=True)     # Max pooling along channel axis

        # Concatenate along the channel dimension -> Shape: (batch, 2, H, W)
        out = torch.cat([avg_out, max_out], dim=1)
        # Apply convolution to fuse features
        out = self.conv(out)
        # Apply Sigmoid to generate spatial attention map
        return self.sigmoid(out)


# =====================================================================================================================
class ACAM(nn.Module):
    """
    Convolutional Block Attention Module (CBAM).

    Structure:
        Sequentially applies Channel Attention and Spatial Attention.
        Refines features by emphasizing 'what' is important (Channel) and 'where' it is (Spatial).
    """

    def __init__(self, in_channels, reduction_ratio=16, spatial_kernel=1):
        super().__init__()
        # Channel Attention Map: [B, C, 1, 1]
        self.channel_attention = ChannelAttention(in_channels, reduction_ratio)
        # Spatial Attention Map: [B, 1, H, W]
        self.spatial_attention = SpatialAttention(spatial_kernel)

    def forward(self, x):
        # 1. Apply Channel Attention
        out = self.channel_attention(x)
        self.ca_weight = out  # Store weights for visualization or analysis
        x = out * x           # Broadcast multiplication

        # 2. Apply Spatial Attention (Commented out in original code, uncomment if needed)
        # out = self.spatial_attention(x)
        # self.sa_weight = out
        # x = out * x

        return x


# =====================================================================================================================
# --- ISimAM Module ---
class ISimAM(nn.Module):
    """
    ISimAM: A Simple, Parameter-Free Attention Module.

    Theory:
        Based on neuroscience theories (energy function) to calculate the importance of each neuron.
        It finds neurons that are statistically different from the surrounding background.
    """

    def __init__(self, e_lambda=1e-4):
        super().__init__()
        self.e_lambda = e_lambda       # Epsilon to prevent division by zero
        self.attention_map = None      # Placeholder to store the generated attention map

    def forward(self, x):
        b, c, h, w = x.size()
        n = h * w - 1  # Total pixels minus the current one (degree of freedom correction)

        # Calculate squared difference from the channel mean
        x_minus_mean_square = (x - x.mean(dim=[2, 3], keepdim=True)) ** 2

        # Calculate channel-wise variance
        var = x_minus_mean_square.sum(dim=[2, 3], keepdim=True) / n

        # Compute the energy function (1/energy roughly indicates importance)
        # Formula derived from the SimAM paper
        attention = x_minus_mean_square / (4 * (var + self.e_lambda)) + 0.5

        # Map to [0, 1] probability range
        attention = torch.sigmoid(attention)

        self.attention_map = attention.detach()  # Save for visualization

        # Reweight the input features
        return x * attention


# =====================================================================================================================
#  1. MLP Filter Generator
class MLPFilterGenerator(nn.Module):
    """
    Generates dynamic convolution filters based on input features using an MLP.
    """
    def __init__(self, in_features=2 * 3 * 4, out_channels=64, in_channels=2, kernel_size=3, MLP_hidden=4):
        super().__init__()
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.in_channels = in_channels

        self.mlp = nn.Sequential(
            nn.Linear(in_features, MLP_hidden),
            nn.Tanh(),
            nn.Linear(MLP_hidden, out_channels * self.in_channels * kernel_size * kernel_size)
        )

    def forward(self, x):  # Input x: (B, 2, 3, 4)
        B = x.size(0)
        x_flat = x.view(B, -1)     # Flatten input
        weights = self.mlp(x_flat) # Generate weights
        # Reshape linear output to convolutional kernel format: [B, C_out, C_in, K, K]
        filters = weights.view(B, self.out_channels, self.in_channels, self.kernel_size, self.kernel_size)
        return filters


# 2. Dynamic Conv2D V1 (Basic MLP)
class DynamicConv2D_v1(nn.Module):
    """
    Dynamic Convolution v1:
    Generates sample-specific kernels dependent on the input instance itself.
    """
    def __init__(self, in_channels, out_channels, kernel_size):
        super(DynamicConv2D_v1, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.generator = None  # Lazy initialization

    def forward(self, x):  # x: [B, C_in, H, W]
        B, C_in, H, W = x.shape
        in_features = C_in * H * W

        # Lazy initialization to handle input size dependency
        if self.generator is None:
            self.generator = MLPFilterGenerator(
                in_features=in_features,
                out_channels=self.out_channels,
                in_channels=self.in_channels,
                kernel_size=self.kernel_size
            ).to(x.device)

        # Generate filters: [B, C_out, C_in, kH, kW]
        filters = self.generator(x)

        # Reshape input and filters for grouped convolution
        # We treat the batch as a large 'group' to apply different filters to each sample
        x_reshaped = x.view(1, B * C_in, H, W)
        filters_reshaped = filters.view(B * self.out_channels, self.in_channels, self.kernel_size, self.kernel_size)

        # Perform convolution with groups=B
        x = F.conv2d(x_reshaped, filters_reshaped, groups=B, padding=1)

        # Restore original batch dimension: (B, out_channels, H_out, W_out)
        H_out, W_out = x.shape[2], x.shape[3]
        x = x.view(B, self.out_channels, H_out, W_out)
        return x


# =====================================================================================================================
#  1. Standard Filter Generator
class FilterGenerator(nn.Module):
    def __init__(self, in_features, num_filter_params):
        super().__init__()
        self.generator_mlp = nn.Sequential(
            nn.Linear(in_features, 512),  # Hidden layer size
            nn.Tanh(),
            nn.Linear(512, num_filter_params)
        )

    def forward(self, x):
        return self.generator_mlp(x)


# 2. PCA Trend Extraction
def get_batch_pca_trend(x_batch):
    """
    Extracts the principal trend (PC1) from the batch using PCA.
    This captures the dominant global variation pattern.
    """
    B, C, H, W = x_batch.shape
    device = x_batch.device
    # Flatten: [B, Features]
    x_flattened = x_batch.view(B, -1).cpu().detach().numpy()

    if x_flattened.shape[0] < 2:  # PCA requires at least 2 samples
        return torch.zeros(C, H, W, device=device)

    # Compute Principal Component Analysis
    pca = PCA(n_components=1)
    pca.fit(x_flattened)

    # pc1_vector represents the direction of maximum variance
    pc1_vector = pca.components_[0]
    trend_vector_torch = torch.tensor(pc1_vector, dtype=torch.float32, device=device)

    return trend_vector_torch.view(C, H, W)


#  3. Dynamic Conv2D V2 (Dual-Path: Trend + Mean)
class DynamicConv2D_v2(nn.Module):
    """
    Dynamic Convolution v2:
    Generates filters based on global context decoupled into two paths:
    1. Mean Feature (Static baseline)
    2. Trend Feature (PCA-based variation)
    """
    def __init__(self, out_channels, kernel_size=3):
        super().__init__()
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.generator_tre = None  # Generator for Trend path
        self.generator_mean = None  # Generator for Mean path

    def forward(self, x):
        # x shape: [B, C, H, W]
        B, C, H, W = x.shape
        device = x.device

        # --- Phase 1: Global Feature Extraction ---
        # 1. Mean Image: [C, H, W]
        mean_image = x.mean(dim=0)
        # 2. Trend Image (via PCA): [C, H, W]
        trend_image = get_batch_pca_trend(x)

        # --- Phase 2: Prepare Generator Inputs ---
        # Flatten features
        context_vector_tre = trend_image.flatten()  # shape: [1*C*H*W]
        context_vector_mean = mean_image.flatten()  # shape: [1*C*H*W]

        # --- Phase 3: Dynamic Filter Generation ---
        # Lazy initialization
        if self.generator_tre is None:
            in_features = context_vector_tre.shape[0]
            num_filter_params = self.out_channels * C * self.kernel_size * self.kernel_size
            self.generator_tre = FilterGenerator(in_features, num_filter_params).to(device)

        if self.generator_mean is None:
            in_features = context_vector_mean.shape[0]
            num_filter_params = self.out_channels * C * self.kernel_size * self.kernel_size
            self.generator_mean = FilterGenerator(in_features, num_filter_params).to(device)

        # Generate shared filter weights for the entire batch
        filter_params_tre = self.generator_tre(context_vector_tre)
        filter_params_mean = self.generator_mean(context_vector_mean)

        # Reshape to [C_out, C_in, k, k]
        generated_filter_tre = filter_params_tre.view(self.out_channels, C, self.kernel_size, self.kernel_size)
        generated_filter_mean = filter_params_mean.view(self.out_channels, C, self.kernel_size, self.kernel_size)

        # --- Phase 4: Apply Convolution ---
        padding = self.kernel_size // 2

        # Convolve using the generated global filters
        output_tre = F.conv2d(x, generated_filter_tre, padding=padding)
        output_mean = F.conv2d(x, generated_filter_mean, padding=padding)
        # output shape: [B, C_out, H, W]

        return output_tre, output_mean


# =====================================================================================================================
# 1. Flexible MLP Filter Generator
class FilterGenerator_v1(nn.Module):
    """A standard, flexible MLP for filter generation."""
    def __init__(self, in_features, num_filter_params):
        super().__init__()
        self.generator_mlp = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_filter_params)
        )

    def forward(self, x):
        return self.generator_mlp(x)


# 2. Dynamic Conv2D V3 (Window-based Spatially Adaptive)
class DynamicConv2D_v3(nn.Module):
    """
    Dynamic Convolution v3: Spatially Adaptive Window-based Convolution.
    Decomposes the image into patches/windows and generates specific filters
    for each local window based on local statistics (Mean + Trend).
    """
    def __init__(self, out_channels, kernel_size=3, window_size=5, stride=1):
        super().__init__()
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.window_size = window_size
        self.stride = stride
        self.padding = window_size // 2

        self.generator_tre = None
        self.generator_mean = None

    def forward(self, x):
        B, C, H, W = x.shape
        device = x.device

        # --- 1. Decomposition: Extract Local Patches ---
        # Unfold extracts sliding local blocks from a batched input tensor
        patches_col = F.unfold(x, kernel_size=self.window_size, stride=self.stride, padding=self.padding)
        L = patches_col.shape[2]  # Number of sliding windows (patches)
        # Reshape to [N, C, Win_H, Win_W], where N = Batch * num_windows
        windows_batch = patches_col.transpose(1, 2).contiguous().view(-1, C, self.window_size, self.window_size)
        N = windows_batch.shape[0]

        # --- 2. Local Feature Extraction ---
        # Compute mean per window -> Shape: [N, C]
        mean_vectors = windows_batch.mean(dim=(2, 3))

        # Compute trend (Standard Deviation) per window -> Shape: [N, C]
        # Uses std dev instead of PCA for computational efficiency on patches
        trend_vectors = torch.std(windows_batch.view(N, C, -1), dim=2)

        # Feature Inputs for Generators
        generator_input_tre = trend_vectors   # Shape: [N, C]
        generator_input_mean = mean_vectors   # Shape: [N, C]

        # --- 3. Filter Generation ---
        # Generate exclusive filters for each window
        if self.generator_tre is None:
            in_features = generator_input_tre.shape[1]
            num_filter_params = self.out_channels * C * self.kernel_size * self.kernel_size
            self.generator_tre = FilterGenerator_v1(in_features, num_filter_params).to(device)

        filter_params_tre = self.generator_tre(generator_input_tre)  # Shape: [N, params]

        if self.generator_mean is None:
            in_features = generator_input_mean.shape[1]
            num_filter_params = self.out_channels * C * self.kernel_size * self.kernel_size
            self.generator_mean = FilterGenerator_v1(in_features, num_filter_params).to(device)

        filter_params_mean = self.generator_mean(generator_input_mean) # Shape: [N, params]

        # --- 4. Per-Window Dynamic Convolution ---
        # a. Reshape input for grouped convolution: [1, N*C, win, win]
        x_reshaped = windows_batch.view(1, N * C, self.window_size, self.window_size)

        # b. Reshape filters: [N*C_out, C, k, k]
        filters_reshaped_tre = filter_params_tre.view(N * self.out_channels, C, self.kernel_size, self.kernel_size)
        filters_reshaped_mean = filter_params_mean.view(N * self.out_channels, C, self.kernel_size, self.kernel_size)

        # c. Execute convolution with groups=N (one filter set per window)
        conv_padding = self.kernel_size // 2
        output_patches_tre = F.conv2d(x_reshaped, filters_reshaped_tre, groups=N, padding=conv_padding)
        output_patches_mean = F.conv2d(x_reshaped, filters_reshaped_mean, groups=N, padding=conv_padding)

        # d. Restore shapes: [N, C_out, win_size, win_size]
        output_patches_tre = output_patches_tre.view(N, self.out_channels, self.window_size, self.window_size)
        output_patches_mean = output_patches_mean.view(N, self.out_channels, self.window_size, self.window_size)

        # --- 5. Reconstruction: Merge patches back to image ---
        # a. Flatten patches to match 'fold' requirements
        output_patches_flat_tre = output_patches_tre.view(N, -1)
        output_patches_flat_mean = output_patches_mean.view(N, -1)

        # b. Reshape back to col format: [B, C_out*win*win, L]
        output_col_tre = output_patches_flat_tre.view(B, L, -1).transpose(1, 2)
        output_col_mean = output_patches_flat_mean.view(B, L, -1).transpose(1, 2)

        # c. Apply F.fold to reconstruct the full spatial map
        final_output_tre = F.fold(
            output_col_tre,
            output_size=(H, W),
            kernel_size=self.window_size,
            stride=self.stride,
            padding=self.padding
        )

        final_output_mean = F.fold(
            output_col_mean,
            output_size=(H, W),
            kernel_size=self.window_size,
            stride=self.stride,
            padding=self.padding
        )

        # d. Normalization: Handle overlapping regions
        # F.fold sums up overlapping values; we need the average.
        normalizer_col = torch.ones_like(output_col_tre)
        normalizer = F.fold(
            normalizer_col,
            output_size=(H, W),
            kernel_size=self.window_size,
            stride=self.stride,
            padding=self.padding
        )
        # Avoid division by zero
        normalizer[normalizer == 0] = 1.0

        final_output_tre = final_output_tre / normalizer
        final_output_mean = final_output_mean / normalizer

        return final_output_tre, final_output_mean


# =====================================================================================================================
# Fusion Layer
class ConcatLayer(nn.Module):
    """Simple feature concatenation along the channel dimension."""
    def forward(self, x1, x2):
        return torch.cat([x1, x2], dim=1)


# =====================================================================================================================
#  Dynamic Conv2D V4 (Mixture of Experts)
class DynamicConv2D_v4(nn.Module):
    """
    Dynamic Convolution v4: Mixture of Experts (MoE).
    Dynamically weights multiple 'expert' convolution kernels based on input features.
    """
    def __init__(self, in_channels, out_channels, kernel_size, num_experts=3):
        super().__init__()
        self.num_experts = num_experts
        self.out_channels = out_channels
        self.kernel_size = kernel_size

        # Lazy initialization
        self.router = None
        self.expert_weights = None

    def forward(self, x):
        B, C_in, H, W = x.shape

        # Lazy Initialization for Router and Experts
        if self.router is None:
            # i. Routing Network: Predicts weights for each expert [B, Num_Experts]
            self.router = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(C_in, self.num_experts),
                nn.Softmax(dim=1)
            ).to(x.device)

            # ii. Expert Weights: [Num_Experts, Out, In, K, K]
            self.expert_weights = nn.Parameter(
                torch.randn(self.num_experts, self.out_channels, C_in, self.kernel_size, self.kernel_size)
            ).to(x.device)
            nn.init.kaiming_normal_(self.expert_weights, mode='fan_out', nonlinearity='relu')

        # Calculate routing weights
        routing_weights = self.router(x)  # [B, num_experts]

        # Aggregate expert weights based on routing probability
        # Einsum: 'be, eochw -> bochw'
        # b: batch, e: experts, o: out_channels, c: in_channels, h/w: kernel size
        combined_weights = torch.einsum('be,eochw->bochw', routing_weights, self.expert_weights)
        # combined_weights shape: [B, C_out, C_in, k, k]

        # Apply convolution sample-wise (using group convolution trick)
        x_reshaped = x.view(1, B * C_in, H, W)
        weights_reshaped = combined_weights.view(B * self.out_channels, C_in, self.kernel_size, self.kernel_size)
        padding = self.kernel_size // 2

        output = F.conv2d(x_reshaped, weights_reshaped, groups=B, padding=padding)
        output = output.view(B, self.out_channels, output.shape[-2], output.shape[-1])
        return output


# =====================================================================================================================
# SE Convolution
class DynamicConv2D_v5(nn.Module):
    """
    Dynamic Convolution v5: Squeeze-and-Excitation (SE) Convolution.
    Integrates channel re-calibration (SE block) directly into the convolution block.
    """
    def __init__(self, out_channels, kernel_size, stride=1, reduction_ratio=16):
        super().__init__()
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.reduction_ratio = reduction_ratio

        self.conv = None
        self.squeeze = nn.AdaptiveAvgPool2d(1)
        self.excitation = None

    def forward(self, x):
        B, C_in, H, W = x.shape

        # Lazy initialization
        if self.conv is None:
            # a. Standard Convolution
            padding = self.kernel_size // 2
            self.conv = nn.Conv2d(
                in_channels=C_in,
                out_channels=self.out_channels,
                kernel_size=self.kernel_size,
                stride=self.stride,
                padding=padding
            ).to(x.device)

            # b. Excitation Network (MLP)
            self.excitation = nn.Sequential(
                nn.Linear(self.out_channels, self.out_channels // self.reduction_ratio, bias=False),
                nn.ReLU(inplace=True),
                nn.Linear(self.out_channels // self.reduction_ratio, self.out_channels, bias=False),
                nn.Sigmoid()
            ).to(x.device)

        # 1. Convolution: [B, C_out, H', W']
        x_conv = self.conv(x)

        # 2. SE Attention: Recalibrate channel importance based on output features
        y = self.squeeze(x_conv).view(B, self.out_channels)
        y = self.excitation(y).view(B, self.out_channels, 1, 1)

        # 3. Scale Output
        return x_conv * y.expand_as(x_conv)


# =====================================================================================================================
#  Depthwise Separable Convolution
class DynamicConv2D_v6(nn.Module):
    """
    Depthwise Separable Convolution.
    Standard efficient convolution decoupling spatial and channel correlations.
    """
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=1):
        super().__init__()
        # Depthwise: Spatially convolve each channel independently
        self.depthwise = nn.Conv2d(
            in_channels,
            in_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            groups=in_channels  # Groups = in_channels creates depthwise conv
        )
        # Pointwise: Mix channels using 1x1 convolution
        self.pointwise = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=1
        )
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.depthwise(x)
        x = self.pointwise(x)
        x = self.relu(x)
        return x


# =====================================================================================================================
class DPFD_ACAM_ISimAM_TwoChannelFusion(nn.Module):
    """
    Dual-Path Convolutional Neural Network with Attention Mechanisms.
    Integrates CBAM, SimAM, and Dynamic Convolution strategies for 11-class classification.
    """

    def __init__(self, in_channels=1, conv_channels=64, cbam_reduction=16):
        super().__init__()
        self.concat1 = ConcatLayer()  # Feature fusion layer
        self.concat2 = ConcatLayer()
        self.in_channels = in_channels
        self.conv_channels = conv_channels
        self.cbam_reduction = cbam_reduction

        # --- Filter Configuration Selection ---
        # Modify the lines below to switch between different convolution strategies.

        # Option 0: Basic MLP Dynamic Conv
        # self.dynamic_conv1_1 = DynamicConv2D_v1(in_channels=in_channels, out_channels=conv_channels // 4, kernel_size=kernel_size)
        # self.dynamic_conv2_1 = DynamicConv2D_v1(in_channels=conv_channels//2, out_channels=conv_channels // 2, kernel_size=kernel_size)

        # Option 1: Dual-Path Dynamic Conv (Trend + Mean) - [Currently Active]
        self.dynamic_conv1_1 = DynamicConv2D_v2(out_channels=conv_channels//4, kernel_size=kernel_size)
        self.dynamic_conv2_1 = DynamicConv2D_v2(out_channels=conv_channels//2, kernel_size=kernel_size)

        # Option 2: Window-based Dynamic Conv
        # self.dynamic_conv1_1 = DynamicConv2D_v3(out_channels=conv_channels // 4, kernel_size=kernel_size, window_size=window_size, stride=1)
        # self.dynamic_conv2_1 = DynamicConv2D_v3(out_channels=conv_channels // 2, kernel_size=kernel_size, window_size=window_size, stride=1)

        # Option 3: Mixture of Experts (MoE)
        # self.dynamic_conv1_1 = DynamicConv2D_v4(in_channels=in_channels, out_channels=conv_channels // 4, kernel_size=kernel_size, num_experts=1)
        # self.dynamic_conv2_1 = DynamicConv2D_v4(in_channels=in_channels // 2, out_channels=conv_channels // 2, kernel_size=kernel_size, num_experts=1)

        # Option 4: Dilated Convolution (Atrous)
        # dilation_rate = 1
        # self.dynamic_conv1_1 = nn.Conv2d(in_channels, conv_channels//4, kernel_size=kernel_size, padding=1, dilation=dilation_rate)
        # self.dynamic_conv2_1 = nn.Conv2d(conv_channels//2, conv_channels//2, kernel_size=kernel_size, padding=1, dilation=dilation_rate)

        # Option 5: SE Convolution
        # self.dynamic_conv1_1 = DynamicConv2D_v5(conv_channels//4, kernel_size=kernel_size, reduction_ratio=16)
        # self.dynamic_conv2_1 = DynamicConv2D_v5(conv_channels//2, kernel_size=kernel_size, reduction_ratio=16)

        # Option 6: Group Convolution
        # groups = conv_channels//4
        # self.dynamic_conv1_1 = nn.Conv2d(in_channels, conv_channels//4, kernel_size=kernel_size, padding=padding)
        # self.dynamic_conv2_1 = nn.Conv2d(conv_channels//2, conv_channels//2, kernel_size=kernel_size, padding=padding, groups=groups)

        # Option 7: Depthwise Separable Convolution
        # self.dynamic_conv1_1 = DynamicConv2D_v6(in_channels, conv_channels // 4, kernel_size=kernel_size)
        # self.dynamic_conv2_1 = DynamicConv2D_v6(conv_channels // 2, conv_channels // 2, kernel_size=kernel_size)

        # Option 8: Standard Convolution
        # self.dynamic_conv1_1 = nn.Conv2d(in_channels, conv_channels // 4, kernel_size=kernel_size, padding=padding)
        # self.dynamic_conv2_1 = nn.Conv2d(conv_channels // 2, conv_channels // 2, kernel_size=kernel_size, padding=padding)

        # --- Layer 1 Definition ---
        self.bn1 = nn.BatchNorm2d(conv_channels // 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.cbam1 = ACAM(conv_channels // 2, reduction_ratio=cbam_reduction)
        self.simam1 = ISimAM()
        self.pool = nn.MaxPool2d((1, 1))  # Keep spatial dimensions unchanged

        # --- Layer 2 Definition ---
        self.bn2 = nn.BatchNorm2d(conv_channels)
        self.cbam2 = ACAM(conv_channels, reduction_ratio=cbam_reduction)
        self.simam2 = ISimAM()
        self.global_pool = nn.AdaptiveAvgPool2d(1)

        # --- Classifier ---
        # If using concatenated output (64 channels)
        self.fc = nn.Linear(conv_channels, 11)
        # If using single path (32 channels)
        # self.fc = nn.Linear(conv_channels//2, 11)

    def forward(self, x):
        # --- Block 1 ---
        # Dual-path dynamic convolution extraction
        # x_1 and x_2 are features from Trend and Mean paths respectively
        x_1, x_2 = self.dynamic_conv1_1(x)

        # Feature Fusion
        x = self.concat1(x_1, x_2)
        x = self.bn1(x)
        x = self.relu(x)

        # Attention Mechanism Application
        x = self.cbam1(x)
        self.ca_weight1 = self.cbam1.ca_weight  # Store weights
        x = self.simam1(x)

        # Pooling
        x = self.pool(x)

        # --- Block 2 ---
        x_1, x_2 = self.dynamic_conv2_1(x)

        # Feature Fusion
        x = self.concat2(x_1, x_2)
        x = self.bn2(x)
        x = self.relu(x)

        # Attention Mechanism Application
        x = self.cbam2(x)
        self.ca_weight2 = self.cbam2.ca_weight
        x = self.simam2(x)

        # --- Classification Head ---
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)  # Flatten: (batch_size, channels)
        x = self.dropout(x)
        x = self.fc(x)  # Prediction

        return x