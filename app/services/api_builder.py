def build_url(group, params):
    base = f"/device.cgi/{group}?"

    query = "&".join([f"{k}={v}" for k, v in params.items()])

    return base + query