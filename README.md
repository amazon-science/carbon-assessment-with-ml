## Carbon assessment with machine learning
This code repository presents a machine learning based method for selection of an Environmental Impact Factor (EIF) for a given product, material, or activity, which is a fundamental step of carbon footprinting. The code documents the methods in the following research papers.

1. EIF matching for EIO-LCA, published in [WWW 2023](https://www2023.thewebconf.org/calls/special-tracks/web4good/) -- \
[CaML: Carbon Footprinting of Household Products with Zero-Shot Semantic Text Similarity](https://www.amazon.science/publications/caml-carbon-footprinting-of-household-products-with-zero-shot-semantic-text-similarity) \
Bharathan Balaji, Venkata Sai Gargeya Vunnava, Geoffrey Guest, Jared Kramer

2. EIF matching for Process LCA, published in [ACM JCSS](https://dl.acm.org/journal/acmjcss) -- \
[Flamingo: Environmental Impact Factor Matching for Life Cycle Assessment with Zero-Shot Machine Learning](https://www.amazon.science/publications/flamingo-environmental-impact-factor-matching-for-life-cycle-assessment-with-zero-shot-machine-learning) \ 
Bharathan Balaji, Venkata Sai Gargeya Vunnava, Shikhar Gupta, Nina Domingo, Harsh Gupta, Geoffrey Guest, Aravind Srinivasan

## Installation
Required packages are given `requirements.txt`
Run the following commands to install the package:
```
git clone https://github.com/amazon-science/carbon-assessment-with-ml.git
cd carbon-assessment-with-ml
pip install -r requirements.txt
pip install -e .
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