lca_assistant_prompt = """
The following is a conversation between a life cycle assessment (LCA) expert and an LCA AI assistant.

Current conversation:
{history}

Human:
{input}

Assistant:
"""

system_lca_assistant_prompt = """
The following is a conversation between a life cycle assessment (LCA) expert and an LCA AI assistant.
"""

text_clean_prompt = """In order to do Life Cycle Assessment, given an item description, I want you to paraphrase it in a plain language. Just provide the output and nothing else.

### Additional Instructions ###
- If the given description is already generic/common, no need to paraphrase. Example. {{"Ingredient": "mild chili pepper"}} -> mild chili pepper.
- Do not remove the specifics (e.g. "date sugar' should NOT be paraphrased as just "sugar").
- Make the most of the given information. DO NOT say that information is limited. DO NOT refrain from providing a description, or ask for more information. DO NOT say you have insufficient information for an LCA.
- If you cannot provide a plain language description, simply summarize the information provided. You MUST provide a description. 
- Avoid filler words such as "Based on the details" or "happy to assist", 
- keep your response to the point.
- Do not repeat the given instructions or information. 


### Example Input for an LCA for IT industry ###
itemname                 PRT.CLR.MFP.LRG - HP Color LaserJet Ent MFP M5...
itemdescription                                            PRT.CLR.MFP.LRG
itemcommodityname                                                 Printers
unique_identifiername                                  UIN - OPERATIONS IT

### Example Output ###
a color laserjet printer used for operations in an IT environment

### Input ###
{}
"""

text_clean_prompt_eio = """I want to do of LCA of business activities based on Environmentally Extended Input Output (EEIO) 
Environmental Impact Factors (EIF). I'm interested in the environmental impact associated with the materials 
and manufacturing phase of the activity. I am given business activity descriptions, and I want to 
paraphrase it to a plain language description before I select an EIF. 

Below is an example of a given activity and it's plain language description. Note that the description 
is brief, and does not make any assumptions about the activity.

itemname                 PRT.CLR.MFP.LRG - HP Color LaserJet Ent MFP M5...
itemdescription                                            PRT.CLR.MFP.LRG
itemcommodityname                                                 Printers
unique_identifiername                                  UIN - OPERATIONS IT

The item is a color laserjet printer used for operations in an IT environment.

Following the example, provide a plain language description of the activity data given below:
{}

Make the most of the given information. DO NOT say that information is limited.
DO NOT refrain from providing a description, or ask for more information.
If you cannot provide a plain language description, simply summarize the 
information provided. You MUST provide a description. 

Avoid filler words such as "Based on the details" or "happy to assist", 
keep your response to the point.
Do not repeat the given instructions or information. 
DO NOT say you have insufficient information for an LCA.

Only provide the description and nothing else."""

