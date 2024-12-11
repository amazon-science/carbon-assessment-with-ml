import ast
import json
import logging
import os
from copy import deepcopy
from datetime import datetime, timezone

import click
import nltk
import pandas as pd
import prompts
import rich
import rich.traceback
from assistant import LCAAssistant

from utils import (
    RichProgress,
    get_cached_embedding,
    get_naics_data,
    get_ecoinvent_data,
    get_ranked_list,
    md5_hash_base64,
    prepare_eio_json,
    prepare_process_json,
    preprocess_texts,
    read_activities,
    setup_logging,
)
from functools import partial

rich.traceback.install(show_locals=False)
nltk.download("stopwords", quiet=True)

logger = logging.getLogger("eifmap")


@click.command()
@click.option(
    "--llm_model",
    help="The LLM model to generate ranked predictions for.",
    default="anthropic.claude-3-sonnet-20240229-v1:0",
)
@click.option(
    "--activity_file",
    help="The activity file to generate ranked predictions for.",
    default="recipe_ingredients_1956.csv",
)
@click.option(
    "--activity_col",
    help="The activity column to use for the LLM model.",
    default="auto",
)
@click.option(
    "--reference_file",
    help="The reference file to use for the LLM model.",
    default="https://19913970.fs1.hubspotusercontent-na1.net/hubfs/19913970/Database-Overview-for-ecoinvent-v3.9.1-9.xlsx",
)
@click.option(
    "--embedding",
    help="The embedding to use for the LLM model.",
    default="thenlper/gte-large",
)
@click.option("--verbose", help="Print verbose output.", is_flag=True, default=False)
@click.option("--start_idx", help="Start index for the activity file.", default=0, type=int)
@click.option("--end_idx", help="End index for the activity file.", default=None, type=int)
@click.option(
    "--output_file",
    help="The output file to write the ranked predictions to.",
    default="ranked_preds",
)
@click.option(
    "--lca_type",
    help="The LCA type to use for the LLM model [process/eio]",
    default="process",
)
@click.option(
    "--no_progress_bar",
    help="Don't show the progress bar.",
    is_flag=True,
    default=False,
)
@click.option(
    "--useeio_file",
    help="NAICS to CO2e mapping file.",
    default="https://pasteur.epa.gov/uploads/10.23719/1528686/SupplyChainGHGEmissionFactors_v1.2_NAICS_CO2e_USD2021.csv",
)
@click.option(
    "--naics_file",
    help="List of NAICS",
    default="https://www.census.gov/naics/2017NAICS/2017_NAICS_Index_File.xlsx",
)
@click.option(
    "--sheet_name",
    help="Sheet name from the input file",
    type=str,
    default="Sheet1",
)
@click.option(
    "--reference_filter",
    help="Filter the reference file based on the given database",
    default="ecoinvent, cut-off system; v3.9.1; 2022; www.ecoinvent.org",
)
@click.option(
    "--paraphrasing",
    help="Needs paraphrasing",
    default=True,
)

