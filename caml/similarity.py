from sentence_transformers import (
    SentenceTransformer, InputExample, losses, util
)
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np

class MLModel:
    def __init__(self, model_name = 'all-mpnet-base-v2'):
        self.model = SentenceTransformer(model_name)
    
    def compute_similarity_scores(self, product_list, naics_list):
        prod_embeddings = self.model.encode(product_list, convert_to_tensor=True)
        naics_embeddings = self.model.encode(naics_list, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(prod_embeddings, naics_embeddings)
        return cosine_scores

    # Given an product, use model to generate embedding and return the top-20 matched NAICS descriptions
    def rank_similarity_scores(self, df, cosine_scores, product_ix, naics_df):
        sorted_cs, indices = cosine_scores.sort(dim=1, descending=True)
        
        sorted_product_cs = sorted_cs[product_ix].cpu().numpy()
        naics_ix = indices[product_ix].cpu().numpy()
        similarity_scores = pd.DataFrame(index=np.arange(20))
        for i in range(20):
            similarity_scores.loc[i,'cosine_score'] = float("{:.8f}".format(sorted_product_cs[i]))
            similarity_scores.loc[i, 'naics_code'] = naics_df.loc[naics_ix[i], 'naics_code']
            similarity_scores.loc[i, 'naics_desc'] = naics_df.loc[naics_ix[i], 'naics_desc']
            similarity_scores.loc[i, 'naics_title'] = naics_df.loc[naics_ix[i], 'Title']
            
        similarity_scores['product_code'] = df.iloc[product_ix].product_code
        similarity_scores['product_text'] = df.iloc[product_ix].text_clean
        
        return similarity_scores

    def fine_tune(self, train_df, batch_size=16, epochs=5, warmup_steps=100):
        #Define your train dataset, the dataloader and the train loss
        train_examples = [InputExample(texts=[row.naics_desc, row.product_text], label=row.label) for i, row in train_df.iterrows()]
        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
        train_loss = losses.CosineSimilarityLoss(self.model)

        #Tune the model
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)], 
            epochs=epochs,
            warmup_steps=warmup_steps
        )

        