eio_reranker_prompt = """
### Instructions ###
You want to perform economic input-output life-cycle assessment, or EIO-LCA.
You have description of an activity and a few relevant North American Industry Classification System (NAICS) titles, their descriptions and codes.
Reorder these NAICS titles and codes from the most likely relevance to the least likely relevance. Only report the top 5 unique titles and associated codes.
The criteria for relevance is the environmental impact associated with the materials and manufacturing phase of the activity.

Be sure to properly escape any special characters in the 'justification' field so that your response can be parsed with a python code interpreter.
Return a Python list of dictionaries where each dictionary contains the keys 'naics_code', 'justification', and 'naics_title'. The format of each dictionary must match the following example: [{{'naics_code': , 'justification': '', 'naics_title': ''}},{{'naics_code': , 'justification': '', 'naics_title': ''}}]. Do not include any additional text or explanation in your response.

### Example Input ###
Activity description: 'IT hardware and software for enterprise operations'
NAICS titles, descriptions and codes:
[
{{"naics_title": "Computer Facilities Management Services","naics description": "Computer systems facilities (i.e., clients' facilities) management and operation services","naics_code": "541513"}},
{{"naics_title": "Electronic Computer Manufacturing","naics description": "Workstations, computer, manufacturing","naics_code": "334111"}},
{{"naics_title": "Computer Facilities Management Services","naics description": "Data processing facilities (i.e., clients' facilities) management and operation services","naics_code": "541513"}},
{{"naics_title": "All Other Support Services","naics description": "Inventory computing services","naics_code": "561990"}},
{{"naics_title": "Facilities Support Services","naics description": "Facilities (except computer operation) support services","naics_code": "561210"}},
{{"naics_title": "Computer Storage Device Manufacturing","naics description": "Storage devices, computer, manufacturing","naics_code": "334112"}},
{{"naics_title": "Electronic Computer Manufacturing","naics description": "Computers manufacturing","naics_code": "334111"}},
{{"naics_title": "Computer Terminal and Other Computer Peripheral Equipment Manufacturing","naics description": "Computer input/output equipment manufacturing","naics_code": "334118"}},
{{"naics_title": "Electronic Computer Manufacturing","naics description": "Computer servers manufacturing","naics_code": "334111"}}
]

### Example Output ###
[
{{'naics_code': 541513,
'justification': 'This NAICS title covers the management and operation of computer systems facilities and data processing facilities for clients, which aligns with providing IT hardware and software for enterprise operations.',
'naics_title': 'Computer Facilities Management Services'}},
{{'naics_code': 334111,
'justification': 'This covers manufacturing of computers, servers, and workstations, which are relevant hardware components for enterprise IT operations.',
'naics_title': 'Electronic Computer Manufacturing'}}
]

### Input ###
Activity description: {}
NAICS titles, descriptions and codes: {}
"""


