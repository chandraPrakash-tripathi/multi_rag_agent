from data_setup.unified_layer.transformers.neows import NeoWsTransformer
from data_setup.unified_layer.transformers.donki import DonkiTransformer
from data_setup.unified_layer.transformers.eonet import EonetTransformer
from data_setup.unified_layer.transformers.apod import ApodTransformer
from data_setup.unified_layer.transformers.spaceflight import SpaceflightTransformer
from data_setup.unified_layer.transformers.html_docs import HtmlDocsTransformer

# The central mapping framework linking dataset IDs to their execution blocks
TRANSFORMER_REGISTRY = {
    # Structured sources mapping to UnifiedEvent / UnifiedKnowledge
    "neows": NeoWsTransformer,
    "donki": DonkiTransformer,
    "eonet": EonetTransformer,
    "apod": ApodTransformer,
    "spaceflight_news": SpaceflightTransformer,
    # Unstructured HTML sources mapping to UnifiedKnowledge
    "jwst": HtmlDocsTransformer,
    "artemis": HtmlDocsTransformer,
    "hubble": HtmlDocsTransformer,
    "mars": HtmlDocsTransformer,
    "earth_observatory": HtmlDocsTransformer,
}
