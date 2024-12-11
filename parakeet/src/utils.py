import ast
import base64
import hashlib
import logging
import os
import re
import uuid
from time import time
import requests

import cohere_aws
import nltk
import numpy as np
import pandas as pd
import rich
import rich.traceback
import torch
from nltk.corpus import stopwords as nltk_stopwords
from prompts import eio_groundtruth_json, process_groundtruth_json
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from sentence_transformers import SentenceTransformer, util
from spacy.lang.en import stop_words as spacy_stopwords
from tqdm import tqdm

torch.manual_seed(0)
np.random.seed(0)

rich.traceback.install(show_locals=False)

nltk.download("stopwords", quiet=True)

logger = logging.getLogger("eifmap")


def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def md5_hash_base64(text):
    md5_hash = hashlib.md5(text.encode()).digest()
    b64_hash = base64.b64encode(md5_hash).decode().replace("=", "")
    return b64_hash


def uuid4_base64():
    return base64.b64encode(uuid.uuid4().bytes).decode().replace("=", "")


def uuid_to_base64(text):
    return ".".join([base64.b64encode(uuid.UUID(x).bytes).decode().replace("=", "") for x in text.split("_")])


def base64_to_uuid(text):
    return "_".join([uuid.UUID(bytes=base64.b64decode(x + "==")).hex for x in text.split(".")])


def preprocess_texts(texts):
    stop_words = spacy_stopwords.STOP_WORDS.union(set(nltk_stopwords.words("english")))

    def clean_and_tokenize(text):
        text = re.sub(r"[^\w\s]", " ", text.lower())
        return [word for word in text.split() if word not in stop_words]

    if isinstance(texts, np.ndarray):
        processed_texts = [clean_and_tokenize(text) for text in texts]
    elif isinstance(texts, str):
        processed_texts = clean_and_tokenize(texts)
    else:
        error_message = "Input must be an np.ndarray or a string."
        raise TypeError(error_message)

    return processed_texts


def get_device():
    if torch.cuda.is_available():
        device = "cuda"
        logger.info("Using GPU to calculate semantic text embedding ...")
    elif torch.backends.mps.is_available():
        device = "mps"
        logger.info("Using MPS to calculate semantic text embedding ...")
    else:
        device = None
        logger.info("Using CPU to calculate semantic text embedding ...")
    return device


class RichProgress:
    def __init__(self, data, disable_progress=False, description="Processing"):
        self.data = data
        self.total_iterations = len(data)
        self.disable_progress = disable_progress
        self.description = description

    def __enter__(self):
        if not self.disable_progress:
            self.progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                TextColumn("[progress.custom] {task.fields[rate]}"),
            )
            self.task: TaskID = self.progress.add_task(
                f"{self.description} (0/{self.total_iterations})",
                total=self.total_iterations,
                rate="",
            )
            self.start_time = time()
            self.progress.start()
            self.last_update_time = time()
        else:
            self.start_time = time()
            self.last_update_time = time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.disable_progress:
            self.progress.stop()

    def update(self, advance=1):
        current_time = time()
        elapsed_time = current_time - self.start_time
        iteration_time = current_time - self.last_update_time
        completed = self.progress.tasks[self.task].completed + advance
        if iteration_time > 1:
            rate = f"{iteration_time:.2f} sec/iteration"
        else:
            iterations_per_second = (completed) / elapsed_time if elapsed_time > 0 else 0
            rate = f"{iterations_per_second:.2f} iterations/sec"

        if not self.disable_progress:
            self.progress.update(
                self.task,
                advance=advance,
                rate=rate,
                description=f"{self.description} ({completed}/{self.total_iterations})",
            )

        self.last_update_time = current_time