reference_prods_prompt = """
### Instructions ###
You are a Life Cycle Assessment expert and is performing a process-based Life Cycle Assessment (LCA).
I will give you an 'item description' and a list of 'reference_product's. 
Find a maximum of 5 highest matched 'reference_product's from the given list and report them in the order of match (highest match first) in a Python list of dictionaries.
For each entry in the dictionary, you must provide the 'justification' field, 'reference_product' and the 'index' of the 'reference_product'.

### Detailed Instructions ###
- Definition of match: Given an item description, a reference product is considered a match if it is either an exact match of the reference product (e.g. 'tomato' in an exact match for item "red tomato") or one of the components of the item description (e.g. given 'chili bean sauce' as the item, and 'bean' and 'chilli' as reference products, both are considered matches). Note that this definition is optimized for recall (i.e. to capture as many reference products as possible in the top 5 list).
- Write the 'justification' field following this chain of thoughts: (a) break down the "Item description" into its components if it has multiple components (b) go through each reference product in the list and see if any of them are either an exact match of the item or one of its components.
- Similar reference products are not considered as a match. Example: For the item description 'rapini', the reference product 'spinach' is not a match; they are similar vegetables but not the same.
- ALL 'index' and 'reference_product's that you return as an output MUST be in the reference_product's input data. DO NOT generate or hallucinate an 'index' or a 'reference_product' that is not in the input.
- If any of the reference product is not a match, do not report that entry. It is better to report fewer entries than to report unmatched entries, but report at least 1 entry if possible.
- If none of reference products is a match, return one entry with 'reference_product': '', 'index': ''. DO NOT return this entry once there is at least one match.
- If the given list contains duplicate reference products, only report the first occurrence of the reference product.
- Always give a higher ranking to reference products that cover the most volume (thereby contributes to more CO2 emission) of the item. e.g. given 'chili bean sauce' as the item, and 'bean' and 'chilli' as reference products, you have to rank 'bean' higher than 'chilli' as 'chili bean sauce' is made from beans.
- Return a python list of dictionaries, each dictionary should contain the fields 'index', 'justification' and 'reference_product'. Output nothing else before and after this list of dictionary.
- The format of response must match the following example: [{{'justification': '', 'reference_product': '', 'index':}},{{'justification': '', 'reference_product': '', 'index':}}]. Do not include any additional text or explanation in your response. DO NOT break this rule.
- Be sure to properly escape any special characters in the 'justification' field so that your response can be parsed with a python code interpreter.
- DO NOT return sentences like 'Here are the top 5 highest matched reference products for the item'. Just return the python list of dictionary and nothing else. 
- Return a Python List of dictionaries and nothing else.
- Your response will be parsed using ast.literal_eval(response) command, so you MUST return a Python list of dictionaries to avoid errors.

### Example Input ###
item description: "Ingredient    popped popcorn"
Reference products:
 [
 {{'index': 0, 'reference_product': 'sweet corn'}},
 {{'index': 1, 'reference_product': 'chopping, maize'}},
 {{'index': 2, 'reference_product': 'maize chop'}},
 {{'index': 3, 'reference_product': 'palm kernel meal'}},
 {{'index': 4, 'reference_product': 'maize grain, organic'}},
 {{'index': 5, 'reference_product': 'lime, packed'}},
 {{'index': 6, 'reference_product': 'flax husks'}},
 {{'index': 7, 'reference_product': 'maize grain'}},
 {{'index': 8, 'reference_product': 'wood chips and particles, willow'}},
 {{'index': 9, 'reference_product': 'maize grain, feed'}},
 {{'index': 10, 'reference_product': 'lime, hydrated, packed'}},
 {{'index': 11, 'reference_product': 'maize seed, at farm'}},
 {{'index': 12, 'reference_product': 'tomato, fresh grade'}},
 {{'index': 13, 'reference_product': 'quicklime, milled, packed'}},
 {{'index': 14, 'reference_product': 'bottom ash, MSWI[F]-WWT, WW from maize starch production'}},
 {{'index': 15, 'reference_product': 'maize grain, feed, organic'}},
 {{'index': 16, 'reference_product': 'frozen fish sticks, hake'}},
 {{'index': 17, 'reference_product': 'sweet sorghum grain'}},
 {{'index': 18, 'reference_product': 'operation, reefer, freezing'}},
 {{'index': 19, 'reference_product': 'orange, fresh grade'}}
 ]
 
### Example Output ###
[
{{"justification": 'Popcorn is made from maize/corn kernels, so "maize grain" is the most relevant reference product.',"reference_product": "maize grain","index": 7}},
{{"justification": '"Maize grain, organic" is also highly relevant as popcorn is made from maize/corn.',"reference_product": "maize grain, organic","index": 4}},
{{"justification": '"Maize grain, feed" is relevant as it refers to maize/corn which is used to make popcorn.',"reference_product": "maize grain, feed","index": 9}},
{{"justification": '"Maize seed, at farm" is relevant as it refers to the source of maize/corn used for popcorn.',"reference_product": "maize seed, at farm","index": 11}},
{{"justification": '"Maize grain, feed, organic" is somewhat relevant as it refers to organic maize/corn which could be used for popcorn.',"reference_product": "maize grain, feed, organic","index": 15}},
]


### Input ###
Information on item: {}
Reference products: {}
"""


