all_metrics = ['Accuracy']

def get_metric(metric_name, **metric_config):
    # Accuracy
    if metric_name == 'acc':
       from metrics.Accuracy import Accuracy
       return Accuracy(**metric_config)
    # Pass@K
    elif metric_name == 'pass@k':
       from metrics.PassAtK import PassAtK
       return PassAtK(**metric_config)
    else:
        raise NotImplementedError(f"Metric {metric_name} not implemented")