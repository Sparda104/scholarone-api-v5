# checkpointing.py - V5 FINAL VERSION (Thoroughly Reviewed & Corrected)
"""
Checkpoint management for ScholarOne API operations.
Enhanced with configurable directory paths and better error handling.
"""
import json
import os
from typing import Optional, Any, Dict

class CheckpointManager:
    def __init__(self, logger=None, checkpoint_file: Optional[str] = None):
        """
        Initialize CheckpointManager with optional custom checkpoint file path.

        Args:
            logger: Optional logger instance for logging checkpoint operations
            checkpoint_file: Optional custom path for checkpoint file.
                           If None, uses environment variable or default location.
        """
        self.logger = logger

        # Determine checkpoint file location
        if checkpoint_file is None:
            # Use environment variable or sensible default
            checkpoint_dir = os.environ.get(
                'SCHOLARONE_CHECKPOINT_DIR',
                os.path.join(os.path.expanduser("~"), "ScholarOne_Checkpoints")
            )

            # Create directory if it doesn't exist
            try:
                os.makedirs(checkpoint_dir, exist_ok=True)
            except Exception as ex:
                if self.logger:
                    self.logger.warning(f"Could not create checkpoint directory {checkpoint_dir}: {ex}")
                # Fallback to current directory
                checkpoint_dir = os.getcwd()

            checkpoint_file = os.path.join(checkpoint_dir, "scholarone_checkpoint.json")

        self.checkpoint_file = checkpoint_file

        if self.logger:
            self.logger.debug(f"Checkpoint file: {self.checkpoint_file}")

    def save_checkpoint(self, executor: Any, batch_num: int, total_batches: int) -> None:

    # V5 MULTI-SITE SUPPORT
    # Enhanced for per-site tracking
        """
        Save current processing state to checkpoint file.

        Args:
            executor: EndpointExecutor instance with current state
            batch_num: Current batch number being processed
            total_batches: Total number of batches to process
        """
        state: Dict[str, Any] = {
            "endpoint_id": getattr(executor, "eid", None),
            "params": getattr(executor, "params", None),
            "batch_num": batch_num,
            "total_batches": total_batches,
        }

        try:
            # Ensure directory exists
            checkpoint_dir = os.path.dirname(self.checkpoint_file)
            if checkpoint_dir:
                os.makedirs(checkpoint_dir, exist_ok=True)

            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            if self.logger:
                self.logger.info(f"Checkpoint saved at batch {batch_num}/{total_batches}")

        except Exception as ex:
            if self.logger:
                self.logger.error(f"Checkpoint save failed: {ex}")

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load processing state from checkpoint file.

        Returns:
            Dict containing saved state if checkpoint exists, None otherwise
        """
        try:
            if not os.path.exists(self.checkpoint_file):
                return None

            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                state = json.load(f)

            if self.logger:
                self.logger.info("Checkpoint loaded successfully")

            return state

        except json.JSONDecodeError as ex:
            if self.logger:
                self.logger.error(f"Checkpoint file is corrupted: {ex}")
            return None

        except Exception as ex:
            if self.logger:
                self.logger.error(f"Checkpoint load failed: {ex}")
            return None

    def clear_checkpoint(self) -> None:
        """
        Remove checkpoint file after successful completion.
        """
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)

                if self.logger:
                    self.logger.info("Checkpoint cleared successfully")

        except Exception as ex:
            if self.logger:
                self.logger.error(f"Checkpoint clear failed: {ex}")

    def has_checkpoint(self) -> bool:
        """
        Check if a checkpoint file exists.

        Returns:
            bool: True if checkpoint exists, False otherwise
        """
        return os.path.exists(self.checkpoint_file)

    def get_checkpoint_info(self) -> Optional[str]:
        """
        Get human-readable information about current checkpoint.

        Returns:
            str: Checkpoint information or None if no checkpoint exists
        """
        state = self.load_checkpoint()
        if not state:
            return None

        endpoint_id = state.get("endpoint_id", "Unknown")
        batch_num = state.get("batch_num", 0)
        total_batches = state.get("total_batches", 0)

        return f"Checkpoint: Endpoint {endpoint_id}, Batch {batch_num}/{total_batches}"