best_eif_prompt = """
### Instructions ###
You are a Life Cycle Assessment expert and is performing a process-based Life Cycle Assessment (LCA).
I have (a) an 'item description' and (b) the name ('impact_factor_name') and associated information ('reference_product', 'process_technology', 'process_description') of a few candidate impact factors.
Report the first and the second (in that order of match) 'impact_factor_name' that 'exactly matches' with the given 'item description'.
Note that this task is optimized for precision (i.e. to find the exact match).
In each entry report 'justification', 'impact_factor_name', 'index' (in this order). This 'index' value should refer to the index from the provided impact factor list.

### Detailed Instructions ###
- Definition of exact match:
    - An 'exact match' happens when (a) the item description is directly covered by a single impact factor (e.g. 'market for grape' covers 'black grape' comprehensively), or (b) each components of the given item is covered by a single the impact factor under consideration.
    - Similar impact factors are not considered as exact match. Example: For the item description 'rapini', if you are given 'market for spinach' as a relevant impact factor (since spinach is a similar vegetable), you have to return None for 'index' and 'impact_factor_name' as 'emission associated with spinach cannot be used to estimate the emissions associated with rapini' (justification).
    - Once you breakdown an item with multiple components or ingredients, the exact match MUST cover ALL components and processes happened on the item. If there is no impact factor that covers processes happend on the main component, you MUST return None.  
    - Examples of cases that item description has multiple components: 
        - For item description 'frozen artichoke', 'market for artichoke' is NOT an exact match becuase it does not cover the process of freezing. 
        - Another example of item description is 'ground lamb' which includes the process of grounding, so do not choose 'market for sheep for slaughtering, live weight'.
        - For item description 'popcorn', an exact impact factor MUST include the process of popping and the corn, so the 'market for maize grain, organic' is not a exact match, so you MUST return None.
- Write the 'justification' field following this chain of thoughts:
    - break down the "Item description" into its components if it has multiple components. e.g. if given 'chocolate milk', write 'chocolate milk consists of multiple components such as chocolate and milk'. Then go step by step through each impact factor from the given list and see if any of them comprehensively cover all the emissions associated with all the components of the item description.
    - if there is no exact match, return None for 'index' and 'impact_factor_name'. Example: given 'chocolate milk' as item description and (i) 'market for milk', (ii) 'milk production' (iii) chocolate production as three candidate impact factors, you have to return None for for both 'index' and 'impact_factor_name' as none of the impact factors provided capture the full emissions associated with all two ingredients. They only capture one of the main ingredients like milk or chocolate.
    - If there is an exact match, report the 'index' and 'impact_factor_name' for that impact factor. Example, given 'chocolate milk' as item description and (i) 'market for milk', (ii) 'market for chocolate milk' (iii) 'market for chocolate' as three candidate impact factors, you have to return 'market for chocolate milk' and it's 'index' as it exactly matches with the item description.
- Whenever there is an impact factor starting with 'market for' and other impact factors that has 'production' in their name like 'X production' or 'production of X', ALWAYS SELECT the impact factor starting with 'market for' as the best match. This rule is to be followed strictly, without any exceptions or considerations for additional details or qualifiers in either impact factors. 
- Examples:
    - Given 'table grape' and both 'market for grape' and 'grape production', 'market for grape' MUST be chosen as the best match, and 'grape production' as the second-best match.
    - Given 'tomato, fresh grade' and both 'market for tomato, fresh grade' and 'tomato production, fresh grade, open field-tomato, fresh grade', 'market for tomato, fresh grade' MUST be chosen as the best match, and 'tomato production, fresh grade, open field-tomato, fresh grade' as the second-best match, regardless of additional details in the 'production' impact factor.
    - Given 'polypropylene, granulate' and both 'market for polypropylene, granulate' and 'polypropylene production, granulate-polypropylene, granulate', 'market for polypropylene, granulate' MUST be chosen as the best match, and 'polypropylene production, granulate-polypropylene, granulate' as the second-best match.
- You should NEVER, under any circumstances, select an impact factor that has 'production' in the name as the best match when there is an impact factor starting with 'market for' available as an option.
- If there are duplicate impact factors (exact same name), only report the first occurrence of the impact factor.
- If there are two similar impact factors and one of them has 'organic' in the name, you must return the impact factor that does not contain 'organic', unless the item description clearly indicates the item is organic.
- Return a Python list of dictionaries where each dictionary contains the keys 'index', 'impact_factor_name', and 'justification'. The format of each dictionary must match the following example: [{{'justification': '', 'index': , 'impact_factor_name': ''}},{{'justification': '', 'index': , 'impact_factor_name': ''}}]. Do not include any additional text or explanation in your response.
- Be sure to properly escape any special characters in the 'justification' field so that your response can be parsed with a python code interpreter.
- All 'index' and 'impact_factor_name' that you return MUST be from the input or can be None. DO not generate or hallucinate 'index' that is not in the input list. 

### Example Input ###
item description: "hot salsa"
Impact factor list:
{{
  0: {{'impact_factor_name': 'tomato production, fresh grade, open field-tomato, fresh grade',
  'reference_product': 'tomato, fresh grade',
  'process_technology': 'Cultivation of Tomato follows conventional production standards',
  'process_description': ' This dataset represents the production of 1 kg of fresh Tomato fresh grade during December, 2015- June, 2016 at a farm located in Village- Bhagatpur Ratan, District- Moradabad of UP. In this area, fields are irrigated with ground water using electric pump for surface irrigation. The farm has a yield of 60,000 kg fresh matter per ha for this crop cycle. Sowing date for the crop is 10-Feburary, 2016 and harvesting date is 12-June, 2016. Mineral NP fertilizer input is 113.25-69 kg/ha. Herbicide used has active ingredient as Carbofuran 495g/ha, Cypermethrin 156.25g/ha Machinery is used only for soil cultivation with fuel consumption of 12.48 kg/ha using plough and rotary cultivator for soil tillage.    This dataset is meant to replace the following datasets:  - tomato production, fresh grade, IN-UP, 2015 - 2018 (877f8df3-fbfc-408f-beee-46664f92cdbb)'}},
 1: {{'impact_factor_name': 'market for coriander',
  'reference_product': 'coriander',
  'process_technology': nan,
  'process_description': ' This is a market activity. Each market represents the consumption mix of a product in a given geography, connecting suppliers with consumers of the same product in the same geographical area. Markets group the producers and also the imports of the product (if relevant) within the same geographical area. They also account for transport to the consumer and for the losses during that process, when relevant. This is the market for  coriander, in the Global geography. Transport from producers to consumers of this product in the geography covered by the market is included. The product coriander is a spice/aromatic crop. It is a perennial crop.'}},
}}

### Example Response ###
[
{{ 'justification': 'Hot salsa contains multiple ingredients such as tomato, chilli, corn, and none of the provided impact factors capture the emissions associated with all the typical ingredients. They only capture one of the main ingredients like tomato.', 'index': None, 'impact_factor_name': None}},
{{ 'justification': 'Hot salsa contains multiple ingredients such as tomato, chilli, corn, and none of the provided impact factors capture the emissions associated with all the typical ingredients. They only capture one of the main ingredients like tomato.', 'index': None, 'impact_factor_name': None}}
]

Input For you
=============
Item description: {}
Impact factor list:
{}
"""
# Use this for unlicensed Ecoinvent databse. The results differs from what we report in the paper as we used the licensed database.
best_eif_in_unlicensed_ecoinvent_prompt = """
### Instructions ###
You are a Life Cycle Assessment expert and is performing a process-based Life Cycle Assessment (LCA).
I have (a) an 'item description' and (b) the name ('impact_factor_name') and associated information ('reference_product','product_info') of a few candidate impact factors.
Report the first and the second (in that order of match) 'impact_factor_name' that 'exactly matches' with the given 'item description'.
Note that this task is optimized for precision (i.e. to find the exact match).
In each entry report 'justification', 'impact_factor_name', 'index' (in this order). This 'index' value should refer to the index from the provided impact factor list.

### Detailed Instructions ###
- Definition of exact match:
    - An 'exact match' happens when (a) the item description is directly covered by a single impact factor (e.g. 'market for grape' covers 'black grape' comprehensively), or (b) each components of the given item is covered by a single the impact factor under consideration.
    - Similar impact factors are not considered as exact match. Example: For the item description 'rapini', if you are given 'market for spinach' as a relevant impact factor (since spinach is a similar vegetable), you have to return None for 'index' and 'impact_factor_name' as 'emission associated with spinach cannot be used to estimate the emissions associated with rapini' (justification).
    - Once you breakdown an item with multiple components or ingredients, the exact match MUST cover ALL components and processes happened on the item. If there is no impact factor that covers processes happend on the main component, you MUST return None.  
    - Examples of cases that item description has multiple components: 
        - For item description 'frozen artichoke', 'market for artichoke' is NOT an exact match becuase it does not cover the process of freezing. 
        - Another example of item description is 'ground lamb' which includes the process of grounding, so do not choose 'market for sheep for slaughtering, live weight'.
        - For item description 'popcorn', an exact impact factor MUST include the process of popping and the corn, so the 'market for maize grain, organic' is not a exact match, so you MUST return None.
- Write the 'justification' field following this chain of thoughts:
    - break down the "Item description" into its components if it has multiple components. e.g. if given 'chocolate milk', write 'chocolate milk consists of multiple components such as chocolate and milk'. Then go step by step through each impact factor from the given list and see if any of them comprehensively cover all the emissions associated with all the components of the item description.
    - if there is no exact match, return None for 'index' and 'impact_factor_name'. Example: given 'chocolate milk' as item description and (i) 'market for milk', (ii) 'milk production' (iii) chocolate production as three candidate impact factors, you have to return None for for both 'index' and 'impact_factor_name' as none of the impact factors provided capture the full emissions associated with all two ingredients. They only capture one of the main ingredients like milk or chocolate.
    - If there is an exact match, report the 'index' and 'impact_factor_name' for that impact factor. Example, given 'chocolate milk' as item description and (i) 'market for milk', (ii) 'market for chocolate milk' (iii) 'market for chocolate' as three candidate impact factors, you have to return 'market for chocolate milk' and it's 'index' as it exactly matches with the item description.
- Whenever there is an impact factor starting with 'market for' and other impact factors that has 'production' in their name like 'X production' or 'production of X', ALWAYS SELECT the impact factor starting with 'market for' as the best match. This rule is to be followed strictly, without any exceptions or considerations for additional details or qualifiers in either impact factors. 
- Examples:
    - Given 'table grape' and both 'market for grape' and 'grape production', 'market for grape' MUST be chosen as the best match, and 'grape production' as the second-best match.
    - Given 'tomato, fresh grade' and both 'market for tomato, fresh grade' and 'tomato production, fresh grade, open field-tomato, fresh grade', 'market for tomato, fresh grade' MUST be chosen as the best match, and 'tomato production, fresh grade, open field-tomato, fresh grade' as the second-best match, regardless of additional details in the 'production' impact factor.
    - Given 'polypropylene, granulate' and both 'market for polypropylene, granulate' and 'polypropylene production, granulate-polypropylene, granulate', 'market for polypropylene, granulate' MUST be chosen as the best match, and 'polypropylene production, granulate-polypropylene, granulate' as the second-best match.
- You should NEVER, under any circumstances, select an impact factor that has 'production' in the name as the best match when there is an impact factor starting with 'market for' available as an option.
- If there are duplicate impact factors (exact same name), only report the first occurrence of the impact factor.
- If there are two similar impact factors and one of them has 'organic' in the name, you must return the impact factor that does not contain 'organic', unless the item description clearly indicates the item is organic.
- Return a Python list of dictionaries where each dictionary contains the keys 'index', 'impact_factor_name', and 'justification'. The format of each dictionary must match the following example: [{{'justification': '', 'index': , 'impact_factor_name': ''}},{{'justification': '', 'index': , 'impact_factor_name': ''}}]. Do not include any additional text or explanation in your response.
- Be sure to properly escape any special characters in the 'justification' field so that your response can be parsed with a python code interpreter.
- All 'index' and 'impact_factor_name' that you return MUST be from the input or can be None. DO not generate or hallucinate 'index' that is not in the input list. 

### Example Input ###
item description: "hot salsa"
Impact factor list:
{{
  0: {{'impact_factor_name': 'tomato production, fresh grade, open field',
  'reference_product': 'tomato, fresh grade',
  'product_info': 'The product 'tomato, fresh grade' is a fruit. It is an annual crop. Fresh grade represents a product that is meant for human consumption directly.',
  }},
 1: {{'impact_factor_name': 'market for coriander',
  'reference_product': 'coriander',
  'product_info': 'The product 'coriander' is a herb. It is an annual crop.',
  }}

### Example Response ###
[
{{ 'justification': 'Hot salsa contains multiple ingredients such as tomato, chilli, corn, and none of the provided impact factors capture the emissions associated with all the typical ingredients. They only capture one of the main ingredients like tomato.', 'index': None, 'impact_factor_name': None}},
{{ 'justification': 'Hot salsa contains multiple ingredients such as tomato, chilli, corn, and none of the provided impact factors capture the emissions associated with all the typical ingredients. They only capture one of the main ingredients like tomato.', 'index': None, 'impact_factor_name': None}}
]

Input For you
=============
Item description: {}
Impact factor list:
{}
"""



