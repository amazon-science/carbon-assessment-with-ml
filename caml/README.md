## Task: Product carbon footprinting with EIO-LCA

Economic input-output life cycle assessment (EIO-LCA) is a method to estimate the cradle-to-gate carbon footprint of a product or activity based on its sale value. There are databases such as [USEEIO](https://www.epa.gov/land-research/us-environmentally-extended-input-output-useeio-technical-content) which publish the carbon emissions associated with industry sectors in the economy on a per unit currency basis. EIO-LCA estimates are compatible with [Greenhouse Gas Protocol](https://ghgprotocol.org/), and can be used for external reporting of scope 3 impacts. Given that the carbon emission estimate is only based on sale value of a product, it is an approximation and roughly within 2X the value of true emissions as per a [recent study](https://onlinelibrary.wiley.com/doi/pdf/10.1111/jiec.13271). 

We automate the process of mapping products to their EIO industry sectors based on text descriptions. This is one of the key steps in life cycle assessment that is done manually in practice. Our solution alleviates this manual overhead, and scales to any type of product. In a nutshell, we use a natural language model to match industry sectors based on semantic text similarity. The model is pre-trained on web data, and we use it as-is without additional training on products or industry sectors.

Figure below gives an overview of the text similarity model inference.

<img src="../../images/sbert_model.png"  width="800">
