import numpy as np
import shap

def get_reasons(input_df, explainer):
    shap_values = explainer.shap_values(input_df)

    if isinstance(shap_values, list):
        values = shap_values[1][0]
    else:
        values = shap_values[0]

    importance = {}
    for i, f in enumerate(input_df.columns):
        val = values[i]
        if isinstance(val, (list, np.ndarray)):
            val = float(val[0]) if len(val) > 0 else 0.0
        importance[f] = float(val)

    sorted_features = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)
    return [{"feature": f, "impact": round(v, 4)} for f, v in sorted_features[:5]]