eio_groundtruth_json = {
    "source": "Account number: 16100 \n \
    Account name: Buildings \n \
    Account description: Building capex, may consist of super structure \n",
    "sourceType": "text",
    "formTitle": "Match input activity to economic sector",
    "taskDescription": "Activity to EIO EIF Mapping",
    "formConfigMode": "inline",
    "formConfig": {
        "fields": [
            {
                "id": "eif_choice",
                "label": """Which of the following economic categories best describes the activity?""",
                "fieldType": "radio",
                "options": [
                    {"label": "Cabbage farming", "value": "111219"},
                    {
                        "label": "Nuts, chocolate covered, made from purchased cacao beans",
                        "value": "311330",
                    },
                    {
                        "label": "Nuts, covered (except chocolate covered), manufacturing",
                        "value": "311340",
                    },
                    {"label": "Almond pastes manufacturing", "value": "311999"},
                    {
                        "label": "Peanut cake, meal, and oil made in crushing mills",
                        "value": "311223",
                    },
                    {"label": "Not sure", "value": "-1"},
                    {"label": "No good match", "value": "0"},
                ],
                "isRequired": True,
            },
            {
                "id": "justification",
                "label": "If you made a different choice than the top recommendation given by the AI, \
or if you want to edit the AI justification, provide your justification below.",
                "fieldType": "text",
                "isRequired": False,
            },
            {
                "id": "comment",
                "label": "Optional comments or notes",
                "fieldType": "text",
                "isRequired": False,
            },
        ]
    },
}

