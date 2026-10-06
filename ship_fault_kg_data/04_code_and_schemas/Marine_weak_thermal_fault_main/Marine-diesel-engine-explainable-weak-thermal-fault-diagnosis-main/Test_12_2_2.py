import torch
import torch.nn.functional as F
import numpy as np


def normalize_cam(cam):
    """
    Normalizes the Class Activation Map (CAM) to the range [0, 1].

    Args:
        cam (np.ndarray): The raw CAM heatmap.

    Returns:
        np.ndarray: Normalized CAM.
    """
    cam = cam - np.min(cam)
    # Add epsilon to prevent division by zero
    cam_img = cam / (np.max(cam) + 1e-10)
    return cam_img


# --- BaseCAM: Abstract Base Class for CAM Methods ---
class BaseCAM:
    """
    Base Class Activation Map (CAM) wrapper.
    Handles the registration of forward and backward hooks to capture
    feature maps and gradients.
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _forward_hook(self, module, input, output):
        # Capture feature maps (activations) during forward pass
        self.activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        # Capture gradients during backward pass
        # grad_output[0] corresponds to the gradients of the target class score w.r.t layer output
        self.gradients = grad_output[0].detach()

    def _register_hooks(self):
        """Registers hooks to the specified target layer."""
        found = False
        for name, module in self.model.named_modules():
            if name == self.target_layer:
                self.forward_handle = module.register_forward_hook(self._forward_hook)
                self.backward_handle = module.register_backward_hook(self._backward_hook)
                found = True
                break
        if not found:
            raise ValueError(f"Target layer '{self.target_layer}' not found in the model.")

    def _remove_hooks(self):
        """Removes hooks to prevent memory leaks."""
        self.forward_handle.remove()
        self.backward_handle.remove()

    def _compute_weights(self):
        """Abstract method to calculate channel weights."""
        raise NotImplementedError

    def generate_cam(self, input_tensor, class_idx=None):
        """
        Generates the heatmap for a specific input and target class.

        Args:
            input_tensor (torch.Tensor): Input image tensor.
            class_idx (int, optional): Target class index. If None, uses the predicted class.

        Returns:
            tuple: (heatmap [numpy array], target_class_index [int])
        """
        self.model.eval()
        output = self.model(input_tensor)

        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        # Zero gradients and backward pass to compute gradients for the target class
        self.model.zero_grad()
        target_score = output[:, class_idx]
        target_score.backward()

        # Compute weights (implemented by subclasses)
        weights = self._compute_weights()

        # Weighted summation of feature maps: sum(w_k * A_k)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)

        # Apply ReLU to retain only features that have a positive influence on the class of interest
        cam = F.relu(cam)

        # Cleanup
        self._remove_hooks()

        return cam.squeeze().cpu().numpy(), class_idx


# --- GradCAM Implementation ---
class GradCAM_1(BaseCAM):
    """
    Standard Grad-CAM implementation.
    Reference: Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization".
    """

    def _compute_weights(self):
        # Global Average Pooling (GAP) of gradients over spatial dimensions (H, W)
        return torch.mean(self.gradients, dim=(2, 3), keepdim=True)


# --- GradCAM++ Implementation ---
class GradCAMpp(BaseCAM):
    """
    Grad-CAM++ implementation.
    Reference: Chattopadhay et al., "Grad-CAM++: Generalized Gradient-based Visual Explanations for Deep Convolutional Networks".
    """

    def _compute_weights(self):
        # Compute higher-order derivatives
        grads_power_2 = self.gradients.pow(2)
        grads_power_3 = grads_power_2 * self.gradients

        # Compute sum of activations over spatial dimensions
        sum_activations = torch.sum(self.activations, dim=(2, 3), keepdim=True)

        # Calculate coefficient alpha (pixel-wise weighting)
        alpha_numerator = grads_power_2
        alpha_denominator = 2 * grads_power_2 + sum_activations * grads_power_3 + 1e-10
        alpha = alpha_numerator / alpha_denominator

        # Apply ReLU to gradients (positive gradients indicate positive contribution)
        relu_grads = F.relu(self.gradients)

        # Compute final weights using alpha coefficients
        weights = torch.sum(alpha * relu_grads, dim=(2, 3), keepdim=True)
        return weights


# --- FusionCAM Implementation ---
class FusionCAM(BaseCAM):
    """
    FusionCAM: A specialized visualization method for Multi-Branch/Two-Channel Architectures.

    It decouples the attribution of the target layer (which contains concatenated features)
    back into their original branches (e.g., Mean Path and Trend Path).
    """

    def __init__(self, model, target_layer, num_channels_per_path):
        """
        Args:
            model: The neural network.
            target_layer: Name of the layer where features are concatenated (e.g., last conv layer).
            num_channels_per_path (list): List containing channel counts for each path, e.g., [64, 64].
        """
        super().__init__(model, target_layer)
        self.num_channels_per_path = num_channels_per_path

    def generate_cam(self, input_tensor, class_idx=None):
        self.model.eval()
        output = self.model(input_tensor)

        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        self.model.zero_grad()
        target_score = output[:, class_idx]
        target_score.backward()

        # 1. Compute unified weights using standard Grad-CAM logic (Global Average Pooling)
        unified_weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)

        cams = []
        start_channel = 0
        channel_weights_all = []

        # 2. Core Step: Attribution Decoupling
        # Iterate through defined paths (e.g., Path 1: Trend, Path 2: Mean)
        for num_channels in self.num_channels_per_path:
            # Slice weights and activations corresponding to the specific path
            end_channel = start_channel + num_channels

            weights_path = unified_weights[:, start_channel: end_channel, :, :]
            activations_path = self.activations[:, start_channel: end_channel, :, :]

            # Generate independent heatmap for this path
            # Weighted summation of the specific path's channels
            cam_path = torch.sum(weights_path * activations_path, dim=1, keepdim=True)
            cam_path = F.relu(cam_path)  # Apply ReLU

            cams.append(cam_path.squeeze().cpu().numpy())

            # --- Statistical Analysis of Channel Importance ---
            # 1. Spatial mean
            weights_spatial_mean = weights_path.mean(dim=[2, 3])  # Shape: [B, C]
            # 2. Batch mean (Global importance of each channel in this path)
            weights_global_mean = weights_spatial_mean.mean(dim=0)  # Shape: [C]

            channel_weights_all.append(weights_global_mean.cpu().numpy())

            # Update pointer for the next path
            start_channel += num_channels

        self._remove_hooks()

        # Returns:
        # cams: List of heatmaps [heatmap_path1, heatmap_path2]
        # class_idx: Predicted class
        # channel_weights_all: List of weight vectors for analysis
        return cams, class_idx, channel_weights_all