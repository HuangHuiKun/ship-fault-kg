# Full Script: Training + Validation + Testing + Visualization Pipeline

import torch
import torch.utils.data as data_utils
from sklearn.model_selection import KFold
from Code.Test_12 import DPFD_ACAM_ISimAM_TwoChannelFusion  # Import custom model
from Code.Test_12_1 import read_data  # Import data loading utility
from Code.config import *  # Import hyperparameters (Batch_size, Learn_rate, etc.)


# ======================================================================================================================
# ---------- Training Function ---------- #
def train(model, dataloader, criterion, optimizer, device):
    """
    Executes one epoch of training.

    Args:
        model (nn.Module): The neural network model.
        dataloader (DataLoader): Iterator for the training dataset.
        criterion (Loss): The loss function (e.g., CrossEntropyLoss).
        optimizer (Optimizer): Optimization algorithm (e.g., Adam).
        device (torch.device): Computing device (CPU or GPU).

    Returns:
        float: Average training loss for the epoch.
        float: Training accuracy for the epoch.
    """
    model.train()  # Set model to training mode (enables Dropout, BatchNorm updates)
    total_loss, correct, total = 0, 0, 0

    for x, y in dataloader:
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()  # Clear previous gradients
        outputs = model(x)  # Forward pass
        loss = criterion(outputs, y)  # Compute loss
        loss.backward()  # Backward pass (compute gradients)
        optimizer.step()  # Update model parameters

        # Metrics accumulation
        total_loss += loss.item() * x.size(0)
        correct += (outputs.argmax(1) == y).sum().item()
        total += y.size(0)

    return total_loss / total, correct / total


# ======================================================================================================================
# ---------- Evaluation Function ---------- #
def evaluate(model, dataloader, criterion, device):
    """
    Evaluates the model on Validation or Test sets.

    Args:
        model (nn.Module): The neural network model.
        dataloader (DataLoader): Iterator for validation/test dataset.
        criterion (Loss): The loss function.
        device (torch.device): Computing device.

    Returns:
        float: Average loss.
        float: Accuracy.
        torch.Tensor: All predicted labels.
        torch.Tensor: All true labels.
        torch.Tensor: Raw model outputs (logits/features) for visualization.
    """
    model.eval()  # Set model to evaluation mode (disables Dropout, BatchNorm updates)
    total_loss, correct, total = 0, 0, 0
    all_preds, all_labels, all_features = [], [], []

    with torch.no_grad():  # Disable gradient calculation for efficiency
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)

            outputs = model(x)
            loss = criterion(outputs, y)

            total_loss += loss.item() * x.size(0)
            preds = outputs.argmax(1)
            correct += (preds == y).sum().item()
            total += y.size(0)

            # Store results for analysis/visualization
            all_preds.append(preds.cpu())
            all_labels.append(y.cpu())
            all_features.append(outputs.cpu())

    return (total_loss / total,
            correct / total,
            torch.cat(all_preds),
            torch.cat(all_labels),
            torch.cat(all_features))


