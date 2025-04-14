## Carbon assessment with machine learning
This code repository presents a machine learning based method for selection of an Environmental Impact Factor (EIF) for a given product, material, or activity, which is a fundamental step of carbon footprinting. The code documents the methods in the following research papers.

1. EIF matching with generative AI, published in [CCAI@NeurIPS 2024](https://www.climatechange.ai/) -- \
   [Parakeet: Emission Factor Recommendation for Carbon Footprinting with Generative AI](https://www.amazon.science/publications/parakeet-emission-factor-recommendation-for-carbon-footprinting-with-generative-ai) \
Bharathan Balaji, Fahimeh Ebrahimi, Nina Domingo, Gargeya Vunnava, Abu-Zaher Faridee, Soma Ramalingam, Shikha Gupta, Anran Wang, Harsh Gupta, Domenic Belcastro, Kellen Axten, Jeremie Hakian, Aravind Srinivasan, Qingshi Tu, Jared Kramer

2. EIF matching for Process LCA, published in [ACM JCSS](https://dl.acm.org/journal/acmjcss) -- \
[Flamingo: Environmental Impact Factor Matching for Life Cycle Assessment with Zero-Shot Machine Learning](https://www.amazon.science/publications/flamingo-environmental-impact-factor-matching-for-life-cycle-assessment-with-zero-shot-machine-learning) 
Bharathan Balaji, Venkata Sai Gargeya Vunnava, Shikhar Gupta, Nina Domingo, Harsh Gupta, Geoffrey Guest, Aravind Srinivasan

3. EIF matching for EIO-LCA, published in [WWW 2023](https://www2023.thewebconf.org/calls/special-tracks/web4good/) -- \
[CaML: Carbon Footprinting of Household Products with Zero-Shot Semantic Text Similarity](https://www.amazon.science/publications/caml-carbon-footprinting-of-household-products-with-zero-shot-semantic-text-similarity) \
Bharathan Balaji, Venkata Sai Gargeya Vunnava, Geoffrey Guest, Jared Kramer

## Installation
Required packages are given in `requirements.txt`
Run the following commands to install the package:
```
git clone https://github.com/amazon-science/carbon-assessment-with-ml.git
cd carbon-assessment-with-ml
pip install -r requirements.txt
pip install -e .
```

## Getting Started
For EIO-LCA use: `caml/demo.ipynb`\
for process LCA use: `flamingo/process/generate_ranked_preds.ipynb` 

## Parakeet 
Create+activate conda environment with Python 3.11.7.
```
conda create --name parakeetenv python=3.11.7
conda activate parakeetenv
```
Install the packages
```
pip install -r parakeet/requirements.txt
```
For running the code, you must have an AWS account to call bedrock. 

Create a `User` in your AWS account with your own key `id` and `key` following these steps
```
AWS Console -> IAM -> Users -> Create user -> provide user name -> attach policies directly -> 
    AmazonSageMakerFullAccess
    AmazonS3FullAccess
    AmazonBedrockFullAccess
    -> Create user
AWS Console -> IAM -> Users -> [username] -> Access key 1/create access key -> Local code -> Set description (parakeet) -> copy the "Access Key" and "Secret Access Key"
```

Add these entries in `~/.aws/credentials` file.

```
[AWS_Account_Name]
aws_access_key_id=XXX
aws_secret_access_key=YYY

```
Demo scripts are in the `scripts` folder. Be sure to modify the `OUTPUT_FILE` variable in order to avoid overwritting your results.
```
cd parakeet/scripts
./generate_ranked_preds_eio.sh # for EEIO
./generate_ranked_preds_pLCA.sh # for pLCA
```

## Dataset
The dataset is for research purposes only, and is not indicative of Amazon’s business use for carbon footprinting.

The dataset consists of retail products mapped to North American Industry Classification System (NAICS) codes. The mapping was done with Amazon Mechanical Turk, aggregating ground truth from 5 annotations per product. The dataset is the basis of estimating the carbon emissions of a product using Economic Input-Output Life Cycle Assessment (EIO-LCA). Dataset is stored as a Pandas dataframe.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the terms of the Apache 2.0 license. See `LICENSE`.
Included datasets are licensed under the terms of the CDLA Permissive license, version 2.0. See `LICENSE-DATA`.

## Citation

Below is the BibTeX text, if you would like to cite our work.

```
@Inproceedings{Balaji2023CaML,
 author = {Bharathan Balaji and Geoffrey Guest and Venkata Sai Gargeya Vunnava and Jared Kramer},
 title = {CaML: Carbon footprinting of household products with zero-shot semantic text similarity},
 year = {2023},
 url = {https://www.amazon.science/publications/caml-carbon-footprinting-of-household-products-with-zero-shot-semantic-text-similarity},
 booktitle = {The Web Conference 2023},
}
```

```
@Inproceedings{Balaji2023Flamingo,
 author = {Bharathan Balaji and Venkata Sai Gargeya Vunnava and Shikhar Gupta and Nina Domingo and Harsh Gupta and Geoffrey Guest and Aravind Srinivasan},
 title = {Flamingo: Environmental Impact Factor Matching for Life Cycle Assessment with Zero-Shot Machine Learning},
 year = {2023},
 url = {https://www.amazon.science/publications/flamingo-environmental-impact-factor-matching-for-life-cycle-assessment-with-zero-shot-machine-learning}
 booktitle = {ACM Journal on Computing and Sustainable Societies},
}
```

```
@Inproceedings{Balaji2024,
 author = {Bharathan Balaji and Fahimeh Ebrahimi and Nina Domingo and Gargeya Vunnava and Abu-Zaher Faridee and Soma Ramalingam and Shikhar Gupta and Anran Wang and Harsh Gupta and Domenic Belcastro and Kellen Axten and Jeremie Hakian and Jared Kramer},
 title = {Parakeet: Emission factor recommendation for carbon footprinting with generative AI},
 year = {2024},
 url = {https://www.amazon.science/publications/parakeet-emission-factor-recommendation-for-carbon-footprinting-with-generative-ai},
 booktitle = {NeurIPS 2024 Workshop on Tackling Climate Change with Machine Learning},
}
```
