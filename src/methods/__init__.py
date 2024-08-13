
def get_method(method_name, **method_config):
    if method_name == 'ZeroShotCoT':
        from methods.in_context.ZeroShotCoT import ZeroShotCoT
        return ZeroShotCoT(**method_config)
    elif method_name == 'SelfConsistencyCoT':
        from methods.in_context.SelfConsistencyCoT import SelfConsistencyCoT
        return SelfConsistencyCoT(**method_config)
    elif method_name == 'CoT':
        from methods.in_context.CoT import CoT
        return CoT(**method_config)
    elif method_name == 'AutoCoT':
        from methods.in_context.AutoCoT import AutoCoT
        return AutoCoT.AutoCoT(**method_config)
    elif method_name == 'ComplexCoT':
        from methods.in_context.ComplexCoT import ComplexCoT
        return ComplexCoT.ComplexCoT(**method_config)
    elif method_name == 'PoT':
        from methods.in_context.PoT import PoT
        return PoT.PoT(**method_config)
    elif method_name == 'PAL':
        from methods.in_context.PAL import PAL
        return PAL(**method_config)
    else:
        raise NotImplementedError(f"Method {method_name} not implemented")