def main(
    llm_model,
    activity_file,
    activity_col,
    reference_file,
    reference_filter,
    embedding,
    verbose,
    start_idx,
    end_idx,
    output_file,
    lca_type,
    no_progress_bar,
    useeio_file,
    naics_file,
    sheet_name,
    paraphrasing
):
    setup_logging(output_file + ".log")

    if verbose:
        logger.setLevel(logging.INFO)
    if os.environ.get("PYTHONBREAKPOINT", None) != "0":
        no_progress_bar = True

    # same logic for process and eio
    activity_df, full_df = read_activities(activity_file, activity_col, start_idx, end_idx, sheet_name)

    if lca_type == "process":
        logger.info(f"Reading reference data from {reference_file}")
        eco_df = get_ecoinvent_data(reference_file)
        if len(eco_df) != len(eco_df["impact_factor_id"].unique()):
            error_message = "The length of 'df' is not equal to the length of 'impact_factor_id' unique values."
            raise AssertionError(error_message)

        logger.info(f"Loaded {len(eco_df)} reference entries from {reference_file}")

        eco_ref = eco_df["reference_product"].unique()
        logger.info(
            f"Unique reference products: {len(eco_df['reference_product'].unique())}\nUnique impact factors: {len(eco_df['impact_factor_name'].unique())}"
        )
    else:
        eco_df = get_naics_data(useeio_file, naics_file)
        eco_ref = eco_df["naics_desc"].unique() 
        logger.info(f"Number of NAICS descriptions: {len(eco_ref)}")

    semantic_text_model, eco_ref_embedding = get_cached_embedding(eco_ref, embedding)


    lca_assistant = LCAAssistant(llm_model=llm_model)

    gt_json_list = []
    if os.path.exists(output_file + ".jsonl"):
        with open(output_file + ".jsonl", "r") as jsonfile:
            gt_json_list = [json.loads(line) for line in jsonfile]

    activity_maps = pd.read_csv(output_file + ".csv") if os.path.exists(output_file + ".csv") and os.path.getsize(output_file + ".csv") > 0 else pd.DataFrame()
    
    if len(gt_json_list) != len(activity_maps):
        error_message = "Length of gt_json_list is not equal to the length of activity_maps."
        raise AssertionError(error_message)
    if gt_json_list and not activity_maps["id"].isin([x["formConfig"]["fields"][0]["id"] for x in gt_json_list]).all():
        error_message = "Activity maps do not contain all the ids from gt_json_list."
        raise AssertionError(error_message)

    impact_factor_keys = (
        [
            "impact_factor_name",
            "impact_factor_id",
            "reference_product",
        ]
        if lca_type == "process"
        else [
            "naics_code",
            "naics_title",
            "co2e_per_dollar",
            "bea_code",
        ]
    )
    activity_range = range(0, len(activity_df))

    activity_col = ast.literal_eval(activity_col)

    with open(output_file + ".jsonl", "a") as jsonfile, open(output_file + ".csv", "a") as csvfile, RichProgress(
        activity_range,
        disable_progress=no_progress_bar,
        description="Processing activities:",
    ) as progress:
        for activity_ix in activity_range:
            with pd.option_context("display.max_colwidth", None):
                entry = activity_df.iloc[activity_ix]
                entry_full = full_df.iloc[activity_ix]
                activity_item = entry.to_string()

            uniq_id = md5_hash_base64(json.dumps(entry.to_dict()))
            logger.info(f"({activity_ix}/{len(activity_df)}) {uniq_id}")
            if len(activity_maps) > 0 and len(gt_json_list) > 0 and len(activity_maps[activity_maps["id"] == uniq_id]) > 0 and uniq_id in [x["formConfig"]["fields"][0]["id"] for x in gt_json_list]:
                logger.info("Skipping already processed activity")
                if not no_progress_bar:
                    progress.update()
                continue

            if lca_type == "process":
                full_text = activity_item
                logger.info(f"Item description:\n{activity_item}")
                if paraphrasing:
                    clean_text = lca_assistant(
                        text=prompts.text_clean_prompt.format(activity_item),
                        format="text",
                        reset_mem=True,
                    )
                    
                    logger.info(f"Cleaned text: {clean_text}")
                    full_text = clean_text
                    

                ranked_list, topK_df = get_ranked_list(
                    full_text,
                    semantic_text_model,
                    eco_df,
                    eco_ref,
                    eco_ref_embedding,
                    lca_type,
                )

                logger.info(f"Top reference products ({len(ranked_list)}): {ranked_list}")
                
                ref_prod_response = lca_assistant(
                    text=prompts.reference_prods_prompt.format(full_text, ranked_list),
                    reset_mem=True,
                    format="python",
                )
                logger.info(f"LLM re-ranked ({len(ref_prod_response)}): {ref_prod_response}")
                top_ref_prods = pd.DataFrame(ref_prod_response)

                # NOTE: In the licenced Ecoinvent dataset, use "process_technology" and "process_description" instead of "product_info"
                # ref_cols = ["impact_factor_name", "reference_product", "process_technology", "process_description"] 
                ref_cols = ["impact_factor_name", "reference_product", "product_info"] 

                # This ensures that top impact_factors from top reference products comes first
                sel_eco = []

                for x in top_ref_prods["reference_product"].to_list():
                    sel_eco.append(eco_df[eco_df["reference_product"] == x]) 
                sel_eco = pd.concat(sel_eco)

                sel_eco = sel_eco.drop_duplicates(subset=["impact_factor_name"]) 
                sel_eco_list = sel_eco[ref_cols].to_dict("index")

                def validation_fn(response, sel_eco):
                    index_check = pd.Series([x["index"] for x in response if x["index"] is not None]).isin(sel_eco.index).all()
                    error_message = f"One of the indices is not in range. Returned indices: {[x['index'] for x in response]}. Valid indices: {[*sel_eco.index.to_list(), None]}"
                    if response == "":
                        raise ValueError("Returned an empty message, try again to return a response in the format of a list of python dictionaries as I told you.")
                    if not index_check:
                        raise ValueError(error_message)
                    if not all(set(x.keys()) == {"index", "justification", "impact_factor_name"} for x in response):
                        error_message = "Each dictionary in the list must have all three keys: 'index', 'justification', 'impact_factor_name'"
                        raise ValueError(error_message)                
                
                # For the licenced Ecoinvent dataset wich includes "process_technology" and "process_description", use best_eif_prompt 
                best_eif_response = lca_assistant(
                    text=prompts.best_eif_in_unlicensed_ecoinvent_prompt.format(full_text, sel_eco_list),
                    reset_mem=True,
                    format="python",
                    validation_fn=partial(validation_fn, sel_eco=sel_eco),
                )
                

                candidates = sel_eco[["impact_factor_name", "reference_product"]].to_dict("records")
                logger.info(f"Candidate Impact factors ({len(candidates)}): {sel_eco_list}")
                logger.info(f"LLM Response for EIF ({len(best_eif_response)}): {best_eif_response}")

                
                eif_id = best_eif_response[0]["index"]
                
                if eif_id is None:
                    impact_factor_details = {k: None for k in impact_factor_keys}
                else:
                    best_eif = sel_eco.loc[eif_id]
                    impact_factor_details = best_eif[impact_factor_keys].to_dict()
                
                gt_json = prepare_process_json(activity_item, best_eif_response, sel_eco, uniq_id)
                

            else:
                logger.info(f"Item description:\n{activity_item}")
                full_text = activity_item
                if paraphrasing:
                    clean_text = lca_assistant(
                        text=prompts.text_clean_prompt_eio.format(activity_item),
                        format="text",
                        reset_mem=True,
                    )
                
                    logger.info(f"Cleaned text: {clean_text}")
                    full_text = clean_text

                ranked_list, topK_df = get_ranked_list(
                    full_text,
                    semantic_text_model,
                    eco_df,
                    eco_ref,
                    eco_ref_embedding,
                    lca_type,
                )
                
                logger.info(f"Top {len(ranked_list)} NAICS: {ranked_list}")
               
                try:
                    naics_response = lca_assistant(
                        text=prompts.eio_reranker_prompt.format(full_text, ranked_list),
                        reset_mem=True,
                        format="python",
                    )
                    logger.info(f"LLM re-ranked ({len(naics_response)}): {naics_response}")
                except:
                    logger.warning(f"No NAICS found for {activity_item}")
                    continue
                
                best_naics_code = naics_response[0]["naics_code"]

                best_naics = eco_df[eco_df["naics_code"] == best_naics_code]
                if best_naics.empty:
                    logger.warning(f"No NAICS found for {best_naics_code}")
                    if not no_progress_bar:
                        progress.update()
                    continue

                impact_factor_details = best_naics[impact_factor_keys].drop_duplicates().to_dict("records")[0]
                gt_json = prepare_eio_json(activity_item, full_text, naics_response, uniq_id)

            summary_df = pd.DataFrame(
                [
                    {
                        **entry_full.to_dict(),
                        **{
                            "id": uniq_id,
                            "activity": activity_item,
                            **impact_factor_details,
                            "justification": (best_eif_response[0]["justification"] if lca_type == "process" else naics_response[0]["justification"]),
                            "EIF dataset": (reference_filter if lca_type == "process" else "USEEIO v2.0, SupplyChainGHGEmissionFactors_v1.2"),
                            "mapping_strategy": "EIFMap v1.2+re-ranker",
                            "datetime": datetime.now(timezone.utc).strftime("%Y-%m-%d"),  
                        },
                    }
                ]
            )

            json.dump(gt_json, jsonfile)
            jsonfile.write("\n")

            summary_df.to_csv(
                csvfile,
                header=activity_maps.empty,
                index=False,
                mode="a",
            )

            gt_json_list += [deepcopy(gt_json)]
            activity_maps = pd.concat([activity_maps, summary_df], ignore_index=True)
            logger.info("-" * 96)
            if activity_ix % 10 == 0:
                jsonfile.flush()
                csvfile.flush()
            if not no_progress_bar:
                progress.update()


if __name__ == "__main__":
    main()
