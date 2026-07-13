# What this accomplishes:
# Interface Segregation: It establishes a clear type hint contract. It will instantly know that any new connector added in
# the future must accept a file path and output a list of your unified models.

# Plug-and-Play Extensibility: This allows the central processing engine to loop over any file and execute .transform()
# without ever needing to know what specific dataset it is working on.
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union
from data_setup.unified_layer.models import UnifiedEvent, UnifiedKnowledge


class BaseTransformer(ABC):
    """
    Abstract Base Class enforcing the architectural contract for all data source adapters.
    Every custom transformer must inherit from this and implement the transform method.
    """

    @abstractmethod
    def transform(self, file_path: Path) -> List[Union[UnifiedEvent, UnifiedKnowledge]]:
        """
        Reads a raw file from local storage (Bronze layer) and transforms it into
        a list of database-ready unified Silver layer objects.

        Args:
            file_path (Path): Path to the raw archived file on disk.

        Returns:
            List[Union[UnifiedEvent, UnifiedKnowledge]]: Cleaned and validated database records.
        """
        pass
