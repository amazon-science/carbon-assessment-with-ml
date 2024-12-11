#!/bin/zsh
LCA_TYPE="eio"
ACTIVITY_FILE="../data/raw/invoices_donut.csv"
ACTIVITY_COL="['item_desc']"
OUTPUT_FILE="../data/predictions/parakeet_eioLCA_invoices_dataset_preds"
export AWS_PROFILE="AWS_Account_Name" 
export AWS_REGION="AWS_Region" 



echo "Running..."
python ../src/eifmapnext/generate_ranked_preds.py --verbose --lca_type "$LCA_TYPE" \
--activity_file "$ACTIVITY_FILE" --activity_col "$ACTIVITY_COL" \
--output_file "$OUTPUT_FILE" \
--sheet_name "$SHEET_NAME"\