# ======================================================================================================================
# ---------- Main Execution Block ---------- #
if __name__ == "__main__":

    # --- Option 1: K-Fold Cross-Validation (Robustness Check) ---
    # Use this section to verify model stability across different data splits.
    """
    best_val_acc_overall = 0.0
    from torch.utils.data import ConcatDataset, DataLoader

    # 1. Load Data
    train_loader_raw, val_loader_raw, test_loader_raw = read_data(Batch_size)
    # Combine datasets for K-Fold splitting
    dataset = ConcatDataset([train_loader_raw.dataset, val_loader_raw.dataset])

    k = 5
    kf = KFold(n_splits=k, shuffle=True, random_state=42)

    for fold, (train_idx, val_idx) in enumerate(kf.split(dataset)):
        print(f"Starting fold {fold + 1}/{k}...")

        # Create samplers for current fold
        train_sampler = data_utils.SubsetRandomSampler(train_idx)
        val_sampler = data_utils.SubsetRandomSampler(val_idx)

        train_loader = data_utils.DataLoader(dataset, batch_size=Batch_size, sampler=train_sampler)
        val_loader = data_utils.DataLoader(dataset, batch_size=Batch_size, sampler=val_sampler)

        # Re-initialize model and optimizer for each fold to ensure independence
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = CNN_CBAM_SimAM_TwoChannelFusion(In_channels, Conv_channels, Cbam_reduction).to(device)

        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=Learn_rate, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.7)

        # Metrics storage
        train_losses, val_losses, test_losses = [], [], []
        train_accs, val_accs, test_accs = [], [], []
        # Note: In K-Fold, we usually care about Val metrics, but Test metrics can be logged if external test set exists.

        best_val_acc_this_fold = 0.0

        # Training Loop
        for epoch in range(1, num_epochs):
            train_loss, train_acc = train(model, train_loader, criterion, optimizer, device)
            val_loss, val_acc, val_pred, val_label, val_feat = evaluate(model, val_loader, criterion, device)
            # Optional: Evaluate on external test set
            # test_loss, test_acc, test_pred, test_label, test_feat = evaluate(model, test_loader_raw, criterion, device)

            if val_acc > best_val_acc_this_fold:
                best_val_acc_this_fold = val_acc

            train_losses.append(train_loss)
            val_losses.append(val_loss)
            train_accs.append(train_acc)
            val_accs.append(val_acc)

            print(f"Fold {fold + 1}, Epoch {epoch}: Train Acc={train_acc:.4f}, Val Acc={val_acc:.4f}")
            scheduler.step()

        # Save best model overall folds
        if best_val_acc_this_fold > best_val_acc_overall:
            best_val_acc_overall = best_val_acc_this_fold
            print(f"✅ New global best model found on Fold {fold + 1} with Val Acc = {val_acc:.4f}")
            # Save logic here...
    """

    # --- Option 2: Standard Training (Hold-out Validation) ---
    # Standard pipeline: Train -> Validate -> Test

    # 1. Load Data
    train_loader, val_loader, test_loader = read_data(Batch_size)

    # 2. Setup Device, Model, Loss, Optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DPFD_ACAM_ISimAM_TwoChannelFusion(In_channels, Conv_channels, Cbam_reduction).to(device)

    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=Learn_rate, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.7)

    # 3. Initialize Metric Loggers
    train_losses, val_losses, test_losses = [], [], []
    train_accs, val_accs, test_accs = [], [], []

    # 4. Training Loop
    print(f"Starting training on device: {device}")
    for epoch in range(1, num_epochs + 1):  # Adjusted range to be inclusive if needed
        # A. Training Phase
        train_loss, train_acc = train(model, train_loader, criterion, optimizer, device)

        # B. Validation Phase
        val_loss, val_acc, val_pred, val_label, val_feat = evaluate(model, val_loader, criterion, device)

        # C. Testing Phase
        test_loss, test_acc, test_pred, test_label, test_feat = evaluate(model, test_loader, criterion, device)

        # D. Logging
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        test_losses.append(test_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)
        test_accs.append(test_acc)

        print(f"Epoch {epoch}/{num_epochs}: "
              f"Train Acc={train_acc:.4f}, Val Acc={val_acc:.4f}, Test Acc={test_acc:.4f} | "
              f"Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Test Loss={test_loss:.4f}")

        scheduler.step()

        # E. Checkpoint Saving
        # Saving the model state and all metrics for post-training analysis (e.g., confusion matrix, t-SNE)
        model.eval()
        torch.save({
            'train_loss': train_losses,
            'train_acc': train_accs,
            'val_loss': val_losses,
            'val_acc': val_accs,
            'val_preds': val_pred,
            'val_labels': val_label,
            'val_feats': val_feat,  # Features for t-SNE visualization
            'test_loss': test_losses,
            'test_acc': test_accs,
            'test_preds': test_pred,
            'test_labels': test_label,
            'test_feats': test_feat,
            'model_state_dict': model.state_dict()
        }, f"../model/best_model_{Model_id}.pth")

    print(f"Training completed. Model saved to ../model/best_model_{Model_id}.pth")