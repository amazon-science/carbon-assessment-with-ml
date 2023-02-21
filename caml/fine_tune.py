#%%
# standard libs
import os

# installed packages
import pandas as pd
from tqdm import tqdm

from sklearn.metrics import mean_absolute_percentage_error as mape
from sklearn.metrics import r2_score

# custom packages
from caml.datasets import AnnotationDataset, NAICSDataset, ProductDataset
from caml import config
from caml.similarity import MLModel


#%%
annotation_data = AnnotationDataset(config.annotation_bucket, config.annotation_prefix)

#%%
naics_file_path = os.path.join('s3://', config.data_bucket, 
                        config.project_folder_name, config.naics_file_name)
naics_data = NAICSDataset(naics_file_path)

#%%
# create asin dataset
product_file_path = os.path.join('s3://',config.data_bucket, 
                        config.project_folder_name, config.asin_file_name)
product_data = ProductDataset(product_file_path, 
                        product_group='gl_grocery', # restricting to grocery products
                        marketplace_id=1, # restricting to US marketplace
                        top_shipped=50, # restricting to top shipped ASINs
                        )    

#%%
mturk_df = annotation_data.annotation_df.merge(
                naics_data.naics_df[['naics_code','eio_co2']], 
                left_on='naics_code', right_on='naics_code', how='left')
mturk_df = mturk_df.drop_duplicates()

#%%
model = MLModel(config.model_name)
asin_list = product_data.df_product.text_clean.values
naics_list = naics_data.naics_df.text_clean.values
cosine_scores = model.compute_similarity_scores(asin_list, naics_list)

#%%
# Clear the evaluation dataframes where results will be stored.
# You can choose to comment this cell after each fold to accumulate the results in one dataframe
evaluation_df = pd.DataFrame()
top5_df = pd.DataFrame()

#%%
## Evaluate the ASINs in the test set
# Aggregate the top-20 NAICS descriptions by NAICS codes. Save the top-5. 
for ix in tqdm(range(len(product_data.df_product))):
    similarity_score = model.rank_similarity_scores(product_data.df_product, cosine_scores, ix, naics_data.naics_df)
    aggregated_scores = similarity_score.groupby('naics_code').first()
    aggregated_scores['votes'] = similarity_score.groupby('naics_code').size()
    aggregated_scores = aggregated_scores.sort_values(['cosine_score', 'votes'], ascending=False).reset_index()
    evaluation_df = pd.concat([evaluation_df, aggregated_scores.head(1)])
    top5_df = pd.concat([top5_df, aggregated_scores.head(5)])


#%%
full_df = mturk_df.merge(top5_df, left_on='asin_code', right_on='asin_code', how='left')
print(full_df.shape)
full_df.head()

#%%
full_df['label'] = (full_df.naics_code_x == full_df.naics_code_y).astype('float')
full_df = full_df[['asin_code','asin_text','naics_code_x', 'naics_desc', 'label']].dropna()
full_df.head()

#%%
# Doing a four fold cross-validation. Each fold is trained and evaluated manually, one fold at a time. 
# Can automate this to reduce manual effort.

## fold 1
# train_df = full_df.iloc[:int(0.75*len(full_df))]
# test_df = full_df.iloc[int(0.75*len(full_df)):]
## fold 2
# train_df = pd.concat([full_df.iloc[:int(0.25*len(full_df))], full_df.iloc[:int(0.5*len(full_df))]])
# test_df = full_df.iloc[int(0.25*len(full_df)): int(0.5*len(full_df))]
## fold 3
# train_df = pd.concat([full_df.iloc[:int(0.5*len(full_df))], full_df.iloc[:int(0.75*len(full_df))]])
# test_df = full_df.iloc[int(0.5*len(full_df)): int(0.75*len(full_df))]
## fold 4
train_df = full_df.iloc[int(0.25*len(full_df)):]
test_df = full_df.iloc[:int(0.25*len(full_df))]
train_df.shape, test_df.shape

#%%
model.fine_tune(train_df)

#%%
# Clear the evaluation dataframes where results will be stored.
# You can choose to comment this cell after each fold to accumulate the results in one dataframe
eval_ft_df = pd.DataFrame()
top5_ft_df = pd.DataFrame()

#%%
## Evaluate the ASINs in the test set
# Aggregate the top-20 NAICS descriptions by NAICS codes. Save the top-5. 
test_df = test_df[test_df.label == 1]
test_df = test_df.groupby('asin_code').first().reset_index()
test_df = test_df.rename(columns={'asin_code': 'parent_asin', 
                                  'asin_text': 'text_clean', 
                                  'naics_code_x': 'naics_code'})

naics_list = naics_data.naics_df.text_clean.to_list()
asin_list = test_df.text_clean.values
cosine_scores = model.compute_similarity_scores(asin_list, naics_list)

#%%
## Evaluate the ASINs in the test set
# Aggregate the top-20 NAICS descriptions by NAICS codes. Save the top-5. 
for ix in tqdm(range(len(test_df))):
    similarity_score = model.rank_similarity_scores(test_df, cosine_scores, ix, naics_data.naics_df)
    aggregated_scores = similarity_score.groupby('naics_code').first()
    aggregated_scores['votes'] = similarity_score.groupby('naics_code').size()
    aggregated_scores = aggregated_scores.sort_values(['cosine_score', 'votes'], ascending=False).reset_index()
    eval_ft_df = pd.concat([eval_ft_df, aggregated_scores.head(1)])
    top5_ft_df = pd.concat([top5_ft_df, aggregated_scores.head(5)])
len(eval_ft_df)

#%%
## Compute the top-1 accuracy of the model
# adf = test_df.rename(columns={'parent_asin': 'asin_code'})
adf = full_df.rename(columns={'naics_code_x': 'naics_code'})
adf = adf.merge(naics_data.naics_df[['naics_code','eio_co2']], left_on='naics_code', right_on='naics_code', how='left')

edf = eval_ft_df.merge(naics_data.naics_df[['naics_code','eio_co2']], left_on='naics_code', 
                          right_on='naics_code', how='left')

df = adf.set_index("asin_code").join(edf.set_index("asin_code"), lsuffix='_human', rsuffix='_model')
rf = df[df.naics_code_human == df.naics_code_model]

print("Top-1 accuracy w.r.t NAICS codes: ", len(rf.index.unique())/len(df.index.unique()))
print("Correct predictions: {}, Total ASINs: {}".format(len(rf.index.unique()), len(df.index.unique())))

## Compute the top-1 accuracy with respect to BEA codes (top 4 digits of NAICS code)
df.bea_human = df.naics_code_human//100
df.bea_model = df.naics_code_model//100
bf = df[df.bea_human == df.bea_model]
print("Top-1 accuracy w.r.t BEA codes: ", len(bf.index.unique())/len(df.index.unique()))
print("Correct predictions: {}, Total ASINs: {}".format(len(bf.index.unique()), len(df.index.unique())))

# Compute the mean absolute percentage error and R^2 value w.r.t EIF for zero-shot prediction
df = df.dropna()
y_true = df.groupby(df.index).first().eio_co2_human
y_pred = df.groupby(df.index).first().eio_co2_model
print(mape(y_true, y_pred), r2_score(y_true, y_pred))
# %%
