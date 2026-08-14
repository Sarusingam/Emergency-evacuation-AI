"""
Train Model — Train crowd counting model on datasets.
"""

import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("train")

    print("=" * 50)
    print("  Crowd Counting Model Training")
    print("=" * 50)

    try:
        import torch
    except ImportError:
        print("❌ PyTorch not installed. Install with: pip install torch torchvision")
        return

    from models.crowd_model import CrowdCountingCNN
    from models.model_manager import ModelManager

    model = CrowdCountingCNN()
    manager = ModelManager()

    print(f"Model: CrowdCountingCNN")
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total_params:,}")

    # Check for available datasets
    from datasets.dronecrowd_loader import DroneCrowdLoader
    from datasets.nwpu_loader import NWPUCrowdLoader
    from datasets.ucf_qnrf_loader import UCFQNRFLoader

    loaders = [
        ("DroneCrowd", DroneCrowdLoader()),
        ("NWPU-Crowd", NWPUCrowdLoader()),
        ("UCF-QNRF", UCFQNRFLoader()),
    ]

    available = [(n, l) for n, l in loaders if l.is_available()]

    if not available:
        print("\n⚠️  No datasets found. Download one of:")
        for name, loader in loaders:
            info = loader.get_info()
            print(f"   - {name}: Place in {info['root_dir']}")
        print("\nFor now, creating a dummy training run to test the pipeline...")

        # Dummy training
        import torch.nn as nn
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        criterion = nn.MSELoss()

        model.train()
        for epoch in range(3):
            dummy_input = torch.randn(2, 3, 256, 256)
            dummy_target = torch.randn(2, 1, 256, 256).abs()
            output = model(dummy_input)
            loss = criterion(output, dummy_target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            print(f"  Epoch {epoch + 1}/3 — Loss: {loss.item():.4f}")

        manager.save_model(model, "crowd_model_dummy",
                          metadata={"epochs": 3, "dataset": "dummy"})
        print("✅ Dummy model saved!")
    else:
        print(f"\nFound {len(available)} dataset(s):")
        for name, _ in available:
            print(f"  ✅ {name}")
        print("\n(Full training pipeline available — implement custom training loop)")


if __name__ == "__main__":
    main()
