from script.models.preprocessing import load_all_snapshots

class PreProcessingService:
    """Service class for data loading and preprocessing"""

    @staticmethod
    def load_all_data():
        """Load and preprocess all snapshot data."""
        return load_all_snapshots()