process_groundtruth_json = {
    "source": "Account number: 16100 \n \
    Account name: Buildings \n \
    Account description: Building capex, may consist of super structure \n",
    "sourceType": "text",
    "formTitle": "Match input activity to process",
    "taskDescription": "Activity to Process EIF Mapping",
    "formConfigMode": "inline",
    "formConfig": {
        "fields": [
            {
                "id": "eif_choice",
                "label": """Which of the following process best describes the activity?""",
                "fieldType": "radio",
                "options": [
                    {"label": "Cabbage farming", "value": "111219"},
                    {
                        "label": "Nuts, chocolate covered, made from purchased cacao beans",
                        "value": "311330",
                    },
                    {
                        "label": "Nuts, covered (except chocolate covered), manufacturing",
                        "value": "311340",
                    },
                    {"label": "Almond pastes manufacturing", "value": "311999"},
                    {
                        "label": "Peanut cake, meal, and oil made in crushing mills",
                        "value": "311223",
                    },
                    {"label": "Not sure", "value": "-1"},
                    {"label": "No good match", "value": "0"},
                ],
                "isRequired": True,
            },
            {
                "id": "justification",
                "label": "If you made a different choice than the top recommendation given by the AI, \
or if you want to edit the AI justification, provide your justification below.",
                "fieldType": "text",
                "isRequired": False,
            },
            {
                "id": "comment",
                "label": "Optional comments or notes",
                "fieldType": "text",
                "isRequired": False,
            },
        ]
    },
}


