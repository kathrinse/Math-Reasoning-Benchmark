all_models = ['GPTModel', 'LLaMAModel']

def get_model(model_name, **model_config):
    # GPT Model Series
    if model_name.startswith('gpt'):
       from model.GPT import GPTModel
       return GPTModel(model_name, **model_config)
    # LLaMA-3 Model Series
    elif model_name.startswith('llama-3'):
        from model.LLaMA3 import LLaMA3Model
        return LLaMA3Model(model_name, **model_config)
    else:
        raise NotImplementedError(f"Model {model_name} not implemented")
