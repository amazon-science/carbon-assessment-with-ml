# File containing NAICS codes, text description, corresponding carbon emission per dollar
naics_file_name = 'naics_codes.pkl'

# Product description and annotations by at least 5 workers per product
annotation_file_name = "../data/6k_grocery_products_annotations.pkl"
# annotation_file_name = "../data/40k_products_annotations.pkl"

## ML model configuration
# Models from the following link: https://www.sbert.net/
# Small model, 120MB in size. Use for testing
# model_name = 'paraphrase-MiniLM-L12-v2' 
# Largest model available at the time of writing, 420MB. 
model_name = 'all-mpnet-base-v2' # large model