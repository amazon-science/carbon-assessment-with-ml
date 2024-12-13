# Parakeet: Emission Factor Recommendation for Carbon Footprinting with Generative AI

This code repository presents a Generrative AI based method that levergaes Large Language Models to recommend an Environmental Impact Factor (EIF) for a given product, material, or activity, which is a fundamental step of carbon footprinting. The code documents the methods in the following research papers.


[Parakeet: Emission Factor Recommendation for Carbon Footprinting with Generative AI](https://www.amazon.science/publications/parakeet-emission-factor-recommendation-for-carbon-footprinting-with-generative-ai) \
Bharathan Balaji, Fahimeh Ebrahimi, Nina Domingo, Gargeya Vunnava, Abu-Zaher Faridee, Soma Ramalingam, Shikha Gupta, Anran Wang, Harsh Gupta, Domenic Belcastro, Kellen Axten, Jeremie Hakian, Aravind Srinivasan, Qingshi Tu, Jared Kramer

## Installation


Create+activate conda environment with Python 3.11.7.
```
conda create --name parakeetenv python=3.11.7
conda activate parakeetenv
```

Install the packages
```
pip install -r requirements.txt
```

For running the code, you must have an AWS account to call bedrock. 

Create a `User` in your AWS account with your own key `id` and `key` following these steps
```
AWS Console -> IAM -> Users -> Create user -> provide user name -> attach policies directly -> 
    AmazonSageMakerFullAccess
    AmazonS3FullAccess
    AmazonBedrockFullAccess
    -> Create user
AWS Console -> IAM -> Users -> [username] -> Access key 1/create access key -> Local code -> Set description (eifmap) -> copy the "Access Key" and "Secret Access Key"
```

Add these entries in `~/.aws/credentials` file.

```
[AWS_Account_Name]
aws_access_key_id=XXX
aws_secret_access_key=YYY

```
## Getting Started
Make sure you have these folders:
```
EifmapNext/data/raw/
EifmapNext/data/predictions/
```

Demo scripts are in the `scripts` folder. Be sure to modify the `OUTPUT_FILE` variable in order to avoid overwritting your results.
```
cd parakeet/scripts
./generate_ranked_preds_eio.sh # for EEIO
./generate_ranked_preds_pLCA.sh # for pLCA
```