def setup_logging(filename="debug.log"):
    logger.setLevel(logging.INFO)

    shell_handler = RichHandler(level=logging.INFO, rich_tracebacks=True, markup=True)
    shell_handler.setFormatter(logging.Formatter("%(message)s"))

    file_handler = logging.FileHandler(filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s"))
    logger.addHandler(shell_handler)
    logger.addHandler(file_handler)

# This ecoinvent_file is the public one (unlicensed). For Parakeet we used the licensed dataset.
def get_ecoinvent_data(ecoinvent_file="https://19913970.fs1.hubspotusercontent-na1.net/hubfs/19913970/Database-Overview-for-ecoinvent-v3.9.1-9.xlsx"):
    res = requests.get(ecoinvent_file)
    excel_data = pd.ExcelFile(res.content, engine='openpyxl')
    eco_df = pd.read_excel(excel_data, sheet_name=2)
    eco_df = eco_df.rename(
        columns={
            'Reference Product Name': 'reference_product',
            'Activity UUID & Product UUID': 'impact_factor_id',
            'Activity Name': 'impact_factor_name',
            'Product Information': 'product_info'
            }
        )
    return eco_df

def get_naics_data(
    useeio_file="https://pasteur.epa.gov/uploads/10.23719/1528686/SupplyChainGHGEmissionFactors_v1.2_NAICS_CO2e_USD2021.csv",
    naics_file="https://www.census.gov/naics/2017NAICS/2017_NAICS_Index_File.xlsx",
):
    useeio_df = pd.read_csv(useeio_file)
    useeio_df = useeio_df[
        [
            "2017 NAICS Code",
            "2017 NAICS Title",
            "Supply Chain Emission Factors with Margins",
            "Reference USEEIO Code",
        ]
    ]
    useeio_df = useeio_df.rename(
        columns={
            "2017 NAICS Code": "naics_code",
            "2017 NAICS Title": "naics_title",
            "Supply Chain Emission Factors with Margins": "co2e_per_dollar",
            "Reference USEEIO Code": "bea_code",
        }
    )
    logger.info(f"Loaded {useeio_df.shape[0]} rows from {useeio_file}")

    naics_df = pd.read_excel(naics_file)
    naics_df = naics_df.rename(
        columns={
            "NAICS17": "naics_code",
            "INDEX ITEM DESCRIPTION": "naics_desc",
        }
    )
    logger.info(f"Loaded {naics_df.shape[0]} rows from {naics_file}")
    naics_df = naics_df.merge(useeio_df, on="naics_code", how="left").dropna()
    naics_df = naics_df.groupby("naics_desc").first().reset_index()
    logger.info(f"Final shape after merge on naics_code: {naics_df.shape}")
    return naics_df


def get_ranked_list(
    text,
    semantic_text_model,
    eco_df,
    eco_ref,
    eco_ref_embedding,
    lca_type,
):
    activity_embedding = semantic_text_model.encode([text], show_progress_bar=False, batch_size=1)
    
    k = 10 if lca_type == "process" else 20
    cosine_scores = util.cos_sim(activity_embedding, eco_ref_embedding) 
    sorted_cs, indices = cosine_scores.sort(dim=1, descending=True)
    topK_sbert = indices.squeeze().numpy()[:k].tolist()
    eco_ix = topK_sbert

    # Create a ranked list for collecting ground truth
    if lca_type == "process":
        topK_df = pd.DataFrame(eco_ref[eco_ix], columns=["reference_product"]).copy(deep=True).reset_index()  
        topK_df["cosine_score"] = sorted_cs.squeeze().numpy()[:k]
        ranked_list = topK_df.reset_index()[["index", "reference_product"]].to_dict("records")  
        topK_df = topK_df.reset_index()[["index", "reference_product"]]
    else:
        topK_df = eco_df.loc[eco_ix].copy(deep=True).reset_index()
        topK_df["cosine_score"] = sorted_cs.squeeze().numpy()[:k]
        ranked_list = topK_df[["index", "naics_title", "naics_desc", "naics_code"]].to_dict("records")

    return ranked_list, topK_df


def prepare_eio_json(entry, clean_text, response, uniq_id):
    if len(response) < 1:
        error_message = "Response length must be greater than 1."
        raise ValueError(error_message)
    gt_json = eio_groundtruth_json
    gt_json["source"] = "*Business Activity*: {}\n".format(re.sub(r"[^\w\s]", "", entry))
    gt_json["source"] += f"*AI paraphrased description:* {clean_text}\n\n"

    gt_json["source"] += f"*AI top choice:* {response[0]['naics_title']} ({response[0]['naics_code']})\n"
    gt_json["source"] += f"Justification: {response[0]['justification']}\n\n"
    
    if len(response) > 1:
        gt_json["source"] += f"*AI second choice:* {response[1]['naics_title']} ({response[1]['naics_code']})\n"
        gt_json["source"] += f"Justification: {response[1]['justification']}\n\n"

    gt_json["formConfig"]["fields"][0]["id"] = uniq_id
    gt_json["formConfig"]["fields"][0]["options"] = pd.concat(
        [
            pd.DataFrame(response).drop("justification", axis=1).rename(columns={"naics_code": "value", "naics_title": "label"}),
            pd.DataFrame(
                [
                    {"label": "Not sure", "value": "-1"},
                    {"label": "EIF options are inappropriate, no match", "value": "-2"},
                    {"label": "Activity description is unclear to select an EIF", "value": "-3"},
                ]
            ),
        ]
    ).to_dict("records")

    return gt_json


def prepare_process_json(activity_text, response, sel_eco, uniq_id):
    gt_json = process_groundtruth_json
    gt_json["source"] = "*Given description:* {}\n".format(re.sub(r"[^\w\s]", "", activity_text))

    gt_json["source"] += "\n*AI top choice:* {}\n".format(response[0]["impact_factor_name"])
    gt_json["source"] += f"\nJustification: {response[0]['justification']}"

    if len(response) > 1:
        gt_json["source"] += "\n\n*AI next choice:* {}\n".format(response[1]["impact_factor_name"])
        gt_json["source"] += f"\nJustification: {response[1]['justification']}"

    gt_json["formConfig"]["fields"][0]["id"] = uniq_id
    
    gt_json["formConfig"]["fields"][0]["options"] = pd.concat(
    [
        sel_eco[["impact_factor_name", "impact_factor_id"]].rename(columns={"impact_factor_id": "value", "impact_factor_name": "label"}),
        pd.DataFrame(
            [
                {"label": "None of the impact factors match", "value": "0"},
                {"label": "Not sure", "value": "-1"},
                {"label": "Activity text unclear for selection", "value": "-3"},
            ]
        ),
    ]
    ).to_dict("records")
    return gt_json


def read_activities(
    activity_file,
    activity_col,
    start_idx,
    end_idx,
    sheet_name=0,
):
    logger.info(f"Reading {activity_file}")
    _, file_extension = os.path.splitext(activity_file)
    if file_extension == ".csv":
        activity_df = pd.read_csv(activity_file)
    elif file_extension == ".xlsx":
        activity_df = pd.read_excel(activity_file)
    else:
        error_message = f"Unsupported file extension: {file_extension}"
        raise ValueError(error_message)

    activity_df = activity_df.fillna("").reset_index(drop=True).drop_duplicates()
    logger.info(f"Read {len(activity_df)} activities")
    logger.info(f"Will be processing between index {start_idx} and {end_idx}")

    if activity_col == "auto":
        # use all activity columns
        activity_col = activity_df.columns.to_list()
        logger.info(f"Using all of the columns from the dataset: {activity_col}")
    else:
        activity_col = ast.literal_eval(activity_col)
        logger.info(f"User provided the following activity columns: {activity_col}")
    sliced_df = activity_df.iloc[start_idx:end_idx][activity_col]
    activity_df = activity_df.iloc[start_idx:end_idx]

    return sliced_df, activity_df


class CohereEmbedding:  
    def __init__(self, model_id) -> None:
        self.co = cohere_aws.Client(mode=cohere_aws.Mode.BEDROCK, region_name="us-west-2")
        self.model_id = model_id

    def encode(self, data: pd.Series | list, *, show_progress_bar=False, batch_size=32):  
        if isinstance(data, pd.Series):
            data = data.to_list()
        elif isinstance(data, np.ndarray):
            data = list(data)

        if not isinstance(data, list):
            error_message = "Input must be a list of strings"
            raise TypeError(error_message)
        if batch_size > 1:
            eco_ref_embedding = []
            for i in tqdm(range(0, len(data), batch_size), disable=False):
                eco_ref_embedding.append(np.array(self.co.embed(texts=data[i : min(len(data), i + batch_size)], input_type="clustering", model_id=self.model_id).embeddings))  # noqa: PERF401
            eco_ref_embedding = np.concatenate(eco_ref_embedding)
            if eco_ref_embedding.shape[0] != len(data):
                error_message = "Mismatch in embedding size"
                raise ValueError(error_message)
            return eco_ref_embedding
        return np.array(self.co.embed(texts=data, input_type="clustering", model_id=self.model_id).embeddings)


def get_cached_embedding(eco_ref, embedding):
    
    if embedding.startswith("cohere"):
        logger.info("Using Cohere model from BedRock for semantic text embedding ...")
        semantic_text_model = CohereEmbedding(embedding)
    else:
        semantic_text_model = SentenceTransformer(embedding, device=get_device())
        semantic_text_model = torch.compile(semantic_text_model, mode="reduce-overhead")

    cache_id = md5_hash(f"{embedding}+{str(eco_ref.tolist())!s}")
    cache_file = f"/tmp/{cache_id}.pt"
    if os.path.exists(cache_file):
        logger.info("Loading cached embeddings")
        eco_ref_embedding = torch.load(cache_file)
    else:
        logger.info("Encoding embedding")
        eco_ref_embedding = semantic_text_model.encode(
            eco_ref,
            show_progress_bar=True,
            batch_size=32,
        )
        torch.save(eco_ref_embedding, cache_file)
    return semantic_text_model, eco_ref_embedding
