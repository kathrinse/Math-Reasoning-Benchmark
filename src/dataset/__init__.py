all_datasets = ['GSM8K', 'MATH', 'AQUA', 'SVAMP', 'MultiArith']

def get_dataset(dataset_name, **dataset_config):
    # GSM8K
    if dataset_name == 'gsm8k':
       from dataset.GSM8K import GSM8K
       return GSM8K
    # MATH
    elif dataset_name == 'math':
        from dataset.MATH import MATH
        return MATH
    # SVAMP
    elif dataset_name == 'svamp':
        from dataset.SVAMP import SVAMP
        return SVAMP
    # AQUA
    elif dataset_name == 'aqua':
        from dataset.AQUA import AQUA
        return AQUA
    # MULTI-ARITH
    elif dataset_name == 'multiarith':
        from dataset.MultiArith import MultiArith
        return MultiArith
    else:
        raise NotImplementedError(f"Dataset {dataset_name} not implemented")